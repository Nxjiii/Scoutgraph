# ScoutGraph

ScoutGraph is a football intelligence backend that turns public football data into player and team tactical profiles, similarity results, and explainable scouting-style outputs.

The first phase of the project is backend-only:

- ingest football data from source adapters
- normalize it into local analytical tables
- engineer player and team features
- calculate stylistic similarity
- expose the results through an API later

## Current Status

This repo is in the first backend phase. It can list available StatsBomb Open Data competition-seasons, fetch and normalize match data, query normalized pass data, generate player and team feature matrices, calculate per-90 player metrics, inspect generated vectors, and run a first player-similarity baseline.

## Planned Backend Shape

```text
src/scoutgraph/
  sources/       # source-specific adapters: StatsBomb, Understat, etc.
  storage/       # local paths and storage helpers
  features/      # player/team feature engineering
  similarity/    # vector normalization and nearest-neighbor search
  api/           # FastAPI endpoints later
```

## Data Policy

ScoutGraph works with public football data sources and documents source-specific attribution and usage requirements as integrations are added.

## Current Commands

List available StatsBomb competition-seasons and matches:

```bash
scoutgraph list statsbomb-competitions
scoutgraph list statsbomb-matches --competition-id 9 --season-id 281
```

Fetch the starter StatsBomb sample:

```bash
scoutgraph ingest statsbomb-sample
```

Fetch a specific StatsBomb match:

```bash
scoutgraph ingest statsbomb-match --competition-id 9 --season-id 281 --match-id 3895302
```

Fetch a limited StatsBomb season subset:

```bash
scoutgraph ingest statsbomb-season --competition-id 9 --season-id 281 --limit 2
```

Inspect the cached raw sample:

```bash
scoutgraph inspect statsbomb-sample
scoutgraph inspect statsbomb-event
```

Normalize the sample into analytical tables:

```bash
scoutgraph normalize statsbomb-sample
```

Normalize a specific StatsBomb match:

```bash
scoutgraph normalize statsbomb-match --competition-id 9 --season-id 281 --match-id 3895302
```

Normalize a limited StatsBomb season subset:

```bash
scoutgraph normalize statsbomb-season --competition-id 9 --season-id 281 --limit 2
```

Query normalized pass data:

```bash
scoutgraph query passes --match-id 3895302 --limit 5
scoutgraph query passes --match-id 3895302 --team "Bayer Leverkusen" --limit 5
scoutgraph query passes --match-id 3895302 --player "Granit Xhaka" --limit 5
```

Build player passing features:

```bash
scoutgraph features player-passing --match-id 3895302 --limit 10
```

Build player carrying features:

```bash
scoutgraph features player-carrying --match-id 3895302 --limit 10
```

Build player shooting features:

```bash
scoutgraph features player-shooting --match-id 3895302 --limit 10
```

Build the combined player feature matrix:

```bash
scoutgraph features player-matrix --match-id 3895302 --limit 10
```

The combined matrix includes minutes played and per-90 versions of volume metrics for fairer
player comparisons.

Build the combined team feature matrix:

```bash
scoutgraph features team-matrix --match-id 3895302
```

Inspect generated player and team vectors for suspicious feature values:

```bash
scoutgraph inspect player-vector --player "Granit Xhaka"
scoutgraph inspect team-vector --team "Bayer Leverkusen"
```

Find similar players from the generated feature matrix:

```bash
scoutgraph similarity players --player "Granit Xhaka" --limit 5
```

Limit similarity results to the same broad position group:

```bash
scoutgraph similarity players --player "Granit Xhaka" --same-position --limit 5
```

Show shared traits, key differences, confidence, and limitations for similar players:

```bash
scoutgraph similarity players --player "Granit Xhaka" --same-position --explain --limit 5
```

Run known player similarity sanity examples:

```bash
scoutgraph similarity examples
```

## Documentation

Longer methodology, architecture, and setup guides will be added as the backend takes shape.

## Development

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run the project info command:

```bash
scoutgraph info
```

Run tests:

```bash
pytest
```
