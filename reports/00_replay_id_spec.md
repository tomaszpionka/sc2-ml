# replay_id Specification

## Definition

`replay_id` is the 32-character MD5 hex prefix extracted from the replay filename.

## Extraction

**SQL:**
```sql
regexp_extract(filename, '([0-9a-f]{32})\.SC2Replay\.json$', 1)
```

**Python:**
```python
re.search(r'([0-9a-f]{32})\.SC2Replay\.json$', path).group(1)
```

## Worked Examples

### 8c9c6c59cda973687e698f67950ce7db.SC2Replay.json
- Absolute path ID: `8c9c6c59cda973687e698f67950ce7db`
- Relative path ID: `8c9c6c59cda973687e698f67950ce7db`
- Match: YES

### 905a46ae041a82d4d5e4fbac12a9936a.SC2Replay.json
- Absolute path ID: `905a46ae041a82d4d5e4fbac12a9936a`
- Relative path ID: `905a46ae041a82d4d5e4fbac12a9936a`
- Match: YES

### 2511679ed48f0f35d5542319ee8d5b7b.SC2Replay.json
- Absolute path ID: `2511679ed48f0f35d5542319ee8d5b7b`
- Relative path ID: `2511679ed48f0f35d5542319ee8d5b7b`
- Match: YES
