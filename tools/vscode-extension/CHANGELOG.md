# Changelog

All notable changes to the Memory-Server Activity Tracker extension will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 

### Changed
- 

### Fixed
- 

## [1.1.2] - 2025-08-26

### Fixed
- **CRITICAL: Activity summaries now work properly** - Fixed eventsBuffer being cleared before summary generation
- **Buffer synchronization issue** - Implemented separate `eventsSummaryBuffer` that persists events for summary generation
- **"No activity to summarize" error** - Summary commands now access persistent event data instead of cleared buffer

### Technical Changes
- Added `eventsSummaryBuffer` to maintain last 500 events for summary generation
- Modified `enqueueEvent()` to populate both buffers (sending buffer + summary buffer)
- All summary functions now use `eventsSummaryBuffer` instead of cleared `eventsBuffer`
- Enhanced debug logging to show both buffer states

## [1.1.0] - 2025-08-26

### Added
- **Multi-terminal capture support**: Now captures commands from ALL VSCode terminals, not just the first one
- Enhanced Shell Integration API tracking with proper terminal lifecycle management
- Comprehensive terminal event logging (open, close, command start/end, output)

### Changed
- **Simplified workspace model**: Single ingest workspace (`code`) + multiple query-only workspaces (`research`, `projects`)
- Updated UI to show workspace status with emoji indicators: 🎯 ingest, 📖 query-only, ⭕ inactive
- Improved terminal capture initialization with proper Shell Integration readiness detection
- Removed duplicate terminal event listeners

### Fixed
- Multi-terminal capture issue where only first terminal was tracked
- Workspace configuration synchronization between UI and settings
- Shell Integration event handling for new terminals created after extension load

### Technical Details
- Enhanced `initializeTerminalCapture()` function with `trackTerminalShellIntegration()`
- Added `onDidChangeTerminalShellIntegration` listener for proper Shell Integration lifecycle
- Payload now includes `query_workspaces` and `workspace_model: 'ingest-only'` metadata
- Consolidated terminal open/close tracking with Shell Integration setup

## [1.0.0] - 2025-08-25

### Added
- Initial release of Memory-Server Activity Tracker
- Basic terminal command capture using VSCode Shell Integration API
- Activity monitoring with real-time WebView display
- Multi-workspace support (code, research, projects, personal, experimental, learning)
- Offline data storage and synchronization
- Auto-tagging based on file types and activity patterns
- Privacy-focused content redaction
- Activity summary generation
- Terminal-style live activity monitor

### Features
- File operations tracking (open, edit, save, close)
- Terminal command execution monitoring
- Debug session tracking
- Git repository changes monitoring
- Extension installation/removal tracking
- Configurable content filtering and redaction

### Configuration
- Customizable API endpoints
- Workspace management
- File size limits and exclusion patterns
- Redaction patterns for sensitive data
- Flush interval settings

## [1.1.1] - 2025-08-26

### Added
- **Enhanced Activity Summary**: Interactive menu with 4 summary types (Complete, Terminal, File, Recent)
- **Comprehensive terminal command details** in activity summaries with success rates and execution stats
- **Recent terminal activity timeline** showing exact commands with timestamps and exit codes
- Debug logging for investigating summary buffer issues

### Changed
- **Summary generation**: Now offers 100 events for complete summary (vs 50 previously)
- **Terminal summary**: Focused view with last 30 terminal commands and detailed statistics
- **File summary**: Dedicated view for last 50 file operations

### Fixed
- **Summary command selection**: Interactive picker for different summary types and time ranges
- **Terminal command visibility**: Commands now properly displayed in comprehensive summaries

### Debug
- Added temporary console logging to investigate eventsBuffer vs activity monitor disconnect
- Enhanced event tracking debugging for troubleshooting summary generation issues

## [1.1.2] - 2025-08-26

### Planned
- Fix eventsBuffer synchronization issues with activity monitor
- Remove debug logging after buffer issues are resolved
- Better error handling for network failures
- Performance optimizations for large repositories
- Enhanced activity categorization
- Integration with more Memory-Server RAG features