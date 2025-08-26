#!/bin/bash
# Version Bump and Build Script for VSCode Extension
# Usage: ./scripts/version-bump.sh [patch|minor|major]

set -e

# Default to patch if no argument provided
VERSION_TYPE=${1:-patch}

# Validate version type
if [[ ! "$VERSION_TYPE" =~ ^(patch|minor|major)$ ]]; then
    echo "❌ Invalid version type. Use: patch, minor, or major"
    exit 1
fi

echo "🔄 Starting $VERSION_TYPE version bump..."

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "📋 Current version: $CURRENT_VERSION"

# Bump version using npm
npm version $VERSION_TYPE --no-git-tag-version

# Get new version
NEW_VERSION=$(node -p "require('./package.json').version")
echo "🆕 New version: $NEW_VERSION"

# Update changelog with new version entry
TODAY=$(date '+%Y-%m-%d')
echo "📝 Updating CHANGELOG.md..."

# Create temp file for changelog update
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to the Memory-Server Activity Tracker extension will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "## [Unreleased]"
    echo ""
    echo "### Added"
    echo "- "
    echo ""
    echo "### Changed"
    echo "- "
    echo ""
    echo "### Fixed"
    echo "- "
    echo ""
    # Add the rest of the changelog after the unreleased section
    tail -n +8 CHANGELOG.md | sed "s/## \[Unreleased\]/## [$NEW_VERSION] - $TODAY/"
} > CHANGELOG.tmp && mv CHANGELOG.tmp CHANGELOG.md

echo "✅ Changelog updated with version $NEW_VERSION"

# Compile TypeScript
echo "🔨 Compiling TypeScript..."
npm run compile

# Package extension
echo "📦 Packaging extension..."
vsce package --no-yarn

# Find the generated .vsix file
VSIX_FILE="memory-server-activity-tracker-$NEW_VERSION.vsix"

if [ ! -f "$VSIX_FILE" ]; then
    echo "❌ Failed to create extension package: $VSIX_FILE"
    exit 1
fi

echo "✅ Extension packaged: $VSIX_FILE"

# Archive previous versions
ARCHIVE_DIR="versions"
mkdir -p "$ARCHIVE_DIR"

# Move old .vsix files to archive
for file in memory-server-activity-tracker-*.vsix; do
    if [ "$file" != "$VSIX_FILE" ] && [ -f "$file" ]; then
        echo "📁 Archiving old version: $file"
        mv "$file" "$ARCHIVE_DIR/"
    fi
done

echo ""
echo "🎉 Version bump complete!"
echo "   Version: $CURRENT_VERSION → $NEW_VERSION"
echo "   Package: $VSIX_FILE"
echo "   Archive: Previous versions moved to $ARCHIVE_DIR/"
echo ""
echo "📋 Next steps:"
echo "   1. Review CHANGELOG.md and add specific changes"
echo "   2. Test the new version"
echo "   3. Install with: code --install-extension $VSIX_FILE"
echo "   4. Commit changes: git add . && git commit -m 'v$NEW_VERSION'"
echo "   5. Tag release: git tag v$NEW_VERSION"