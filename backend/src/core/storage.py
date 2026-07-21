import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

import boto3
from fastapi import Depends

from src.core.config import Settings, get_settings


class StorageProvider(Protocol):
    """Ponto de extensão para o backend de blob storage (`CLAUDE.md`, "Anexos" —
    "permitir futura migração para S3 ou serviço equivalente"). `Attachment.storage_key`
    é sempre um ponteiro opaco relativo a este provider, nunca um path absoluto de
    disco vazado para fora desta camada; `Attachment.storage_provider` registra qual
    implementação gravou o arquivo, permitindo que dados antigos ("local") e novos
    (ex.: "s3") coexistam na mesma tabela se o provider for trocado no futuro sem
    migração de dado retroativa.
    """

    provider_name: str

    async def save(self, *, stream: BinaryIO, suggested_name: str) -> str: ...
    async def open(self, storage_key: str) -> Path: ...
    async def delete(self, storage_key: str) -> None: ...


class LocalStorageProvider:
    """Armazenamento em disco local (Sprint 8) — suficiente para um deploy de
    portfólio single-instance; `storage_key` é um path relativo a `upload_dir`
    (nunca o nome original do arquivo, para não colidir/vazar estrutura de
    diretório do cliente), prefixado por um UUIDv7 para evitar colisão sem
    depender de lock de arquivo.
    """

    provider_name = "local"

    def __init__(self, upload_dir: Path) -> None:
        self._upload_dir = upload_dir

    def _resolve(self, storage_key: str) -> Path:
        return self._upload_dir / storage_key

    async def save(self, *, stream: BinaryIO, suggested_name: str) -> str:
        storage_key = f"{uuid.uuid4().hex}-{suggested_name}"
        destination = self._resolve(storage_key)

        def _write() -> None:
            self._upload_dir.mkdir(parents=True, exist_ok=True)
            with destination.open("wb") as out:
                out.write(stream.read())

        await asyncio.to_thread(_write)
        return storage_key

    async def open(self, storage_key: str) -> Path:
        return self._resolve(storage_key)

    async def delete(self, storage_key: str) -> None:
        await asyncio.to_thread(self._resolve(storage_key).unlink, True)


class S3StorageProvider:
    """Armazenamento em um bucket S3-compatible (Sprint 17.2/M6, ADR-038) —
    `boto3` (síncrono) envolvido em `asyncio.to_thread`, mesmo padrão já usado
    por `LocalStorageProvider` para não bloquear o event loop com I/O; um
    cliente S3 é thread-safe para chamadas sequenciais como as daqui, então é
    criado uma vez no `__init__`, não a cada chamada.

    `endpoint_url` não-`None` aponta para um S3-compatible que não é AWS (MinIO,
    R2, Spaces); `None` deixa o boto3 resolver o endpoint padrão da AWS a partir
    de `region_name`. Credenciais nunca passam por aqui — vêm da cadeia padrão
    do boto3 (`core/config.py::Settings` não as modela, de propósito).
    """

    provider_name = "s3"

    def __init__(self, *, bucket_name: str, region_name: str, endpoint_url: str | None) -> None:
        self._bucket_name = bucket_name
        self._client = boto3.client("s3", region_name=region_name, endpoint_url=endpoint_url)

    async def save(self, *, stream: BinaryIO, suggested_name: str) -> str:
        storage_key = f"{uuid.uuid4().hex}-{suggested_name}"
        await asyncio.to_thread(self._client.upload_fileobj, stream, self._bucket_name, storage_key)
        return storage_key

    async def open(self, storage_key: str) -> Path:
        """Baixa o objeto para um arquivo temporário local e devolve o `Path` —
        mantém `download_attachment` (`features/attachments/router.py`) idêntico
        entre providers (`FileResponse` continua funcionando sem mudança de
        contrato), ao custo de um round-trip extra pelo disco local a cada
        download. Quem chama é responsável por apagar o arquivo temporário
        depois de servi-lo (`storage.provider_name != "local"` no router,
        via `BackgroundTask` — apagar incondicionalmente apagaria o arquivo de
        origem real de `LocalStorageProvider`, não uma cópia temporária).
        """
        destination = Path(tempfile.mkstemp(prefix="flowdesk-attachment-")[1])
        try:
            await asyncio.to_thread(
                self._client.download_file, self._bucket_name, storage_key, str(destination)
            )
        except Exception:
            await asyncio.to_thread(destination.unlink, True)
            raise
        return destination

    async def delete(self, storage_key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object, Bucket=self._bucket_name, Key=storage_key
        )


def get_storage_provider(settings: Settings = Depends(get_settings)) -> StorageProvider:
    """`settings: Settings = Depends(get_settings)`, não um default `None` bare —
    um parâmetro tipado como `BaseModel`/`BaseSettings` sem marcador explícito de
    dependency, mesmo com default, faz o FastAPI 0.115 tratá-lo como um segundo
    campo de *body* implícito, forçando o body real da rota a ser embrulhado sob
    o nome do parâmetro (`{"payload": {...}}` em vez do JSON direto) — quebra
    qualquer endpoint que dependa disto, mesmo transitivamente (achado real
    durante a validação retroativa desta sessão, ver ADR-042).
    """
    if settings.storage_provider == "s3":
        assert settings.s3_bucket_name is not None  # já validado por Settings na inicialização
        return S3StorageProvider(
            bucket_name=settings.s3_bucket_name,
            region_name=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
        )
    return LocalStorageProvider(Path(settings.upload_dir))
