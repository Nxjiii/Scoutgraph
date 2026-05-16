# ScoutGraph

ScoutGraph is a football intelligence backend that turns public football data into player and team tactical profiles, similarity results, and explainable scouting-style outputs.

The first phase of the project is backend-only:

- ingest football data from source adapters
- normalize it into local analytical tables
- engineer player and team features
- calculate stylistic similarity
- expose the results through an API later

## Current Status

This repo is in the first backend phase. It can fetch a small StatsBomb Open Data sample, inspect the raw event structure, and normalize the sample into local analytical tables.

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

Fetch the starter StatsBomb sample:

```bash
scoutgraph ingest statsbomb-sample
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
