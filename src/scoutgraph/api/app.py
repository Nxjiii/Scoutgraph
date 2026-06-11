from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel

from scoutgraph.identity.player_identity import build_player_identity
from scoutgraph.storage.paths import ProjectPaths


class PlayerIdentityResponse(BaseModel):
    player_name: str
    team_name: str
    position_group: str
    labels: list[str]
    summary: str


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
