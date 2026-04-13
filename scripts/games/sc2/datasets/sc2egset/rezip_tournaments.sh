#!/usr/bin/env bash
# Re-zips each tournament subdirectory back into a <tournament>.zip file at the
# raw/ level. Uses ditto (macOS native), consistent with rezip_data.sh.
# Files land at zip root (no --keepParent).
#
# IMPORTANT: Run AFTER rezip_data.sh AND remove_data_dirs.sh.
# The inner *_data/ directories must be gone before this step — zipping a
# tournament dir that still contains *_data/ defeats the purpose.
#
# Safe to re-run: skips any tournament where <tournament>.zip already exists.
# Run this BEFORE remove_tournament_dirs.sh.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"

if [[ ! -d "$TARGET" ]]; then
    echo "Error: $TARGET not found."
    exit 1
fi

shopt -s nullglob

total=0
skipped=0
failed=0

for tournament_dir in "$TARGET"/20*; do
    [[ -d "$tournament_dir" ]] || continue

    folder_name=$(basename "$tournament_dir")
    zip_file="${TARGET}/${folder_name}.zip"

    echo ">>> Processing: $folder_name"

    if [[ -f "$zip_file" ]]; then
        echo "    Skip: $(basename "$zip_file") already exists."
        ((skipped++))
        echo "---"
        continue
    fi

    file_count=$(find "$tournament_dir" -type f | wc -l | tr -d ' ')
    dir_size=$(du -sh "$tournament_dir" | awk '{print $1}')
    echo "    Zipping $file_count files ($dir_size)..."

    # ditto -c -k: create zip from directory contents (files at root, no parent wrapper)
    if ditto -c -k "$tournament_dir" "$zip_file"; then
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
    echo "All done. Review the zips, then run remove_tournament_dirs.sh to free disk space."
else
    echo "WARNING: $failed tournament(s) failed. Do not run remove_tournament_dirs.sh until resolved."
fi
