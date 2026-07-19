from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query
from pydantic import BaseModel

from scoutgraph.api.player_analysis import get_player_profile
from scoutgraph.api.player_analysis import search_players
from scoutgraph.identity.player_identity import build_player_identity
from scoutgraph.similarity.player_similarity import evaluate_similar_player_confidence
from scoutgraph.similarity.player_similarity import explain_similar_players
from scoutgraph.similarity.player_similarity import find_similar_players
from scoutgraph.storage.paths import ProjectPaths


class PlayerIdentityResponse(BaseModel):
    player_name: str
    team_name: str
    position_group: str
    labels: list[str]
    summary: str


class PlayerSummaryResponse(BaseModel):
    player_id: int
    player_name: str
    team_id: int
    team_name: str
    position_group: str | None


class PlayerProfileResponse(PlayerSummaryResponse):
    labels: list[str]
    summary: str
    metrics: dict[str, float]


class PlayerSimilarityResponse(PlayerSummaryResponse):
    similarity: float
    shared_traits: list[str]
    differences: list[str]
    confidence: str
    limitations: list[str]


def create_app(project_root: str | Path | None = None) -> FastAPI:
    """Create the ScoutGraph FastAPI application."""
    app = FastAPI(
        title="ScoutGraph API",
        version="0.1.0",
    )
    paths = ProjectPaths.from_root(project_root)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "scoutgraph",
        }

    @app.get("/players", response_model=list[PlayerSummaryResponse])
    def players(
        query: str = Query(min_length=1, max_length=100),
        limit: int = Query(default=10, ge=1, le=50),
    ) -> list[PlayerSummaryResponse]:
        try:
            matches = search_players(paths, query=query, limit=limit)
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return [PlayerSummaryResponse(**match.__dict__) for match in matches]

    @app.get("/players/{player}", response_model=PlayerProfileResponse)
    def player_profile(player: str) -> PlayerProfileResponse:
        try:
            profile = get_player_profile(paths, player=player)
            identity = build_player_identity(paths, player=player)
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return PlayerProfileResponse(
            player_id=profile.player_id,
            player_name=profile.player_name,
            team_id=profile.team_id,
            team_name=profile.team_name,
            position_group=profile.position_group,
            labels=list(identity.labels),
            summary=identity.summary,
            metrics=profile.metrics,
        )

    @app.get(
        "/players/{player}/similarity",
        response_model=list[PlayerSimilarityResponse],
    )
    def player_similarity(
        player: str,
        limit: int = Query(default=5, ge=1, le=25),
        same_position: bool = False,
    ) -> list[PlayerSimilarityResponse]:
        try:
            players = find_similar_players(
                paths,
                player=player,
                limit=limit,
                same_position=same_position,
            )
            explanations = explain_similar_players(paths, player=player, players=players)
            confidence = evaluate_similar_player_confidence(
                paths,
                player=player,
                players=players,
                same_position=same_position,
            )
            profiles = {
                (row.player_id, row.team_id): row
                for row in search_players(paths, query="", limit=10_000)
            }
        except FileNotFoundError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        results = []
        for _, row in players.iterrows():
            name = str(row["player_name"])
            profile = profiles[(int(row["player_id"]), int(row["team_id"]))]
            explanation = explanations[name]
            result_confidence = confidence[name]
            results.append(
                PlayerSimilarityResponse(
                    **profile.__dict__,
                    similarity=float(row["similarity"]),
                    shared_traits=list(explanation.shared_traits),
                    differences=list(explanation.differences),
                    confidence=result_confidence.level,
                    limitations=list(result_confidence.limitations),
                )
            )
        return results

    @app.get("/players/{player}/identity", response_model=PlayerIdentityResponse)
    def player_identity(player: str) -> PlayerIdentityResponse:
        try:
            identity = build_player_identity(paths, player=player)
        except (FileNotFoundError, ValueError) as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

        return PlayerIdentityResponse(
            player_name=identity.player_name,
            team_name=identity.team_name,
            position_group=identity.position_group,
            labels=list(identity.labels),
            summary=identity.summary,
        )

    return app


app = create_app()
