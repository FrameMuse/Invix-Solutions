import httpx


class ProductApi:
    def __init__(self, base_url: str, service_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"X-Service-Token": service_token},
            timeout=30.0,
        )

    async def create_product(self, title: str, photo: bytes) -> None:
        response = await self._client.post(
            "/internal/products",
            data={"title": title},
            files={"photo": ("product.jpg", photo, "image/jpeg")},
        )
        response.raise_for_status()

    async def close(self) -> None:
        await self._client.aclose()
