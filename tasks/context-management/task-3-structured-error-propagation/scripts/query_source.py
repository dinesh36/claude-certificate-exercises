#!/usr/bin/env python3
"""Mock vendor-data-source lookup tool.

Each subagent shells out to this script instead of an MCP tool, so its
behavior (success, valid-empty, retryable timeout, or permanent outage) is
real, deterministic, and driven entirely by data/source_config.json plus the
--attempt flag the caller passes — no hidden state, no randomness. This is
what a coordinator/subagent pair actually calls to see error propagation
happen for real, not just get narrated about.
"""

import argparse
import json
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = TASK_ROOT / "data" / "source_config.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()

    config = load_config()
    if args.source not in config:
        print(json.dumps({
            "status": "error",
            "error_type": "unknown_source",
            "detail": f"no such source configured: {args.source}",
            "retryable": False,
        }))
        sys.exit(1)

    cfg = config[args.source]
    mode = cfg["mode"]

    if mode == "ok":
        results = json.loads((TASK_ROOT / "data" / cfg["result_file"]).read_text())
        print(json.dumps({"status": "success", "source": args.source, "results": results}))
        return

    if mode == "empty":
        print(json.dumps({"status": "success", "source": args.source, "results": []}))
        return

    if mode == "transient":
        if args.attempt < cfg["recovers_after_attempt"]:
            print(json.dumps({
                "status": "error",
                "error_type": "timeout",
                "detail": f"{args.source} did not respond within the request window (attempt {args.attempt}).",
                "retryable": True,
            }))
            sys.exit(1)
        results = json.loads((TASK_ROOT / "data" / cfg["result_file"]).read_text())
        print(json.dumps({
            "status": "success",
            "source": args.source,
            "results": results,
            "recovered_after_attempts": args.attempt,
        }))
        return

    if mode == "down":
        print(json.dumps({
            "status": "error",
            "error_type": cfg.get("error_type", "access_denied"),
            "detail": cfg.get("detail", f"{args.source} is unavailable."),
            "retryable": False,
            "alternative": cfg.get("alternative"),
        }))
        sys.exit(1)

    raise ValueError(f"unknown mode {mode!r} for source {args.source}")


if __name__ == "__main__":
    main()
