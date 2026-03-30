import httpx
from urllib.parse import urljoin

from app.core.config import settings

class LaravelRoutes:
    CHAT_FINALIZE = "internal/chat/finalize"
    FILE_OPERATIONS_WEBHOOK = "internal/file-operations/webhook"


class LaravelClient:
    def __init__(self) -> None:
        self.base_url = settings.LARAVEL_API_BASE_URL.rstrip("/") + "/"
        self.headers = {
            "X-Internal-Key": settings.INTERNAL_API_KEY,
        }

    def url(self, path: str) -> str:
        return urljoin(self.base_url, path.lstrip("/"))

    async def post(self, path: str, json: dict):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.url(path),
                headers=self.headers,
                json=json,
            )
            response.raise_for_status()
            return response

    async def get(self, path: str, params: dict | None = None):
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(
                self.url(path),
                headers=self.headers,
                params=params,
            )
            response.raise_for_status()
            return response


laravel_client = LaravelClient()
laravel_routes = LaravelRoutes()