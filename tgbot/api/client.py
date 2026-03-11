import httpx

from tgbot.config import settings


async def create_ticket(data: dict) -> dict:
    async with httpx.AsyncClient(base_url=settings.backend_url) as client:
        resp = await client.post("/api/tickets", json=data)
        resp.raise_for_status()
        return resp.json()


async def cancel_ticket(ticket_id: str) -> None:
    async with httpx.AsyncClient(base_url=settings.backend_url) as client:
        resp = await client.delete(f"/api/tickets/{ticket_id}")
        resp.raise_for_status()


async def list_tickets() -> list[dict]:
    async with httpx.AsyncClient(base_url=settings.backend_url) as client:
        resp = await client.get("/api/tickets")
        resp.raise_for_status()
        return resp.json()
