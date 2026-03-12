# Cleanup and Commit Plan

## Files to Delete
1. `.pyre_configuration` - Remove Pyre config (not used)
2. `docs/toon_migration_plan.md` - Remove completed migration plan

## Documentation Updates Needed
1. `docs/current/STRUCTURE.md` - Update directory structure to reflect current state
2. Verify all docs are current with new researcher/personalizer services

## Git Operations
1. Stage all deletions and modifications
2. Verify status
3. Commit with message: "refactor: clean up redundant files and update docs"
4. Push to remote

## Current Git Status
- Many files modified (TOON migration, new services)
- Several files already staged for deletion
- New files: researcher.py, personalizer.py

## Steps
1. Remove .pyre_configuration
2. Remove docs/toon_migration_plan.md
3. Stage all changes
4. Commit
5. Push
