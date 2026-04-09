# Event Data Schema Reference

Generated from Steps 1.9D and 1.9E field inventory results.
Each section lists JSON keys found in `event_data` for that event type,
the dominant key-set variant coverage, and intended Phase 4 usage.

## Tracker Events (`tracker_events_raw`)

### PlayerSetup

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (7 total): `evtTypeName`, `id`, `loop`, `playerId`, `slotId`, `type`, `userId`
- **Phase 4 usage**: TBD

### PlayerStats

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (5 total): `evtTypeName`, `id`, `loop`, `playerId`, `stats`
- **Nested keys**: `stats`
- **Phase 4 usage**: TBD

### UnitBorn

- **Dominant key-set coverage**: 93.8%
- **JSON keys** (16 total): `controlPlayerId`, `creatorAbilityName`, `creatorAbilityName`, `creatorUnitTagIndex`, `creatorUnitTagIndex`, `creatorUnitTagRecycle`, `creatorUnitTagRecycle`, `evtTypeName`, `id`, `loop`, `unitTagIndex`, `unitTagRecycle`, `unitTypeName`, `upkeepPlayerId`, `x`, `y`
- **Phase 4 usage**: TBD

### UnitDied

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (13 total): `evtTypeName`, `id`, `killerPlayerId`, `killerPlayerId`, `killerUnitTagIndex`, `killerUnitTagIndex`, `killerUnitTagRecycle`, `killerUnitTagRecycle`, `loop`, `unitTagIndex`, `unitTagRecycle`, `x`, `y`
- **Phase 4 usage**: TBD

### UnitDone

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (5 total): `evtTypeName`, `id`, `loop`, `unitTagIndex`, `unitTagRecycle`
- **Phase 4 usage**: TBD

### UnitInit

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (10 total): `controlPlayerId`, `evtTypeName`, `id`, `loop`, `unitTagIndex`, `unitTagRecycle`, `unitTypeName`, `upkeepPlayerId`, `x`, `y`
- **Phase 4 usage**: TBD

### UnitOwnerChange

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (7 total): `controlPlayerId`, `evtTypeName`, `id`, `loop`, `unitTagIndex`, `unitTagRecycle`, `upkeepPlayerId`
- **Phase 4 usage**: TBD

### UnitPositions

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (5 total): `evtTypeName`, `firstUnitIndex`, `id`, `items`, `loop`
- **Nested keys**: `items`
- **Phase 4 usage**: TBD

### UnitTypeChange

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (6 total): `evtTypeName`, `id`, `loop`, `unitTagIndex`, `unitTagRecycle`, `unitTypeName`
- **Phase 4 usage**: TBD

### Upgrade

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (6 total): `count`, `evtTypeName`, `id`, `loop`, `playerId`, `upgradeTypeName`
- **Phase 4 usage**: TBD

## High-Value Game Events (`game_events_raw`)

### Cmd

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (19 total): `abil`, `abil`, `abil.abilCmdData`, `abil.abilCmdIndex`, `abil.abilLink`, `cmdFlags`, `data`, `data.Data`, `data.None`, `data.TargetPoint`, `data.TargetUnit`, `data.snapshotPoint`, `evtTypeName`, `id`, `loop`, `otherUnit`, `sequence`, `unitGroup`, `userid`
- **Nested keys**: `abil`, `cmdFlags`, `data`, `userid`
- **Phase 4 usage**: TBD

### CmdUpdateTargetPoint

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (5 total): `evtTypeName`, `id`, `loop`, `target`, `userid`
- **Nested keys**: `target`, `userid`
- **Phase 4 usage**: TBD

### CmdUpdateTargetUnit

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (5 total): `evtTypeName`, `id`, `loop`, `target`, `userid`
- **Nested keys**: `target`, `userid`
- **Phase 4 usage**: TBD

### ControlGroupUpdate

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (7 total): `controlGroupIndex`, `controlGroupUpdate`, `evtTypeName`, `id`, `loop`, `mask`, `userid`
- **Nested keys**: `mask`, `userid`
- **Phase 4 usage**: TBD

### SelectionDelta

- **Dominant key-set coverage**: 100.0%
- **JSON keys** (10 total): `controlGroupId`, `delta`, `delta.addSubgroups`, `delta.addUnitTags`, `delta.removeMask`, `delta.subgroupIndex`, `evtTypeName`, `id`, `loop`, `userid`
- **Nested keys**: `delta`, `userid`
- **Phase 4 usage**: TBD
