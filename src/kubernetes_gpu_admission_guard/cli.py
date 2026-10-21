import argparse
import json
from pathlib import Path

from .engine import evaluate


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a Kubernetes GPU workload admission snapshot")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = evaluate(json.loads(args.input.read_text()))
    rendered = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\n")
    else:
        print(rendered)
    return 2 if result["decision"] == "BLOCK" else 0
