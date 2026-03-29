import os
from pathlib import Path

# Paths
ROOT_PROJECTS_DIR = Path("/home/tomasz/projects/sc2-ml").resolve()
DB_FILE = Path("/home/tomasz/duckdb_work/test_sc2.duckdb").resolve()
MANIFEST_PATH = ROOT_PROJECTS_DIR / "processing_manifest.json"

# DuckDB config
DUCKDB_TEMP_DIR = "/home/tomasz/duckdb_work/tmp"
