import json
import sys


def main(findings_path: str) -> None:
    with open(findings_path) as f:
        findings = json.load(f)["findings"]

    new_findings = [f for f in findings if f["status"] == "new"]
    for f in new_findings:
        print(f"[inline comment] {f['file']}:{f.get('line', '?')} ({f['severity']}) {f['description']}")

    skipped = len(findings) - len(new_findings)
    if skipped:
        print(f"Skipped {skipped} finding(s) already reported on a prior run.")


if __name__ == "__main__":
    main(sys.argv[1])
