from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create the ScoutGraph FastAPI application."""
    app = FastAPI(
        title="ScoutGraph API",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": "scoutgraph",
        }

    return app


app = create_app()
