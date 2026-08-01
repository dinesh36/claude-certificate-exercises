# CLAUDE.md

Universal conventions for the multiplayer game backend monorepo: `matchmaking_service/`, `leaderboard_service/`, and the `shared_protocol/` package both services import from.

## Coding standards

- Python 3.11+, full type hints on every public function.
- Prefer `dataclasses` for shared data shapes (see `shared_protocol/types.py`) over bare dicts.
- No service imports another service directly — shared shapes only ever live in `shared_protocol/`.

## Testing conventions

- Every package has its own `tests/` directory, run with `pytest`.
- New logic needs a test in the same change — no "add tests later" follow-ups.

## Directory-level conventions

`matchmaking_service/` and `leaderboard_service/` each have their own `CLAUDE.md` with service-specific conventions layered on top of these universal ones — see those files when working inside either directory.
