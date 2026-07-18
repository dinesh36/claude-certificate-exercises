# Testing Conventions

- Every package ships its tests under `tests/`, mirroring the package's own module layout.
- Use `pytest`. No live network calls and no real database connections in unit tests — mock external I/O.
- A pull request may not merge below 85% line coverage for the package it touches.

These conventions are universal across this repo — every package inherits them from the project root regardless of which package-specific rules it also imports.
