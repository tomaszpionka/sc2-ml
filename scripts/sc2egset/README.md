# SC2EGSet — Data Management Scripts

Operational shell scripts for managing the SC2EGSet raw replay corpus.
All scripts self-locate relative to the repo root via `BASH_SOURCE[0]` — safe to run from any CWD.

## Workflow order

### Initial download processing
```
unpack.sh            # Extract tournament ZIPs from ~/Downloads/ into raw/
extract_nested.sh    # Extract *_data.zip files within each tournament dir
nested_zip_remove.sh # Remove *_data.zip files after successful extraction
```

### Disk space reclaim (optional, reversible)
```
rezip_data.sh        # Re-zip *_data/ dirs back to *_data.zip (run first)
remove_data_dirs.sh  # Remove *_data/ dirs after verified re-zipping
```

### Validation
```
validate_map_names.sh  # Check consistency of map translation files across tournaments
```

## Requirements

- macOS (`ditto` for zip operations)
- `jq` (optional, improves map validation hash accuracy)
