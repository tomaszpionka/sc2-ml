#!/bin/bash
# Removes nested *_data.zip files after successful extraction.
# Run after extract_nested.sh.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"

# Check if directory exists
if [ ! -d "$TARGET" ]; then
    echo "Error: $TARGET not found."
    exit 1
fi

# Use globstar to find all _data.zip files nested inside subfolders
shopt -s globstar

total_size=0
# Loop through every _data.zip found inside the subdirectories
for nested_zip in "$TARGET"/**/*_data.zip; do

    # Get the directory where the zip is located
    parent_dir=$(dirname "$nested_zip")
    # Get the filename without the .zip extension for the new folder
    folder_name=$(basename "$nested_zip" .zip)

    echo ">>> Found: $(basename "$nested_zip")"
    echo ">>> Size: $(du -sh "$nested_zip")"
    echo "    Removing: $nested_zip"
    rm "$nested_zip" && echo "    Successfully removed." || echo "    FAILED to remove $(basename "$nested_zip")"
    echo "---"
done

echo "All nested zip removals complete!"
