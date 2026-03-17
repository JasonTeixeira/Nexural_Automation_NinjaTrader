from __future__ import annotations

import argparse
from pathlib import Path

from nexural_research.ingest.nt_csv import load_nt_trades_csv, save_processed
from nexural_research.utils.paths import paths


def _cmd_ingest(args: argparse.Namespace) -> int:
    project = paths()
    in_path = Path(args.input) if args.input else (project.root / "data" / "exports" / "sample_trades.csv")
    out_path = Path(args.output) if args.output else (project.root / "data" / "processed" / "trades.parquet")

    df = load_nt_trades_csv(in_path)
    save_processed(df, out_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="nexural-research", description="Nexural research utilities")
    sub = p.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest a NinjaTrader trades CSV")
    ingest.add_argument("--input", "-i", help="Path to NinjaTrader trades CSV")
    ingest.add_argument("--output", "-o", help="Output path (.parquet or .csv)")
    ingest.set_defaults(func=_cmd_ingest)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
