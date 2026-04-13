#!/usr/bin/env bash
# Removes *_data/ subdirectories ONLY when ALL three guards pass:
#   1. A corresponding *_data.zip exists beside the directory.
#   2. The zip is non-empty (>0 bytes).
#   3. The JSON file count in the zip matches the JSON file count in the directory.
#
# Run AFTER rezip_data.sh. Any directory that fails a guard is left untouched.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"

if [[ ! -d "$TARGET" ]]; then
    echo "Error: $TARGET not found."
    exit 1
fi

shopt -s nullglob

removed=0
skipped_no_zip=0
skipped_mismatch=0

for data_dir in "$TARGET"/20*/*_data; do
    [[ -d "$data_dir" ]] || continue

    parent_dir=$(dirname "$data_dir")
    folder_name=$(basename "$data_dir")
    zip_file="${parent_dir}/${folder_name}.zip"

    echo ">>> Checking: $folder_name"

    # Guard 1: zip must exist
    if [[ ! -f "$zip_file" ]]; then
        echo "    SKIP: no zip found at $(basename "$zip_file") — directory kept."
        ((skipped_no_zip++))
        echo "---"
        continue
    fi

    # Guard 2: zip must be non-empty
    zip_bytes=$(wc -c < "$zip_file" | tr -d ' ')
    if [[ "$zip_bytes" -eq 0 ]]; then
        echo "    SKIP: zip is 0 bytes — directory kept."
        ((skipped_mismatch++))
        echo "---"
        continue
    fi

    # Guard 3: JSON count in zip must match JSON count in directory.
    # ditto stores resource fork stubs as ._filename.json alongside real files.
    # unzip -Z1 lists one filename per line; filter to .json and exclude ._* stubs.
    dir_count=$(find "$data_dir" -type f -name "*.json" | wc -l | tr -d ' ')
    zip_count=$(unzip -Z1 "$zip_file" 2>/dev/null | grep "\.json$" | grep -cv "^\._" || true)

    if [[ "$dir_count" -ne "$zip_count" ]]; then
        echo "    MISMATCH: directory has $dir_count JSON files, zip has $zip_count — directory kept."
        ((skipped_mismatch++))
        echo "---"
        continue
    fi

    dir_size=$(du -sh "$data_dir" | awk '{print $1}')
    echo "    Verified: $dir_count JSON files match. Removing $dir_size..."

    if rm -rf "$data_dir"; then
        echo "    Removed."
        ((removed++))
    else
        echo "    ERROR: rm -rf failed for $data_dir"
        ((skipped_mismatch++))
    fi

    echo "---"
done

echo ""
echo "Removed: $removed  |  Skipped (no zip): $skipped_no_zip  |  Skipped (guard failed): $skipped_mismatch"
