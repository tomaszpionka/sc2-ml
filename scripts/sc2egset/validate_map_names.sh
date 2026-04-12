#!/usr/bin/env bash
# Validates that map_foreign_to_english_mapping.json files across all tournament
# directories are consistent (same hash). Reports any diverging versions.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BASE_DIR="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"
TARGET_NAME="map_foreign_to_english_mapping.json"

tmp_file="$(mktemp)"
found_any=0

echo "Checking mapping files in $BASE_DIR..."

for dir in "$BASE_DIR"/20*; do
    [[ -d "$dir" ]] || continue

    file="$dir/$TARGET_NAME"

    if [[ ! -f "$file" ]]; then
        echo "MISSING  $dir"
        continue
    fi

    found_any=1

    if command -v jq >/dev/null 2>&1; then
        hash="$(jq -S . "$file" | shasum | awk '{print $1}')"
    else
        hash="$(shasum "$file" | awk '{print $1}')"
    fi

    printf '%s\t%s\n' "$hash" "$dir" >> "$tmp_file"
done

echo

if [[ "$found_any" -eq 0 ]]; then
    echo "No matching subdirectories or mapping files found."
    rm -f "$tmp_file"
    exit 1
fi

unique_hash_count="$(cut -f1 "$tmp_file" | sort | uniq | wc -l | tr -d ' ')"

if [[ "$unique_hash_count" -eq 1 ]]; then
    echo "✅ All mapping files are identical"
else
    echo "❌ Differences found!"
    echo

    sort "$tmp_file" | while IFS=$'\t' read -r hash dir; do
        printf '%s  %s\n' "$hash" "$dir"
    done

    echo
    echo "Grouped summary:"
    cut -f1 "$tmp_file" | sort | uniq | while read -r hash; do
        echo "Hash: $hash"
        awk -F '\t' -v h="$hash" '$1 == h { print "  " $2 }' "$tmp_file"
        echo
    done
fi

rm -f "$tmp_file"
