"""Build FAISS index + ID map from the local dataset.

Usage:
    python scripts/build_faiss.py
    python scripts/build_faiss.py --products data/amazon.csv --model all-MiniLM-L6-v2
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--products", default="data/amazon.csv", help="Input products CSV")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="SentenceTransformer model name")
    parser.add_argument("--index-out", default="data/faiss_index.idx", help="Output FAISS index path")
    parser.add_argument("--idmap-out", default="data/id_map.pkl", help="Output ID map path")
    parser.add_argument("--nrows", type=int, default=None, help="Optional row limit for quick builds")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    builder = repo_root / "data" / "ingest_and_embed.py"

    if not builder.exists():
        print(f"[ERROR] Missing builder script: {builder}")
        return 1

    cmd = [
        sys.executable,
        str(builder),
        "--products",
        str(repo_root / args.products),
        "--model",
        args.model,
        "--index-out",
        str(repo_root / args.index_out),
        "--idmap-out",
        str(repo_root / args.idmap_out),
    ]
    if args.nrows is not None:
        cmd.extend(["--nrows", str(args.nrows)])

    print("[INFO] Building FAISS index...")
    print("[CMD]", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(repo_root))
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
