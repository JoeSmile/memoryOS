"""L1 Harness：健康检查 API 契约（不依赖外部 DB）。"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_unified_envelope():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for path in ("/health", "/api/v1/health"):
            resp = await client.get(path)
            assert resp.status_code == 200
            body = resp.json()
            assert body["code"] == 0
            assert body["message"] == "ok"
            assert body["data"]["status"] == "ok"
            assert "app" in body["data"]
            assert "env" in body["data"]
