#!/usr/bin/env bash
# Extracts each <dir>.zip under raw/ into its corresponding <dir>/ subdirectory.
# Files are stored at zip root (no parent wrapper) — matches rezip_data.sh convention.
#
# Covers: matches.zip  players.zip  overview.zip
#
# Safe to re-run: skips any target dir that already has files.
# Run this to restore raw/ after remove_data_dirs.sh or an accidental zip.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/aoe2/datasets/aoestats/data/raw"

if [[ ! -d "$TARGET" ]]; then
    echo "Error: $TARGET not found."
    exit 1
fi

shopt -s nullglob

total=0
skipped=0
failed=0

for zip_file in "$TARGET"/*.zip; do
    [[ -f "$zip_file" ]] || continue

    folder_name=$(basename "$zip_file" .zip)
    extract_dir="${TARGET}/${folder_name}"

    echo ">>> Processing: $folder_name"

    # Skip if directory already has files
    file_count=$(find "$extract_dir" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$file_count" -gt 0 ]]; then
        echo "    Skip: $folder_name/ already has $file_count file(s)."
        ((skipped++))
        echo "---"
        continue
    fi

    zip_size=$(du -sh "$zip_file" | awk '{print $1}')
    zip_count=$(unzip -Z1 "$zip_file" 2>/dev/null | grep -cv "^\._" || true)
    echo "    Extracting $zip_count files ($zip_size)..."

    mkdir -p "$extract_dir"

    # ditto -x -k: extract zip archive into target directory
    if ditto -x -k "$zip_file" "$extract_dir"; then
        extracted=$(find "$extract_dir" -type f | wc -l | tr -d ' ')
        echo "    Done: $extracted file(s) extracted to $folder_name/"
        ((total++))
    else
        echo "    ERROR: Failed to extract $folder_name"
        ((failed++))
    fi

    echo "---"
done

echo ""
echo "Extracted: $total  |  Skipped (already have files): $skipped  |  Failed: $failed"
