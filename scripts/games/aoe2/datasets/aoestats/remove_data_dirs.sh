#!/usr/bin/env bash
# Removes entity subdirectories under raw/ ONLY when ALL three guards pass:
#   1. A corresponding <dir>.zip exists beside the directory.
#   2. The zip is non-empty (>0 bytes).
#   3. The file count in the zip matches the file count in the directory.
#
# Covers: matches/ players/ overview/
#
# Run AFTER rezip_data.sh. Any directory that fails a guard is left untouched.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/aoe2/datasets/aoestats/data/raw"

if [[ ! -d "$TARGET" ]]; then
    echo "Error: $TARGET not found."
    exit 1
fi

shopt -s nullglob

removed=0
skipped_no_zip=0
skipped_mismatch=0

for entity_dir in "$TARGET"/*/; do
    [[ -d "$entity_dir" ]] || continue

    folder_name=$(basename "$entity_dir")
    zip_file="${TARGET}/${folder_name}.zip"

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

    # Guard 3: file count in zip must match file count in directory.
    # ditto stores resource fork stubs as ._filename alongside real files.
    # unzip -Z1 lists one filename per line; exclude ._* stubs.
    dir_count=$(find "$entity_dir" -type f | wc -l | tr -d ' ')
    zip_count=$(unzip -Z1 "$zip_file" 2>/dev/null | grep -cv "^\._" || true)

    if [[ "$dir_count" -ne "$zip_count" ]]; then
        echo "    MISMATCH: directory has $dir_count files, zip has $zip_count — directory kept."
        ((skipped_mismatch++))
        echo "---"
        continue
    fi

    dir_size=$(du -sh "$entity_dir" | awk '{print $1}')
    echo "    Verified: $dir_count files match. Removing $dir_size..."

    if rm -rf "$entity_dir"; then
        echo "    Removed."
        ((removed++))
    else
        echo "    ERROR: rm -rf failed for $entity_dir"
        ((skipped_mismatch++))
    fi

    echo "---"
done

echo ""
echo "Removed: $removed  |  Skipped (no zip): $skipped_no_zip  |  Skipped (guard failed): $skipped_mismatch"
