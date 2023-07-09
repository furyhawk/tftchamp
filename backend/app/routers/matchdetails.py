from enum import Enum
from fastapi import (
    APIRouter,
    Body,
    Request,
    Response,
    HTTPException,
    Depends,
    Query,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import List, Tuple

from models.matchdetail import MatchDetail, MatchDetailUpdate

router = APIRouter()


class Platform(str, Enum):
    euw1 = ("euw1",)
    br1 = ("br1",)
    eun1 = ("eun1",)
    jp1 = ("jp1",)
    kr = ("kr",)
    la1 = ("la1",)
    la2 = ("la2",)
    na1 = ("na1",)
    oc1 = ("oc1",)
    tr1 = ("tr1",)
    ru = "ru"


async def pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=0),
) -> Tuple[int, int]:
    capped_limit: int = min(20, limit)
    return (skip, capped_limit)


@router.post(
    "/",
    response_description="Create a new match",
    status_code=status.HTTP_201_CREATED,
    response_model=MatchDetail,
)
async def create_match(
    request: Request, match: MatchDetail = Body(...)
) -> JSONResponse:
    match: MatchDetail = jsonable_encoder(match)
    new_match = await request.app.database[f"oc1_matches_detail"].insert_one(match)
    created_match = await request.app.database["oc1_matches_detail"].find_one(
        {"_id": new_match.inserted_id}
    )

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_match)


@router.get(
    "/", response_description="List all matches", response_model=List[MatchDetail]
)
async def list_matches(
    request: Request,
    platform: Platform = "na1",
    pagination: Tuple[int, int] = Depends(pagination),
) -> list[MatchDetail]:
    skip, limit = pagination
    query = request.app.database[f"{platform}_matches_detail"].find(
        {}, skip=skip, limit=limit
    )
    results = [MatchDetail(**raw_post) async for raw_post in query]
    return results


@router.get(
    "/{id}", response_description="Get a single match by id", response_model=MatchDetail
)
async def find_match(id: str, request: Request, platform: Platform = "na1"):
    if (
        match := await request.app.database[f"{platform}_matches_detail"].find_one(
            {"_id": id}
        )
    ) is not None:
        return match

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"MatchDetail with ID {id} not found",
    )


@router.put("/{id}", response_description="Update a match", response_model=MatchDetail)
async def update_match(id: str, request: Request, match: MatchDetailUpdate = Body(...)):
    match: MatchDetailUpdate = {k: v for k, v in match.dict().items() if v is not None}

    if len(match) >= 1:
        update_result = await request.app.database[f"oc1_matches_detail"].update_one(
            {"_id": id}, {"$set": match}
        )

        if update_result.modified_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MatchDetail with ID {id} not found",
            )

    if (
        existing_match := await request.app.database[f"oc1_matches_detail"].find_one(
            {"_id": id}
        )
    ) is not None:
        return existing_match

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"MatchDetail with ID {id} not found",
    )


@router.delete("/{id}", response_description="Delete a match")
async def delete_match(id: str, request: Request, response: Response) -> JSONResponse:
    delete_result = await request.app.database[f"oc1_matches_detail"].delete_one(
        {"_id": id}
    )

    if delete_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content="")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"MatchDetail with ID {id} not found",
    )
