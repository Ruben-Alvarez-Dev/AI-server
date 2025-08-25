# Memory-Server Activity Tracker for VSCode

A VSCode extension that automatically tracks your development activities and integrates them with Memory-Server for intelligent code assistance and insights.

## Features

- 🔄 **Automatic Activity Tracking**: Captures your coding activities, file operations, debug sessions, and more
- 🏷️ **Intelligent Auto-Tagging**: Automatically tags activities based on content, language, and patterns
- 📁 **Workspace Organization**: Organizes activities into logical workspaces (code, research, projects, personal)
- 🌐 **Offline Support**: Stores data offline when Memory-Server is unavailable and syncs when reconnected
- 📊 **Activity Insights**: Generates comprehensive activity summaries and reports
- 🔒 **Privacy-Focused**: Configurable content redaction for sensitive information

## What Gets Tracked

- File operations (open, edit, close, save)
- Text selections and cursor movements
- Active editor changes
- Debug session starts/stops
- Terminal activity (optional)
- Git commits and changes
- Extension installations/removals
- Configuration changes

## Quick Setup

1. **Install the Extension**
   ```bash
   # Clone the repository
   git clone <repository-url>
   cd vscode-memory-server-activity
   
   # Install dependencies
   npm install
   
   # Compile TypeScript
   npm run compile
   ```

2. **Configure Memory-Server**
   - Make sure Memory-Server is running on `http://localhost:8001`
   - Or update the API URL in settings: `memoryServerActivity.apiUrl`

3. **Set Your Workspace**
   - Use Command Palette: `Memory-Server: Switch Workspace`
   - Or configure in settings: `memoryServerActivity.workspace`

4. **Start Coding!**
   - The extension automatically starts tracking your activities
   - View real-time status in the sidebar panel

## Configuration

### Basic Settings

```json
{
  "memoryServerActivity.enabled": true,
  "memoryServerActivity.workspace": "code",
  "memoryServerActivity.apiUrl": "http://localhost:8001/api/v1/documents/activity",
  "memoryServerActivity.autoTag": true
}
```

### Advanced Settings

```json
{
  "memoryServerActivity.maxFileSizeBytes": 1048576,
  "memoryServerActivity.captureTerminalCommands": false,
  "memoryServerActivity.flushInterval": 5000,
  "memoryServerActivity.excludedPatterns": [
    "node_modules",
    ".git",
    "*.log",
    "*.tmp"
  ],
  "memoryServerActivity.redactPatterns": [
    "API_KEY",
    "PRIVATE_KEY", 
    "PASSWORD",
    "SECRET",
    "TOKEN"
  ]
}
```

## Workspaces

The extension organizes activities into four main workspaces:

- **🔧 Code**: Development activities, coding sessions, debugging
- **📚 Research**: Documentation reading, learning materials, tutorials  
- **📋 Projects**: Project planning, management, architecture discussions
- **📝 Personal**: Personal notes, ideas, experimental code

Switch workspaces using:
- Command Palette: `Memory-Server: Switch Workspace`
- Sidebar: Click on workspace items
- Settings: Update `memoryServerActivity.workspace`

## Commands

| Command | Description |
|---------|-------------|
| `Memory-Server: Toggle Activity Capture` | Pause/resume activity tracking |
| `Memory-Server: Switch Workspace` | Change active workspace |
| `Memory-Server: Generate Activity Summary` | Create detailed activity report |
| `Memory-Server: Open Settings` | Open extension settings |
| `Memory-Server: View Status` | Show current status |
| `Memory-Server: Clear Offline Data` | Remove cached offline data |

## Activity Sidebar Panel

The sidebar panel provides real-time information:

- **Status**: Capture state, API connectivity, buffer size
- **Workspace**: Current workspace and available options
- **Configuration**: Current settings overview  
- **Recent Activity**: Last 5 tracked events
- **Activity Summary**: Generate detailed reports
- **Offline Data**: Manage cached data

## Privacy & Security

### Data Protection
- Sensitive patterns are automatically redacted
- Configurable redaction patterns via settings
- No personal data sent without explicit consent
- All data stays within your Memory-Server instance

### What's Not Tracked
- Actual file contents (only metadata and structure)
- Sensitive environment variables (automatically redacted)
- Private keys or authentication tokens
- Personal information outside development context

### Offline Storage
- Data cached locally when Memory-Server unavailable
- Automatically synced when connection restored
- Can be manually cleared via command palette

## Integration with Memory-Server

Activities are processed by Memory-Server as structured documents:

1. **Intelligent Processing**: Events are analyzed and converted to readable reports
2. **Auto-Tagging**: Content is automatically tagged based on:
   - Programming languages used
   - Activity types (coding, debugging, research)
   - File types and frameworks detected
   - Time patterns and session contexts

3. **Searchable Storage**: All activities become searchable within Memory-Server
4. **Contextual Assistance**: Memory-Server uses activity data to provide better:
   - Code completion suggestions
   - Relevant documentation
   - Pattern recognition
   - Productivity insights

## Troubleshooting

### Extension Not Tracking
1. Check if extension is enabled: `memoryServerActivity.enabled`
2. Verify Memory-Server is running on correct URL
3. Check VSCode output panel for errors
4. Ensure workspace has valid permissions

### Connection Issues  
1. Verify Memory-Server API URL in settings
2. Check network connectivity
3. Review Memory-Server logs for errors
4. Try clearing offline data and restarting

### Performance Issues
1. Reduce flush interval: `memoryServerActivity.flushInterval`
2. Add more exclusion patterns for large directories
3. Disable terminal capture if not needed
4. Check Memory-Server resource usage

## Development

### Building from Source

```bash
# Clone repository
git clone <repository-url>
cd vscode-memory-server-activity

# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch for changes during development
npm run watch
```

### Testing

```bash
# Install extension in development mode
code --install-extension vscode-memory-server-activity-1.0.0.vsix

# Or use F5 in VSCode to launch extension development host
```

## Memory-Server Integration

This extension is designed to work seamlessly with Memory-Server's advanced RAG capabilities:

- **LazyGraphRAG**: Activity patterns contribute to knowledge graph construction
- **Late Chunking**: Development sessions are intelligently chunked for optimal retrieval  
- **Hybrid Search**: Activities are searchable via both semantic and graph-based methods
- **Agentic RAG**: Activity context enhances multi-turn reasoning capabilities

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs via GitHub Issues
- **Documentation**: Full docs at Memory-Server repository
- **Community**: Join our Discord/Slack community

---

**Memory-Server Activity Tracker** - Intelligent development activity tracking for enhanced coding assistance.