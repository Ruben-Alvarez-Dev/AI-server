# Version Archive

This directory contains archived versions of the Memory-Server Activity Tracker extension.

## Usage

Old `.vsix` files are automatically moved here when running the version bump script:

```bash
./scripts/version-bump.sh [patch|minor|major]
```

## Installing Archived Versions

To install a specific version:

```bash
code --install-extension versions/memory-server-activity-tracker-X.Y.Z.vsix
```

## Version History

- `memory-server-activity-tracker-1.0.0.vsix` - Initial release
- Future versions will be archived here automatically

## Cleanup

To remove old archived versions:

```bash
# Remove versions older than 30 days
find versions/ -name "*.vsix" -mtime +30 -delete

# Or remove all but the latest 5 versions
ls -t versions/*.vsix | tail -n +6 | xargs rm -f
```