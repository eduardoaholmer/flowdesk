import asyncio
import uuid
from pathlib import Path
from typing import BinaryIO, Protocol

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


def get_storage_provider(settings: Settings | None = None) -> LocalStorageProvider:
    settings = settings or get_settings()
    return LocalStorageProvider(Path(settings.upload_dir))
