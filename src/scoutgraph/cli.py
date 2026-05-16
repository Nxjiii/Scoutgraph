from typing import Annotated

import typer

from scoutgraph.storage.paths import ProjectPaths

app = typer.Typer(help="ScoutGraph backend tools.")


@app.command()
def info(
    root: Annotated[
        str | None,
        typer.Option(help="Project root. Defaults to the current working directory."),
    ] = None,
) -> None:
    """Print the local ScoutGraph project paths."""
    paths = ProjectPaths.from_root(root)

    typer.echo("ScoutGraph backend")
    typer.echo(f"root: {paths.root}")
    typer.echo(f"raw data: {paths.raw_data}")
    typer.echo(f"processed data: {paths.processed_data}")
    typer.echo(f"cache: {paths.cache}")

