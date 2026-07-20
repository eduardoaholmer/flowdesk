import io
import os

import boto3
import pytest
from botocore.exceptions import ClientError
from src.core.storage import S3StorageProvider

# Env vars dedicadas deste teste, independentes de `STORAGE_PROVIDER`/`S3_*` do
# `Settings` da aplicação (que continua "local" por padrão em todo o resto da
# suíte) — exercitam `S3StorageProvider` contra um MinIO efêmero (mesmo padrão
# já usado para Postgres/Redis: serviço real em container, não mock).
_ENDPOINT_URL = os.environ.get("S3_TEST_ENDPOINT_URL", "http://localhost:9000")
_BUCKET_NAME = os.environ.get("S3_TEST_BUCKET_NAME", "flowdesk-test")
_REGION = os.environ.get("S3_TEST_REGION", "us-east-1")


@pytest.fixture(scope="module", autouse=True)
def _ensure_bucket() -> None:
    """MinIO não cria bucket sozinho — criado aqui de forma idempotente, mesmo
    papel que `alembic upgrade head` cumpre para o schema do Postgres em CI.
    """
    client = boto3.client("s3", region_name=_REGION, endpoint_url=_ENDPOINT_URL)
    try:
        client.create_bucket(Bucket=_BUCKET_NAME)
    except ClientError as error:
        code = error.response["Error"]["Code"]
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise


@pytest.fixture
def provider() -> S3StorageProvider:
    return S3StorageProvider(
        bucket_name=_BUCKET_NAME, region_name=_REGION, endpoint_url=_ENDPOINT_URL
    )


async def test_save_open_delete_round_trip(provider: S3StorageProvider) -> None:
    content = b"conteudo de teste do FlowDesk"

    storage_key = await provider.save(stream=io.BytesIO(content), suggested_name="arquivo.txt")
    assert storage_key.endswith("-arquivo.txt")

    path = await provider.open(storage_key)
    try:
        assert path.read_bytes() == content
    finally:
        path.unlink()

    await provider.delete(storage_key)

    with pytest.raises(ClientError):
        await provider.open(storage_key)


async def test_save_generates_unique_keys_for_same_suggested_name(
    provider: S3StorageProvider,
) -> None:
    first = await provider.save(stream=io.BytesIO(b"a"), suggested_name="same.txt")
    second = await provider.save(stream=io.BytesIO(b"b"), suggested_name="same.txt")

    assert first != second

    await provider.delete(first)
    await provider.delete(second)
