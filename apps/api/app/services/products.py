import hashlib
import logging

from fastapi import Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.events import CatalogEvents
from app.models import Product
from app.repositories import products as repository
from app.schemas import ProductRead
from app.storage import CONTENT_TYPE_EXTENSIONS, Storage

logger = logging.getLogger(__name__)

MAX_PHOTO_BYTES = 8 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
MAX_TITLE_LENGTH = 200


class ProductError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def clean_title(value: str) -> str:
    title = value.strip()
    if not title:
        raise ProductError("Title must not be empty")
    if len(title) > MAX_TITLE_LENGTH:
        raise ProductError("Title is too long")
    return title


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def image_extension(content_type: str | None) -> str:
    extension = CONTENT_TYPE_EXTENSIONS.get(normalize_content_type(content_type))
    if extension is None:
        raise ProductError("Unsupported image type")
    return extension


def image_key(data: bytes, extension: str) -> str:
    digest = hashlib.sha256(data).hexdigest()
    return f"products/{digest}.{extension}"


async def read_photo(photo: UploadFile) -> bytes:
    data = bytearray()
    while chunk := await photo.read(CHUNK_SIZE):
        data.extend(chunk)
        if len(data) > MAX_PHOTO_BYTES:
            raise ProductError("Image is too large", status_code=413)
    if not data:
        raise ProductError("Image is empty")
    return bytes(data)


class ProductService:
    def __init__(
        self,
        storage: Storage,
        public_base_url: str,
        events: CatalogEvents,
    ) -> None:
        self._storage = storage
        self._public_base_url = public_base_url.rstrip("/")
        self._events = events

    async def list(self, session: AsyncSession, limit: int, offset: int) -> list[ProductRead]:
        products = await repository.list_products(session, limit, offset)
        return [await self._read(product) for product in products]

    async def create(self, session: AsyncSession, title: str, photo: UploadFile) -> ProductRead:
        clean = clean_title(title)
        content_type = normalize_content_type(photo.content_type)
        extension = image_extension(content_type)
        data = await read_photo(photo)

        key = image_key(data, extension)
        await self._storage.upload(key, data, content_type)
        product = await repository.create_product(session, clean, key)
        result = await self._read(product)
        try:
            await self._events.publish(result.model_dump_json())
        except Exception:
            logger.exception("Failed to publish catalog event")
        return result

    async def image(self, key: str) -> tuple[bytes, str] | None:
        if not key.startswith("products/") or ".." in key:
            return None
        return await self._storage.read(key)

    async def _read(self, product: Product) -> ProductRead:
        return ProductRead(
            id=product.id,
            title=product.title,
            image_url=f"{self._public_base_url}/api/images/{product.image_key}",
            created_at=product.created_at,
        )


def get_product_service(request: Request) -> ProductService:
    return ProductService(
        request.app.state.storage,
        get_settings().public_base_url,
        request.app.state.events,
    )
