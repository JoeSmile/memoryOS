"""L1 Harness：2022 世界杯比赛列表（需 PostgreSQL + migrate + WC ETL）。"""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.worldcup_match_service import WC_2022_TOURNAMENT_ID


def _envelope(body: dict) -> None:
    assert body["code"] == 0
    assert body["message"] == "ok"
    assert "data" in body


@pytest.mark.asyncio
async def test_worldcup_matches_wc2022_contract():
    transport = ASGITransport(app=app)
    email = f"harness-wc-{uuid.uuid4()}@example.com"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        user_resp = await client.post("/api/v1/users", json={"email": email})
        assert user_resp.status_code == 200
        user_id = user_resp.json()["data"]["id"]

        from app.core.security import create_access_token

        token = create_access_token(user_id)

        resp = await client.get(
            "/api/v1/worldcup/matches",
            params={"tournament_id": WC_2022_TOURNAMENT_ID},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        body = resp.json()
        _envelope(body)
        data = body["data"]
        assert data["tournament_id"] == WC_2022_TOURNAMENT_ID
        assert isinstance(data["stages"], list)

        if data["stages"]:
            first_stage = data["stages"][0]
            assert "stage_name" in first_stage
            assert "stage_label" in first_stage
            assert isinstance(first_stage["matches"], list)
            if first_stage["matches"]:
                assert "home_team_name" in first_stage["matches"][0]

        bad = await client.get(
            "/api/v1/worldcup/matches",
            params={"tournament_id": "WC-2018"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert bad.status_code == 422
