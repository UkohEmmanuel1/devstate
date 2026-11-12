import httpx
from .config import Settings

class PhoneNotifier:
    """Push phone alerts through ntfy; no topic means safely disabled."""
    def __init__(self, config: Settings):
        self.config = config

    @property
    def enabled(self) -> bool:
        return bool(self.config.ntfy_topic.strip())

    async def send(self, title: str, message: str, priority: int = 3, tags=None) -> bool:
        if not self.enabled:
            return False
        url = f"{self.config.ntfy_server.rstrip('/')}/{self.config.ntfy_topic.strip()}"
        headers = {"Title": title[:160], "Priority": str(max(1,min(5,priority))),
                   "Tags": ",".join(tags or ["computer"])}
        if self.config.ntfy_token:
            headers["Authorization"] = f"Bearer {self.config.ntfy_token}"
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, content=message[:2000].encode(), headers=headers)
            response.raise_for_status()
        return True
