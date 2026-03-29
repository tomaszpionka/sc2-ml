from pathlib import Path

# Ścieżki lokalnego projektu (gdzie żyje kod, manifest i baza)
ROOT_PROJECTS_DIR = Path("~/Projects/sc2-ml").expanduser().resolve()
DB_FILE = Path("~/duckdb_work/test_sc2.duckdb").expanduser().resolve()
MANIFEST_PATH = ROOT_PROJECTS_DIR / "processing_manifest.json"

# Konfiguracja DuckDB
DUCKDB_TEMP_DIR = Path("~/duckdb_work/tmp").expanduser().resolve()

# Ścieżka do surowych powtórek w Downloads
REPLAYS_SOURCE_DIR = Path("~/Downloads/SC2_Replays").expanduser().resolve()
