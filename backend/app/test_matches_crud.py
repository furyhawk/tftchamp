from routers.matchdetails import router as matchdetails_router
from config import settings
import asyncio
from fastapi import FastAPI, status
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

import pytest

pytest_plugins = ("pytest_asyncio",)


app: FastAPI = FastAPI()


@app.on_event("startup")
async def startup_event() -> None:
    app.mongodb_client = AsyncIOMotorClient(settings.db_uri)
    app.mongodb_client.get_io_loop = asyncio.get_running_loop
    app.database = app.mongodb_client[settings.db_name + "_test"]


@app.on_event("shutdown")
async def shutdown_event() -> None:
    app.database.drop_collection("oc1_matches_detail")
    app.mongodb_client.close()


app.include_router(matchdetails_router, tags=["matchdetails"], prefix="/matchdetail")


sample_post = {
    "_id": "OC1_526884682",
    "metadata": {
        "data_version": "string",
        "match_id": "string",
        "participants": ["string"],
    },
    "info": {
        "game_datetime": 0,
        "game_length": 0,
        "game_version": "string",
        "participants": [
            {
                "augments": ["string"],
                "companion": {
                    "content_ID": "string",
                    "skin_ID": 0,
                    "species": "string",
                },
                "gold_left": 0,
                "last_round": 0,
                "level": 0,
                "placement": 0,
                "players_eliminated": 0,
                "puuid": "string",
                "time_eliminated": 0,
                "total_damage_to_players": 0,
                "traits": [
                    {
                        "name": "string",
                        "num_units": 0,
                        "style": 0,
                        "tier_current": 0,
                        "tier_total": 0,
                    }
                ],
                "units": [
                    {
                        "character_id": "string",
                        "itemNames": ["string"],
                        "items": [0],
                        "name": "string",
                        "rarity": 0,
                        "tier": 0,
                    }
                ],
            }
        ],
        "queue_id": 0,
        "tft_game_type": "string",
        "tft_set_core_name": "string",
        "tft_set_number": 0,
    },
}


@pytest.mark.asyncio
async def test_create_match() -> None:
    with TestClient(app=app) as client:
        response = client.post("/matchdetail/", json=sample_post)
        assert response.status_code == 201

        body = response.json()
        assert body.get("info").get("tft_game_type") == "string"
        assert body.get("info").get("tft_set_core_name") == "string"
        assert body.get("info").get("tft_set_number") == 0
        assert "_id" in body


@pytest.mark.asyncio
async def test_create_match_missing_match_id() -> None:
    with TestClient(app=app) as client:
        response = client.post(
            "/matchdetail/",
            json={"metadata": {"data_version": "string", "participants": ["string"]}},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_match() -> None:
    with TestClient(app=app) as client:
        new_match = client.post("/matchdetail/", json=sample_post).json()
        get_match_response = client.get("/matchdetail/" + new_match.get("_id"))
        assert get_match_response.status_code == 200
        assert get_match_response.json() == new_match


@pytest.mark.asyncio
async def test_get_match_unexisting() -> None:
    with TestClient(app=app) as client:
        get_match_response = client.get("/matchdetail/unexisting_id")
        assert get_match_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_update_match() -> None:
    with TestClient(app=app) as client:
        new_match = client.post("/matchdetail/", json=sample_post).json()
        sample_post["metadata"]["data_version"] = "Don Quixote 1"
        response = client.put("/matchdetail/" + new_match.get("_id"), json=sample_post)
        assert response.status_code == 200
        assert response.json().get("metadata").get("data_version") == "Don Quixote 1"


@pytest.mark.asyncio
async def test_update_match_unexisting() -> None:
    with TestClient(app=app) as client:
        update_match_response = client.put(
            "/matchdetail/unexisting_id", json=sample_post
        )
        assert update_match_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_match() -> None:
    with TestClient(app=app) as client:
        new_match = client.post("/matchdetail/", json=sample_post).json()

        delete_match_response = client.delete("/matchdetail/" + new_match.get("_id"))
        assert delete_match_response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_match_unexisting() -> None:
    with TestClient(app=app) as client:
        delete_match_response = client.delete("/matchdetail/unexisting_id")
        assert delete_match_response.status_code == status.HTTP_404_NOT_FOUND
