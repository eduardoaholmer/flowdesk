import io
import uuid

from fastapi import APIRouter, Depends, UploadFile, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from src.core.authorization import require_permission
from src.core.dependencies import get_current_user
from src.core.permissions import Permission
from src.core.schemas import DataEnvelope
from src.core.security import CurrentUser
from src.core.storage import StorageProvider, get_storage_provider
from src.features.attachments.dependencies import get_attachment_service
from src.features.attachments.schemas import AttachmentResponse
from src.features.attachments.service import AttachmentService
from src.features.workspaces.models import WorkspaceMember

# Mesmo padrão de `comments/router.py`: um router, dois formatos de path —
# upload aninhado sob a Issue-mãe (`.../issues/{issue_id}/attachments`),
# download/exclusão pelo próprio `attachment_id` (`.../attachments/{id}`).
router = APIRouter(prefix="/workspaces/{workspace_id}", tags=["attachments"])


@router.post(
    "/issues/{issue_id}/attachments",
    status_code=status.HTTP_201_CREATED,
    response_model=DataEnvelope[AttachmentResponse],
)
async def upload_issue_attachment(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    file: UploadFile,
    current_user: CurrentUser = Depends(get_current_user),
    _member: WorkspaceMember = Depends(require_permission(Permission.ATTACHMENT_CREATE)),
    service: AttachmentService = Depends(get_attachment_service),
) -> DataEnvelope[AttachmentResponse]:
    """Lê o corpo inteiro do upload em memória (`UploadFile.read()`) antes de
    validar/persistir: para o teto de tamanho desta sprint (`Settings.max_upload_size_bytes`,
    10 MB por padrão) isso é aceitável e mantém `AttachmentService` agnóstico
    de HTTP (recebe `BinaryIO`/`bytes`, nunca o `UploadFile` do Starlette —
    CLAUDE.md §5). Um volume de upload maior no futuro trocaria isso por
    streaming direto ao `StorageProvider` sem mudar o contrato do service.
    """
    content = await file.read()
    attachment = await service.upload_to_issue(
        current_user,
        workspace_id,
        issue_id,
        file_name=file.filename or "arquivo",
        content_type=file.content_type or "application/octet-stream",
        size=len(content),
        stream=io.BytesIO(content),
    )
    return DataEnvelope(data=AttachmentResponse.model_validate(attachment))


@router.get("/issues/{issue_id}/attachments", response_model=DataEnvelope[list[AttachmentResponse]])
async def list_issue_attachments(
    workspace_id: uuid.UUID,
    issue_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> DataEnvelope[list[AttachmentResponse]]:
    attachments = await service.list_for_issue(workspace_id, issue_id)
    return DataEnvelope(data=[AttachmentResponse.model_validate(a) for a in attachments])


@router.get("/attachments/{attachment_id}")
async def download_attachment(
    workspace_id: uuid.UUID,
    attachment_id: uuid.UUID,
    _member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: AttachmentService = Depends(get_attachment_service),
    storage: StorageProvider = Depends(get_storage_provider),
) -> FileResponse:
    """`storage.open()` devolve um `Path` local em qualquer provider — para
    `S3StorageProvider` isso é um download para um arquivo temporário (ver
    `core/storage.py`), não o arquivo de origem; por isso o `BackgroundTask`
    de limpeza só roda quando `provider_name != "local"` (apagar
    incondicionalmente apagaria o próprio anexo armazenado em disco).
    """
    attachment = await service.get(workspace_id, attachment_id)
    path = await storage.open(attachment.storage_key)
    cleanup = (
        BackgroundTask(path.unlink, missing_ok=True)
        if storage.provider_name != "local"
        else None
    )
    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.file_name,
        background=cleanup,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    workspace_id: uuid.UUID,
    attachment_id: uuid.UUID,
    acting_member: WorkspaceMember = Depends(require_permission(Permission.ISSUE_READ)),
    service: AttachmentService = Depends(get_attachment_service),
) -> None:
    await service.delete(acting_member, workspace_id, attachment_id)
