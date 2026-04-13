#!/usr/bin/env bash
# Re-zips each entity subdirectory under raw/ back into a <dir>.zip file placed
# beside it. Uses ditto (macOS native).
# Files land at zip root (no --keepParent).
#
# Covers: matches/ players/ overview/
#
# Safe to re-run: skips any entity dir where <dir>.zip already exists.
# Run this BEFORE remove_data_dirs.sh.

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

for entity_dir in "$TARGET"/*/; do
    [[ -d "$entity_dir" ]] || continue

    folder_name=$(basename "$entity_dir")
    zip_file="${TARGET}/${folder_name}.zip"

    echo ">>> Processing: $folder_name"

    if [[ -f "$zip_file" ]]; then
        echo "    Skip: $(basename "$zip_file") already exists."
        ((skipped++))
        echo "---"
        continue
    fi

    file_count=$(find "$entity_dir" -type f | wc -l | tr -d ' ')
    dir_size=$(du -sh "$entity_dir" | awk '{print $1}')
    echo "    Zipping $file_count files ($dir_size)..."

    # ditto -c -k: create zip from directory contents (files at root, no parent wrapper)
    if ditto -c -k "$entity_dir" "$zip_file"; then
        zip_size=$(du -sh "$zip_file" | awk '{print $1}')
        echo "    Done: $dir_size -> $zip_size"
        ((total++))
    else
        echo "    ERROR: Failed to zip $folder_name"
        rm -f "$zip_file"
        ((failed++))
    fi

    echo "---"
done

echo ""
echo "Rezipped: $total  |  Skipped (already exist): $skipped  |  Failed: $failed"
echo ""
if [[ "$failed" -eq 0 ]]; then
    echo "All done. Review the zips, then run remove_data_dirs.sh to free disk space."
else
    echo "WARNING: $failed dir(s) failed. Do not run remove_data_dirs.sh until resolved."
fi
