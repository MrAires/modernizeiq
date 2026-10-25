"""Run with: python -m backend.app.cli analyze --repo PATH --out PATH"""

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

from backend.app.core.models import AssessmentError
from backend.app.security.ingestion import read_local, read_zip
from backend.app.services.assessment import assess
from backend.app.services.report import executive_text, render_html


def write_outputs(data: dict, out: Path, overwrite: bool = False) -> None:
    outputs = {"assessment.json": json.dumps(data, indent=2, ensure_ascii=False) + "\n",
               "assessment.html": render_html(data), "executive-summary.txt": executive_text(data)}
    if any((out / name).exists() for name in outputs) and not overwrite:
        raise AssessmentError("Output already exists. Choose a new directory or explicitly pass --overwrite.")
    out.mkdir(parents=True, exist_ok=True)
    for name, text in outputs.items():
        fd, temporary = tempfile.mkstemp(prefix=".modernizeiq-", dir=out)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
            os.replace(temporary, out / name)
        finally:
            Path(temporary).unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ModernizeIQ deterministic static assessment. Never executes repository code.")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Inspect a local repository or ZIP")
    source = analyze.add_mutually_exclusive_group(required=True)
    source.add_argument("--repo", type=Path)
    source.add_argument("--zip", type=Path)
    analyze.add_argument("--out", type=Path, required=True)
    analyze.add_argument("--scoring", type=Path, help="Custom scoring configuration")
    analyze.add_argument("--overwrite", action="store_true", help="Replace previously generated reports in the output directory")
    args = parser.parse_args(argv)
    try:
        if args.repo and args.out.resolve().is_relative_to(args.repo.resolve()):
            raise AssessmentError("Choose an output folder outside the scanned repository to avoid analyzing generated reports on later runs.")
        snapshot = read_local(args.repo) if args.repo else read_zip(args.zip)
        result = assess(snapshot, args.scoring)
        write_outputs(result, args.out, args.overwrite)
        print(f"Assessed {result['profile']['files_analyzed']} files; {len(result['findings'])} selected indicators.")
        print(f"Readiness heuristic: {result['readiness']['overall']}/100. Not measured test coverage.")
        print(f"Open: {args.out.resolve() / 'assessment.html'}")
        print(f"Warnings: {len(result['warnings'])}; skipped entries: {len(result['skipped'])}.")
        return 0
    except (AssessmentError, OSError) as exc:
        # OSError can contain full paths and details; keep failure messages bounded.
        message = str(exc) if isinstance(exc, AssessmentError) else "An input or output file could not be accessed. Check paths and permissions."
        print(f"Assessment failed: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
