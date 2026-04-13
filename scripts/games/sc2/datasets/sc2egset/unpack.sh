#!/bin/bash
# Extracts top-level tournament ZIPs from ~/Downloads/ into sc2egset/raw/.
# Run once per new batch of downloaded ZIPs.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
SOURCE="$HOME/Downloads"
TARGET="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"

mkdir -p "$TARGET"

# Use nullglob to handle cases where no files match
shopt -s nullglob

for zip_file in "$SOURCE"/20[0-9][0-9]_*.zip; do
    # Check if file exists (redundant with nullglob but safe)
    [[ -f "$zip_file" ]] || continue

    base_name=$(basename "$zip_file" .zip)
    extract_dir="$TARGET/$base_name"

    # Skip if directory exists and has files
    if [[ -d "$extract_dir" ]] && [[ $(find "$extract_dir" -type f | wc -l) -gt 0 ]]; then
        echo ">>> Skipping (already done): $base_name"
        continue
    fi

    echo ">>> Extracting: $base_name"
    mkdir -p "$extract_dir"

    # Using ditto instead of unzip.
    # -x: extract, -k: treat as archive, -V: verbose (optional)
    if ditto -x -k "$zip_file" "$extract_dir"; then
        echo "    Done: $base_name"
    else
        echo "    ERROR: Failed to extract $base_name"
        # Clean up the empty folder so it tries again next time
        rmdir "$extract_dir" 2>/dev/null
    fi
    echo ""
done

echo "All done!"
