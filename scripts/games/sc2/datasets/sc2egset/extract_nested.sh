#!/bin/bash
# Extracts nested *_data.zip files found inside each tournament subdirectory.
# Run after unpack.sh.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
TARGET="$REPO_ROOT/src/rts_predict/games/sc2/datasets/sc2egset/data/raw"

# Check if directory exists
if [ ! -d "$TARGET" ]; then
    echo "Error: $TARGET not found."
    exit 1
fi

# Use globstar to find all _data.zip files nested inside subfolders
shopt -s globstar

# Loop through every _data.zip found inside the subdirectories
for nested_zip in "$TARGET"/**/*_data.zip; do

    # Get the directory where the zip is located
    parent_dir=$(dirname "$nested_zip")
    # Get the filename without the .zip extension for the new folder
    folder_name=$(basename "$nested_zip" .zip)
    extract_to="$parent_dir/$folder_name"

    echo ">>> Found: $(basename "$nested_zip")"
    echo "    Extracting to: $extract_to"

    # Create the specific subfolder for this data
    mkdir -p "$extract_to"

    # Use ditto for reliable extraction on macOS
    if ditto -x -k "$nested_zip" "$extract_to"; then
        echo "    Successfully unpacked."
        # Optional: Remove the nested zip after successful extraction
        # rm "$nested_zip"
        # echo "    Removed nested zip."
    else
        echo "    FAILED to unpack $(basename "$nested_zip")"
    fi

    echo "---"
done

echo "All nested extractions complete!"
