// VS Code extensibility API
import * as vscode from 'vscode';
import * as https from 'https';
import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';

// Default Memory-Server API endpoint
const DEFAULT_MEMORY_SERVER_API_URL = 'http://localhost:8001/api/v1/documents/activity';

// Available workspaces (synchronized with package.json)
const AVAILABLE_WORKSPACES = ['code', 'research', 'projects', 'personal', 'experimental', 'learning'];

// In-memory buffer and state
let eventsBuffer: any[] = [];
let eventsSummaryBuffer: any[] = []; // Keep events for summaries
let flushing = false;
let flushIntervalHandle: NodeJS.Timeout | undefined;
let lastGitHead: string | undefined;
let isShuttingDown = false;
let activityTreeProvider: MemoryServerActivityTreeProvider;
let activityMonitorProvider: ActivityMonitorProvider;
let isCapturing = true;

// Get workspace configuration dynamically
function getIngestWorkspace(): string {
	const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
	return cfg.get('ingestWorkspace', 'code') as string;
}

function getQueryWorkspaces(): string[] {
	const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
	return cfg.get('queryWorkspaces', ['research', 'projects']) as string[];
}

// Tree Data Provider for the sidebar panel
class MemoryServerActivityTreeProvider implements vscode.TreeDataProvider<ActivityItem> {
	private _onDidChangeTreeData: vscode.EventEmitter<ActivityItem | undefined | null | void> = new vscode.EventEmitter<ActivityItem | undefined | null | void>();
	readonly onDidChangeTreeData: vscode.Event<ActivityItem | undefined | null | void> = this._onDidChangeTreeData.event;

	refresh(): void {
		this._onDidChangeTreeData.fire();
	}

	getTreeItem(element: ActivityItem): vscode.TreeItem {
		return element;
	}

	getChildren(element?: ActivityItem): Thenable<ActivityItem[]> {
		if (!element) {
			// Root level items
			return Promise.resolve([
				new ActivityItem('Status', vscode.TreeItemCollapsibleState.Expanded, 'status'),
				new ActivityItem('Workspace', vscode.TreeItemCollapsibleState.Expanded, 'workspace'),
				new ActivityItem('Configuration', vscode.TreeItemCollapsibleState.Expanded, 'config'),
				new ActivityItem('Terminal Commands', vscode.TreeItemCollapsibleState.Expanded, 'terminalCommands'),
				new ActivityItem('Recent Activity', vscode.TreeItemCollapsibleState.Expanded, 'activity'),
				new ActivityItem('Activity Summary', vscode.TreeItemCollapsibleState.None, 'activitySummary'),
				new ActivityItem('Offline Data', vscode.TreeItemCollapsibleState.Expanded, 'offlineData')
			]);
		} else if (element.contextValue === 'status') {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const apiUrl = cfg.get('apiUrl', DEFAULT_MEMORY_SERVER_API_URL) as string;
			const enabled = cfg.get('enabled', true);
			const autoTag = cfg.get('autoTag', true);
			
			return Promise.resolve([
				new ActivityItem(`Capture: ${isCapturing ? '🟢 Active' : '🔴 Paused'}`, vscode.TreeItemCollapsibleState.None, 'statusItem'),
				new ActivityItem(`Memory-Server: ${apiUrl}`, vscode.TreeItemCollapsibleState.None, 'statusItem'),
				new ActivityItem(`Enabled: ${enabled ? 'Yes' : 'No'}`, vscode.TreeItemCollapsibleState.None, 'statusItem'),
				new ActivityItem(`Auto-Tag: ${autoTag ? 'On' : 'Off'}`, vscode.TreeItemCollapsibleState.None, 'statusItem'),
				new ActivityItem(`Buffer: ${eventsBuffer.length} events`, vscode.TreeItemCollapsibleState.None, 'statusItem')
			]);
		} else if (element.contextValue === 'workspace') {
			const currentIngest = getIngestWorkspace();
			const currentQuery = getQueryWorkspaces();
			
			const workspaceItems = AVAILABLE_WORKSPACES.map(ws => {
				const isIngest = ws === currentIngest;
				const isQuery = currentQuery.includes(ws);
				
				let checkbox = '☐'; // Empty checkbox
				let status = '';
				
				if (isIngest) {
					checkbox = '✅'; // Checked - ingest
					status = ' ingest';
				} else if (isQuery) {
					checkbox = '☑️'; // Checked - query only  
					status = ' query-only';
				}
				
				return new ActivityItem(
					`${checkbox} ${ws.charAt(0).toUpperCase() + ws.slice(1)}${status}`,
					vscode.TreeItemCollapsibleState.None,
					'workspaceItem',
					{
						command: 'memoryServerActivity.switchWorkspace',
						title: `Configure ${ws} workspace`,
						arguments: [ws]
					}
				);
			});
			
			return Promise.resolve(workspaceItems);
		} else if (element.contextValue === 'config') {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			return Promise.resolve([
				new ActivityItem(`Max File Size: ${cfg.get('maxFileSizeMB', 1)} MB`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Terminal Capture: ${cfg.get('captureTerminalCommands', true) ? 'On' : 'Off'}`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Excluded Patterns: ${(cfg.get('excludedPatterns', []) as string[]).length} items`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Flush Interval: ${cfg.get('flushInterval', 5000)}ms`, vscode.TreeItemCollapsibleState.None, 'configItem')
			]);
		} else if (element.contextValue === 'terminalCommands') {
			const terminalEvents = eventsBuffer.filter(event => 
				event.type === 'terminalCommandStart' || 
				event.type === 'terminalCommandEnd' ||
				event.type === 'terminalOutput'
			).slice(-10).reverse();
			
			const groupedCommands = new Map<string, any>();
			
			terminalEvents.forEach(event => {
				if (event.type === 'terminalCommandStart') {
					groupedCommands.set(event.executionId, {
						...event,
						output: '',
						exitCode: null,
						completed: false
					});
				} else if (event.type === 'terminalOutput' && groupedCommands.has(event.executionId)) {
					const cmd = groupedCommands.get(event.executionId)!;
					cmd.output += event.output;
				} else if (event.type === 'terminalCommandEnd' && groupedCommands.has(event.executionId)) {
					const cmd = groupedCommands.get(event.executionId)!;
					cmd.exitCode = event.exitCode;
					cmd.completed = true;
				}
			});
			
			const commands = Array.from(groupedCommands.values()).slice(-5);
			return Promise.resolve(commands.map(cmd => {
				const status = cmd.completed ? (cmd.exitCode === 0 ? '✅' : '❌') : '⏳';
				const shortCommand = cmd.commandLine.length > 30 ? 
					cmd.commandLine.substring(0, 30) + '...' : cmd.commandLine;
				
				return new ActivityItem(
					`${status} ${shortCommand}`,
					vscode.TreeItemCollapsibleState.None,
					'terminalCommand',
					{
						command: 'memoryServerActivity.showTerminalDetails',
						title: 'Show Terminal Details',
						arguments: [cmd]
					}
				);
			}));
		} else if (element.contextValue === 'activity') {
			const recentEvents = eventsBuffer.slice(-5).reverse();
			return Promise.resolve(recentEvents.map(event => 
				new ActivityItem(`${event.type} - ${new Date(event.timestamp).toLocaleTimeString()}`, vscode.TreeItemCollapsibleState.None, 'activityItem')
			));
		} else if (element.contextValue === 'offlineData') {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const offlinePath = cfg.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
			
			let offlineCount = 0;
			let lastOfflineEvent = '';
			
			try {
				if (fs.existsSync(offlinePath)) {
					const content = fs.readFileSync(offlinePath, 'utf8').trim();
					if (content) {
						const lines = content.split('\n').filter(Boolean);
						offlineCount = lines.length;
						if (lines.length > 0) {
							try {
								const lastEvent = JSON.parse(lines[lines.length - 1]);
								lastOfflineEvent = new Date(lastEvent.timestamp).toLocaleString();
							} catch {
								lastOfflineEvent = 'Invalid data';
							}
						}
					}
				}
			} catch (error) {
				lastOfflineEvent = 'Error reading file';
			}
			
			return Promise.resolve([
				new ActivityItem(`📊 Events stored: ${offlineCount}`, vscode.TreeItemCollapsibleState.None, 'offlineItem'),
				new ActivityItem(`📅 Last event: ${lastOfflineEvent || 'None'}`, vscode.TreeItemCollapsibleState.None, 'offlineItem'),
				new ActivityItem(`📁 File: ${offlinePath}`, vscode.TreeItemCollapsibleState.None, 'offlineItem')
			]);
		}
		return Promise.resolve([]);
	}
}

class ActivityItem extends vscode.TreeItem {
	constructor(
		public readonly label: string,
		public readonly collapsibleState: vscode.TreeItemCollapsibleState,
		public readonly contextValue: string,
		public readonly command?: vscode.Command
	) {
		super(label, collapsibleState);
		this.tooltip = this.label;
		
		// Set icons based on context
		switch (contextValue) {
			case 'status':
				this.iconPath = new vscode.ThemeIcon('pulse');
				break;
			case 'workspace':
				this.iconPath = new vscode.ThemeIcon('folder-library');
				break;
			case 'config':
				this.iconPath = new vscode.ThemeIcon('settings-gear');
				break;
			case 'terminalCommands':
				this.iconPath = new vscode.ThemeIcon('terminal');
				break;
			case 'terminalCommand':
				this.iconPath = new vscode.ThemeIcon('console');
				break;
			case 'activity':
				this.iconPath = new vscode.ThemeIcon('history');
				break;
			case 'activitySummary':
				this.iconPath = new vscode.ThemeIcon('file-text');
				break;
			case 'offlineData':
				this.iconPath = new vscode.ThemeIcon('database');
				break;
		}
	}
}

// Activity Monitor WebView Provider
class ActivityMonitorProvider implements vscode.WebviewViewProvider {
	public static readonly viewType = 'memoryServerActivityMonitor';
	private _view?: vscode.WebviewView;

	constructor(private readonly _extensionUri: vscode.Uri) {}

	public resolveWebviewView(
		webviewView: vscode.WebviewView,
		context: vscode.WebviewViewResolveContext,
		_token: vscode.CancellationToken,
	) {
		this._view = webviewView;

		webviewView.webview.options = {
			enableScripts: true,
			localResourceRoots: [this._extensionUri]
		};

		webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

		// Listen for messages from the webview
		webviewView.webview.onDidReceiveMessage(
			message => {
				switch (message.command) {
					case 'clear':
						this.clearMonitor();
						break;
				}
			},
			undefined,
			[]
		);
	}

	public addEvent(event: any) {
		if (this._view) {
			const timestamp = new Date(event.timestamp).toLocaleTimeString();
			const eventData = {
				timestamp,
				type: event.type,
				data: this._formatEventData(event)
			};
			
			this._view.webview.postMessage({
				command: 'addEvent',
				event: eventData
			});
		}
	}

	public clearMonitor() {
		if (this._view) {
			this._view.webview.postMessage({ command: 'clear' });
		}
	}

	private _formatEventData(event: any): string {
		switch (event.type) {
			case 'terminalCommandStart':
				return `🔄 ${event.terminalName}: ${event.commandLine}`;
			case 'terminalCommandEnd':
				const status = event.exitCode === 0 ? '✅' : '❌';
				return `${status} ${event.terminalName}: exit ${event.exitCode}`;
			case 'terminalOutput':
				const preview = event.output.length > 50 ? 
					event.output.substring(0, 50) + '...' : event.output;
				return `📝 ${event.terminalName}: ${preview.replace(/\n/g, '↵')}`;
			case 'edit':
				return `✏️  Edited ${event.file ? event.file.split('/').pop() : 'file'} (${event.changes} changes)`;
			case 'openFile':
				return `📂 Opened ${event.file ? event.file.split('/').pop() : 'file'}`;
			case 'commit':
				return `📦 Git: ${event.message}`;
			default:
				return `${event.type}: ${JSON.stringify(event).substring(0, 50)}...`;
		}
	}

	private _getHtmlForWebview(webview: vscode.Webview) {
		return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Activity Monitor</title>
    <style>
        body {
            font-family: var(--vscode-editor-font-family);
            font-size: var(--vscode-editor-font-size);
            background-color: var(--vscode-terminal-background);
            color: var(--vscode-terminal-foreground);
            margin: 0;
            padding: 8px;
            overflow-x: hidden;
        }
        .monitor {
            height: 100vh;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
        }
        .event {
            padding: 2px 0;
            border-bottom: 1px solid var(--vscode-terminal-ansiBlack);
            word-wrap: break-word;
        }
        .timestamp {
            color: var(--vscode-terminal-ansiGreen);
            font-weight: bold;
        }
        .event-type {
            color: var(--vscode-terminal-ansiCyan);
            font-weight: bold;
        }
        .event-data {
            color: var(--vscode-terminal-foreground);
            margin-left: 8px;
        }
        .controls {
            position: fixed;
            bottom: 8px;
            right: 8px;
            opacity: 0.7;
        }
        .controls:hover {
            opacity: 1;
        }
        button {
            background: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            padding: 4px 8px;
            cursor: pointer;
            font-size: 11px;
        }
        button:hover {
            background: var(--vscode-button-hoverBackground);
        }
    </style>
</head>
<body>
    <div class="monitor" id="monitor">
        <div class="event">
            <span class="timestamp">[${new Date().toLocaleTimeString()}]</span>
            <span class="event-type">SYSTEM</span>
            <span class="event-data">🚀 Activity Monitor initialized - Waiting for events...</span>
        </div>
    </div>
    <div class="controls">
        <button onclick="clearMonitor()">Clear</button>
    </div>

    <script>
        const vscode = acquireVsCodeApi();
        const monitor = document.getElementById('monitor');
        let eventCount = 0;

        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
                case 'addEvent':
                    addEventToMonitor(message.event);
                    break;
                case 'clear':
                    clearMonitorView();
                    break;
            }
        });

        function addEventToMonitor(event) {
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event';
            eventDiv.innerHTML = \`
                <span class="timestamp">[\${event.timestamp}]</span>
                <span class="event-type">\${event.type.toUpperCase()}</span>
                <span class="event-data">\${event.data}</span>
            \`;
            
            monitor.appendChild(eventDiv);
            eventCount++;
            
            // Keep only last 100 events for performance
            if (eventCount > 100) {
                monitor.removeChild(monitor.children[1]); // Keep first system message
                eventCount--;
            }
            
            // Auto scroll to bottom
            monitor.scrollTop = monitor.scrollHeight;
        }

        function clearMonitor() {
            vscode.postMessage({ command: 'clear' });
        }

        function clearMonitorView() {
            monitor.innerHTML = \`
                <div class="event">
                    <span class="timestamp">[\${new Date().toLocaleTimeString()}]</span>
                    <span class="event-type">SYSTEM</span>
                    <span class="event-data">🧹 Monitor cleared - Waiting for events...</span>
                </div>
            \`;
            eventCount = 0;
        }
    </script>
</body>
</html>`;
	}
}

/**
 * Activate extension
 */
export function activate(context: vscode.ExtensionContext) {
	// Load config
	const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
	const apiUrl = cfg.get('apiUrl', DEFAULT_MEMORY_SERVER_API_URL) as string;
	const enabled = cfg.get('enabled', true);
	const offlinePath = cfg.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
	const redactPatterns = cfg.get('redactPatterns', ['API_KEY', 'PRIVATE_KEY', 'PASSWORD', 'SECRET', 'TOKEN']) as string[];
	
	// Load workspace configuration
	// Configuration is now read dynamically via getIngestWorkspace() and getQueryWorkspaces()
	// Query workspaces are now read dynamically via getQueryWorkspaces()

	// Ensure offline directory exists
	try {
		const offlineDir = path.dirname(offlinePath);
		if (offlineDir && offlineDir !== '.') {
			fs.mkdirSync(offlineDir, { recursive: true });
		}
	} catch (e) {
		console.warn('Could not create offline directory', e);
	}

	logAction('activate', { apiUrl, enabled, workspace: getIngestWorkspace() });

	// Replay offline events (async, fire-and-forget)
	replayOfflineEvents(offlinePath, redactPatterns).catch(err => {
		console.warn('replayOfflineEvents error', err);
	});

	// Start periodic flush
	const flushInterval = cfg.get('flushInterval', 5000) as number;
	startFlushInterval(flushInterval);

	// Initialize and register tree data provider
	activityTreeProvider = new MemoryServerActivityTreeProvider();
	vscode.window.registerTreeDataProvider('memoryServerActivityView', activityTreeProvider);

	// Initialize and register activity monitor webview provider
	activityMonitorProvider = new ActivityMonitorProvider(context.extensionUri);
	context.subscriptions.push(
		vscode.window.registerWebviewViewProvider(ActivityMonitorProvider.viewType, activityMonitorProvider)
	);

	// Refresh tree view periodically
	setInterval(() => {
		activityTreeProvider.refresh();
	}, 5000);

	// Register configuration change listener
	context.subscriptions.push(
		vscode.workspace.onDidChangeConfiguration(event => {
			if (event.affectsConfiguration('memoryServerActivity')) {
				const newCfg = vscode.workspace.getConfiguration('memoryServerActivity');
				const newIngestWorkspace = newCfg.get('ingestWorkspace', 'code') as string;
				
				enqueueEvent({
					type: 'workspaceConfigChange',
					ingestWorkspace: newIngestWorkspace,
					queryWorkspaces: getQueryWorkspaces(),
					timestamp: Date.now()
				});
				
				enqueueEvent({ 
					type: 'configurationChange', 
					affects: event.affectsConfiguration.name,
					timestamp: Date.now() 
				});
				activityTreeProvider.refresh();
			}
		})
	);

	// Register workspace folder changes
	context.subscriptions.push(
		vscode.workspace.onDidChangeWorkspaceFolders(event => {
			enqueueEvent({ 
				type: 'workspaceFoldersChange', 
				added: event.added.map(f => f.uri.fsPath), 
				removed: event.removed.map(f => f.uri.fsPath), 
				timestamp: Date.now() 
			});
		})
	);

	// Register visible editors change
	context.subscriptions.push(
		vscode.window.onDidChangeVisibleTextEditors(editors => {
			enqueueEvent({ 
				type: 'visibleEditorsChange', 
				editors: editors.map(e => e.document.uri.fsPath), 
				timestamp: Date.now() 
			});
		})
	);

	// Git commit detection on startup
	detectAndRegisterLatestCommit();

	// Register commands
	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.toggleCapture', () => {
			isCapturing = !isCapturing;
			const status = isCapturing ? 'resumed' : 'paused';
			vscode.window.showInformationMessage(`Memory-Server Activity capture ${status}`);
			enqueueEvent({
				type: 'captureToggle',
				status: isCapturing ? 'active' : 'paused',
				timestamp: Date.now()
			});
			activityTreeProvider.refresh();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.openSettings', () => {
			vscode.commands.executeCommand('workbench.action.openSettings', 'memoryServerActivity');
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.switchWorkspace', async (workspace?: string) => {
			if (!workspace) {
				vscode.window.showErrorMessage('No workspace specified');
				return;
			}

			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const currentIngest = getIngestWorkspace();
			const currentQuery = getQueryWorkspaces();
			const isCurrentIngest = workspace === currentIngest;
			const isCurrentQuery = currentQuery.includes(workspace);
			
			// Show options for this workspace
			const options = [
				{
					label: `✅ Make "${workspace}" the ingest workspace`,
					description: 'This workspace will capture all activity data',
					action: 'ingest'
				},
				{
					label: `☑️ Add "${workspace}" as query-only workspace`,
					description: 'This workspace will be available for RAG queries but won\'t capture data',
					action: 'query'
				},
				{
					label: `❌ Remove "${workspace}" from active workspaces`,
					description: 'This workspace will be inactive',
					action: 'remove'
				}
			];
			
			// Filter options based on current state
			const filteredOptions = options.filter(option => {
				if (isCurrentIngest && option.action === 'ingest') return false;
				if (isCurrentQuery && option.action === 'query') return false;
				if (!isCurrentIngest && !isCurrentQuery && option.action === 'remove') return false;
				return true;
			});
			
			const selectedOption = await vscode.window.showQuickPick(filteredOptions, {
				placeHolder: `Configure "${workspace}" workspace`,
				canPickMany: false
			});
			
			if (!selectedOption) return;
			
			if (selectedOption.action === 'ingest') {
				await cfg.update('ingestWorkspace', workspace, vscode.ConfigurationTarget.Global);
				vscode.window.showInformationMessage(`${workspace} is now the ingest workspace`);
			} else if (selectedOption.action === 'query') {
				const newQueryWorkspaces = [...currentQuery];
				if (!newQueryWorkspaces.includes(workspace)) {
					newQueryWorkspaces.push(workspace);
					await cfg.update('queryWorkspaces', newQueryWorkspaces, vscode.ConfigurationTarget.Global);
					vscode.window.showInformationMessage(`${workspace} added as query-only workspace`);
				}
			} else if (selectedOption.action === 'remove') {
				if (isCurrentQuery) {
					const newQueryWorkspaces = currentQuery.filter(w => w !== workspace);
					await cfg.update('queryWorkspaces', newQueryWorkspaces, vscode.ConfigurationTarget.Global);
					vscode.window.showInformationMessage(`${workspace} removed from query workspaces`);
				}
			}
			
			activityTreeProvider.refresh();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.viewStatus', () => {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const apiUrl = cfg.get('apiUrl', DEFAULT_MEMORY_SERVER_API_URL) as string;
			const enabled = cfg.get('enabled', true);
			const bufferSize = eventsBuffer.length;
			
			const statusMessage = `Memory-Server Activity Status:
• Capture: ${isCapturing ? 'Active' : 'Paused'}
• Workspace: ${getIngestWorkspace()}
• API URL: ${apiUrl}
• Enabled: ${enabled ? 'Yes' : 'No'}
• Auto-Tag: ${cfg.get('autoTag', true) ? 'On' : 'Off'}
• Buffer: ${bufferSize} events
• Last Git Head: ${lastGitHead || 'Unknown'}`;

			vscode.window.showInformationMessage(statusMessage, { modal: true });
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.generateSummary', async () => {
			// Show options for different summary types and time ranges
			const options = [
				{
					label: '📊 Complete Activity Summary (last 100 events)',
					description: 'Full summary with terminal commands, file activity, and more',
					action: 'complete',
					count: 100
				},
				{
					label: '💻 Terminal Activity Only (last 30 commands)',
					description: 'Focus on terminal commands and output',
					action: 'terminal',
					count: 30
				},
				{
					label: '📁 File Activity Only (last 50 file events)',
					description: 'Focus on file operations and code editing',
					action: 'files',
					count: 50
				},
				{
					label: '🕐 Recent Activity (last 20 events)',
					description: 'Quick overview of most recent activity',
					action: 'recent',
					count: 20
				}
			];

			const selectedOption = await vscode.window.showQuickPick(options, {
				placeHolder: 'Select summary type',
				canPickMany: false
			});

			if (!selectedOption) return;

			let events: any[] = [];
			let summary: string = '';

			// Debug: Check buffer status
			console.log(`DEBUG: eventsBuffer.length = ${eventsBuffer.length}`);
			console.log(`DEBUG: eventsSummaryBuffer.length = ${eventsSummaryBuffer.length}`);
			console.log(`DEBUG: isCapturing = ${isCapturing}`);
			console.log(`DEBUG: Last 5 events from summaryBuffer:`, eventsSummaryBuffer.slice(-5));
			
			if (selectedOption.action === 'complete') {
				events = eventsSummaryBuffer.slice(-selectedOption.count);
				summary = generateComprehensiveActivitySummary(events);
			} else if (selectedOption.action === 'terminal') {
				events = eventsSummaryBuffer.filter(event => 
					event.type.startsWith('terminal')
				).slice(-selectedOption.count);
				console.log(`DEBUG: Terminal events found: ${events.length}`);
				summary = generateTerminalSummary(events);
			} else if (selectedOption.action === 'files') {
				events = eventsSummaryBuffer.filter(event => 
					['edit', 'openFile', 'closeFile', 'selection', 'activeEditor'].includes(event.type)
				).slice(-selectedOption.count);
				summary = generateFileSummary(events);
			} else {
				events = eventsSummaryBuffer.slice(-selectedOption.count);
				summary = generateActivitySummary(events);
			}

			if (events.length === 0) {
				vscode.window.showInformationMessage(`No ${selectedOption.action} activity to summarize`);
				return;
			}
			
			// Show summary in a new document
			const doc = await vscode.workspace.openTextDocument({
				content: summary,
				language: 'markdown'
			});
			vscode.window.showTextDocument(doc);
			
			enqueueEvent({
				type: 'summaryGenerated',
				eventCount: events.length,
				summaryType: selectedOption.action,
				timestamp: Date.now()
			});
		})
	);

	// Terminal Summary Command
	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.generateTerminalSummary', async () => {
			const terminalEvents = eventsBuffer.filter(event => 
				event.type.startsWith('terminal')
			).slice(-20);
			
			if (terminalEvents.length === 0) {
				vscode.window.showInformationMessage('No terminal activity to summarize');
				return;
			}

			const summary = generateTerminalSummary(terminalEvents);
			const doc = await vscode.workspace.openTextDocument({
				content: summary,
				language: 'markdown'
			});
			vscode.window.showTextDocument(doc);
		})
	);

	// File Activity Summary Command  
	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.generateFileSummary', async () => {
			const fileEvents = eventsBuffer.filter(event => 
				['edit', 'openFile', 'closeFile', 'selection', 'activeEditor'].includes(event.type)
			).slice(-30);
			
			if (fileEvents.length === 0) {
				vscode.window.showInformationMessage('No file activity to summarize');
				return;
			}

			const summary = generateFileSummary(fileEvents);
			const doc = await vscode.workspace.openTextDocument({
				content: summary,
				language: 'markdown'
			});
			vscode.window.showTextDocument(doc);
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.clearOfflineData', async () => {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const offlinePath = cfg.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
			
			try {
				if (fs.existsSync(offlinePath)) {
					fs.writeFileSync(offlinePath, '', 'utf8');
					vscode.window.showInformationMessage('Offline data cleared successfully');
				} else {
					vscode.window.showInformationMessage('No offline data found');
				}
			} catch (error) {
				vscode.window.showErrorMessage(`Failed to clear offline data: ${error}`);
			}
			activityTreeProvider.refresh();
		})
	);

	context.subscriptions.push(
		vscode.commands.registerCommand('memoryServerActivity.showTerminalDetails', async (command: any) => {
			if (!command) {
				vscode.window.showErrorMessage('No command details available');
				return;
			}

			const details = `# Terminal Command Details

**Command:** \`${command.commandLine}\`
**Terminal:** ${command.terminalName}
**Workspace:** ${command.workspace}
**Executed:** ${new Date(command.timestamp).toLocaleString()}
**Status:** ${command.completed ? (command.exitCode === 0 ? 'Success ✅' : `Failed ❌ (exit code: ${command.exitCode})`) : 'Running ⏳'}
${command.cwd ? `**Directory:** ${command.cwd}` : ''}

## Output

\`\`\`
${command.output || 'No output captured yet...'}
\`\`\`

## Execution Details

- **Execution ID:** ${command.executionId}
- **Command Confidence:** ${command.confidence || 'N/A'}
- **Completion Status:** ${command.completed ? 'Completed' : 'In Progress'}
${command.exitCode !== null ? `- **Exit Code:** ${command.exitCode}` : ''}

---
*This data was captured by Memory-Server Activity Tracker using VSCode Shell Integration API*
`;

			const doc = await vscode.workspace.openTextDocument({
				content: details,
				language: 'markdown'
			});
			vscode.window.showTextDocument(doc);
			
			enqueueEvent({
				type: 'terminalDetailsViewed',
				executionId: command.executionId,
				timestamp: Date.now()
			});
		})
	);

	// Document activity listeners
	context.subscriptions.push(
		vscode.workspace.onDidChangeTextDocument(event => {
			if (!isCapturing) return;
			
			enqueueEvent({
				type: 'edit',
				file: event.document.uri.fsPath,
				language: event.document.languageId,
				changes: event.contentChanges.length,
				workspace: getIngestWorkspace(),
				timestamp: Date.now()
			});
		})
	);

	context.subscriptions.push(
		vscode.workspace.onDidOpenTextDocument(doc => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'openFile', 
				file: doc.uri.fsPath,
				language: doc.languageId,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	context.subscriptions.push(
		vscode.workspace.onDidCloseTextDocument(doc => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'closeFile', 
				file: doc.uri.fsPath,
				language: doc.languageId,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	context.subscriptions.push(
		vscode.window.onDidChangeTextEditorSelection(event => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'selection', 
				file: event.textEditor.document.uri.fsPath,
				language: event.textEditor.document.languageId,
				selections: event.selections.length,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	context.subscriptions.push(
		vscode.window.onDidChangeActiveTextEditor(editor => {
			if (!isCapturing || !editor) return;
			
			enqueueEvent({ 
				type: 'activeEditor', 
				file: editor.document.uri.fsPath,
				language: editor.document.languageId,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	// Terminal close listener (open is now handled in initializeTerminalCapture)
	context.subscriptions.push(
		vscode.window.onDidCloseTerminal(terminal => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'closeTerminal', 
				name: terminal.name,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	// Debug session listeners
	context.subscriptions.push(
		vscode.debug.onDidStartDebugSession(session => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'startDebug', 
				name: session.name,
				debugType: session.type,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	context.subscriptions.push(
		vscode.debug.onDidTerminateDebugSession(session => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'endDebug', 
				name: session.name,
				debugType: session.type,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		})
	);

	// Extensions change listener
	context.subscriptions.push(
		vscode.extensions.onDidChange(() => {
			if (!isCapturing) return;
			
			enqueueEvent({
				type: 'extensionsChange',
				extensionCount: vscode.extensions.all.length,
				workspace: getIngestWorkspace(),
				timestamp: Date.now()
			});
		})
	);

	// Initialize Shell Integration Terminal Capture
	initializeTerminalCapture(context);

	// Start Git polling
	startGitPolling();

	// On deactivate, attempt final flush
	context.subscriptions.push({
		dispose: () => {
			isShuttingDown = true;
			if (flushIntervalHandle) {
				clearInterval(flushIntervalHandle);
			}
			// Attempt final flush
			const cfg2 = vscode.workspace.getConfiguration('memoryServerActivity');
			const offline = cfg2.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
			const redact = cfg2.get('redactPatterns', ['API_KEY', 'PRIVATE_KEY', 'PASSWORD', 'SECRET', 'TOKEN']) as string[];
			flushBuffer(offline, redact).catch(() => { /* noop */ });
		}
	});
}

/**
 * Initialize Shell Integration Terminal Capture
 */
function initializeTerminalCapture(context: vscode.ExtensionContext) {
	const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
	const captureEnabled = cfg.get('captureTerminalCommands', true);
	
	if (!captureEnabled) {
		logAction('terminalCapture_disabled');
		return;
	}

	// Track all terminals - existing and new ones
	const trackTerminalShellIntegration = (terminal: vscode.Terminal) => {
		// Log terminal open event
		if (isCapturing) {
			enqueueEvent({ 
				type: 'openTerminal', 
				name: terminal.name,
				workspace: getIngestWorkspace(),
				timestamp: Date.now() 
			});
		}

		if (terminal.shellIntegration) {
			logAction('terminalCapture_shellIntegrationAvailable', { name: terminal.name });
		} else {
			// Wait for shell integration to become available
			const disposable = vscode.window.onDidChangeTerminalShellIntegration(event => {
				if (event.terminal === terminal && event.shellIntegration) {
					logAction('terminalCapture_shellIntegrationReady', { name: terminal.name });
					disposable.dispose();
				}
			});
			context.subscriptions.push(disposable);
		}
	};

	// Register shell integration for existing terminals
	vscode.window.terminals.forEach(trackTerminalShellIntegration);

	// Register shell integration for new terminals
	context.subscriptions.push(
		vscode.window.onDidOpenTerminal(trackTerminalShellIntegration)
	);

	// Track terminal execution events using Shell Integration API
	context.subscriptions.push(
		vscode.window.onDidStartTerminalShellExecution(async (event) => {
			if (!isCapturing) return;
			
			try {
				const terminal = event.terminal;
				const execution = event.execution;
				
				// Capture command details
				const commandEvent = {
					type: 'terminalCommandStart',
					terminalName: terminal.name,
					commandLine: execution.commandLine.value,
					confidence: execution.commandLine.confidence,
					cwd: execution.cwd?.path,
					workspace: getIngestWorkspace(),
					timestamp: Date.now(),
					executionId: generateExecutionId()
				};
				
				enqueueEvent(commandEvent);
				logAction('terminalCommandStart', { 
					terminal: terminal.name, 
					command: execution.commandLine.value.substring(0, 50) + '...'
				});

				// Start capturing output stream
				try {
					const stream = execution.read();
					let output = '';
					
					for await (const data of stream) {
						output += data;
						
						// Enqueue intermediate output for long-running commands
						if (output.length > 1000) {
							enqueueEvent({
								type: 'terminalOutput',
								terminalName: terminal.name,
								executionId: commandEvent.executionId,
								output: output,
								isPartial: true,
								workspace: getIngestWorkspace(),
								timestamp: Date.now()
							});
							output = ''; // Reset buffer
						}
					}
					
					// Capture final output if any remaining
					if (output.length > 0) {
						enqueueEvent({
							type: 'terminalOutput',
							terminalName: terminal.name,
							executionId: commandEvent.executionId,
							output: output,
							isPartial: false,
							workspace: getIngestWorkspace(),
							timestamp: Date.now()
						});
					}
				} catch (outputError) {
					logAction('terminalOutputCapture_error', outputError);
					enqueueEvent({
						type: 'terminalOutputError',
						terminalName: terminal.name,
						executionId: commandEvent.executionId,
						error: String(outputError),
						workspace: getIngestWorkspace(),
						timestamp: Date.now()
					});
				}
			} catch (error) {
				logAction('terminalCapture_error', error);
			}
		})
	);

	// Track command completion
	context.subscriptions.push(
		vscode.window.onDidEndTerminalShellExecution((event) => {
			if (!isCapturing) return;
			
			try {
				const terminal = event.terminal;
				const execution = event.execution;
				
				enqueueEvent({
					type: 'terminalCommandEnd',
					terminalName: terminal.name,
					commandLine: execution.commandLine.value,
					exitCode: event.exitCode,
					cwd: execution.cwd?.path,
					workspace: getIngestWorkspace(),
					timestamp: Date.now(),
					executionId: generateExecutionId()
				});
				
				logAction('terminalCommandEnd', { 
					terminal: terminal.name, 
					exitCode: event.exitCode 
				});
			} catch (error) {
				logAction('terminalCommandEnd_error', error);
			}
		})
	);

	// Track shell integration changes
	context.subscriptions.push(
		vscode.window.onDidChangeTerminalShellIntegration((event) => {
			if (!isCapturing) return;
			
			try {
				const terminal = event.terminal;
				const shellIntegration = event.shellIntegration;
				
				enqueueEvent({
					type: 'terminalShellIntegrationChange',
					terminalName: terminal.name,
					cwd: shellIntegration?.cwd?.path,
					workspace: getIngestWorkspace(),
					timestamp: Date.now()
				});
				
				logAction('shellIntegrationChange', { 
					terminal: terminal.name,
					hasShellIntegration: !!shellIntegration
				});
			} catch (error) {
				logAction('shellIntegrationChange_error', error);
			}
		})
	);

	logAction('terminalCapture_initialized', { enabled: captureEnabled });
}

/**
 * Generate unique execution ID for tracking command flows
 */
function generateExecutionId(): string {
	return `exec_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
}

/**
 * Enqueue an event into the in-memory buffer
 */
function enqueueEvent(event: any) {
	if (!isCapturing) {
		console.log(`DEBUG: Event not captured because isCapturing=false:`, event.type);
		return;
	}
	
	try {
		// Attach metadata
		event._received_at = Date.now();
		event.workspace = event.workspace || getIngestWorkspace();
		event.vscode_version = vscode.version;
		
		eventsBuffer.push(event);
		eventsSummaryBuffer.push({...event}); // Add copy to summary buffer
		
		// Keep summary buffer manageable (last 500 events)
		if (eventsSummaryBuffer.length > 500) {
			eventsSummaryBuffer = eventsSummaryBuffer.slice(-500);
		}
		
		console.log(`DEBUG: Event added to buffers - main: ${eventsBuffer.length}, summary: ${eventsSummaryBuffer.length}, type: ${event.type}`);
		
		// Send event to activity monitor
		if (activityMonitorProvider) {
			activityMonitorProvider.addEvent(event);
		}
		
		// If buffer grows too large, trigger immediate flush
		if (eventsBuffer.length > 100) {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			const offline = cfg.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
			const redact = cfg.get('redactPatterns', ['API_KEY', 'PRIVATE_KEY', 'PASSWORD', 'SECRET', 'TOKEN']) as string[];
			flushBuffer(offline, redact).catch(() => { /* noop */ });
		}
	} catch (e) {
		console.warn('enqueueEvent error', e);
	}
}

/**
 * Flush buffer: attempt to POST events to Memory-Server endpoint
 */
async function flushBuffer(offlinePath: string, redactPatterns: string[]) {
	if (flushing) return;
	if (eventsBuffer.length === 0) return;
	
	flushing = true;
	const toSend = eventsBuffer.splice(0, eventsBuffer.length);
	const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
	const apiUrl = cfg.get('apiUrl', DEFAULT_MEMORY_SERVER_API_URL) as string;

	// Redact content as configured
	for (const ev of toSend) {
		redactEvent(ev, redactPatterns);
	}

	try {
		const payload = {
			workspace: getIngestWorkspace(),
			query_workspaces: getQueryWorkspaces(),
			events: toSend,
			source: 'vscode-extension',
			auto_tag: cfg.get('autoTag', true),
			metadata: {
				vscode_version: vscode.version,
				extension_version: '1.0.0',
				platform: process.platform,
				arch: process.arch,
				workspace_model: 'ingest-only'
			}
		};

		const ok = await postJson(apiUrl, payload);
		if (!ok) {
			// persist to offline file
			persistOfflineEvents(offlinePath, toSend);
		}
	} catch (err) {
		// On error, persist
		persistOfflineEvents(offlinePath, toSend);
	}
	flushing = false;
}

/**
 * Persist array of events to offline JSONL
 */
function persistOfflineEvents(offlinePath: string, events: any[]) {
	try {
		const data = events.map(e => JSON.stringify(e)).join('\n') + '\n';
		fs.appendFileSync(offlinePath, data, { encoding: 'utf8' });
		logAction('persistOfflineEvents', { file: offlinePath, count: events.length });
	} catch (e) {
		console.warn('persistOfflineEvents error', e);
	}
}

/**
 * Replay offline events from JSONL and try to send them
 */
async function replayOfflineEvents(offlinePath: string, redactPatterns: string[]) {
	try {
		if (!fs.existsSync(offlinePath)) return;
		
		const content = fs.readFileSync(offlinePath, 'utf8').trim();
		if (!content) return;
		
		const lines = content.split('\n').filter(Boolean);
		const events = lines.map(l => {
			try { return JSON.parse(l); } catch { return null; }
		}).filter(Boolean);
		
		if (events.length === 0) return;
		
		const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
		const apiUrl = cfg.get('apiUrl', DEFAULT_MEMORY_SERVER_API_URL) as string;
		
		for (const ev of events) redactEvent(ev, redactPatterns);
		
		const payload = {
			workspace: getIngestWorkspace(),
			events,
			source: 'vscode-extension-offline',
			auto_tag: cfg.get('autoTag', true),
			metadata: {
				replayed: true,
				replay_timestamp: Date.now()
			}
		};
		
		const ok = await postJson(apiUrl, payload);
		if (ok) {
			// truncate file
			fs.writeFileSync(offlinePath, '', 'utf8');
			logAction('replayOfflineEvents_success', { file: offlinePath, count: events.length });
		} else {
			logAction('replayOfflineEvents_failed', { file: offlinePath, count: events.length });
		}
	} catch (e) {
		console.warn('replayOfflineEvents error', e);
	}
}

/**
 * Post JSON to endpoint
 */
function postJson(urlStr: string, body: any): Promise<boolean> {
	return new Promise((resolve) => {
		try {
			const urlObj = new URL(urlStr);
			const postData = JSON.stringify(body);
			const options: any = {
				hostname: urlObj.hostname,
				port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
				path: urlObj.pathname + (urlObj.search || ''),
				method: 'POST',
				headers: {
					'Content-Type': 'application/json',
					'Content-Length': Buffer.byteLength(postData)
				},
				timeout: 10000
			};
			
			const client = urlObj.protocol === 'https:' ? https : http;
			const req = client.request(options, (res: any) => {
				const status = res.statusCode || 0;
				// consume data
				res.on('data', () => { });
				res.on('end', () => {
					resolve(status >= 200 && status < 300);
				});
			});
			
			req.on('error', (err: any) => {
				console.warn('postJson error', err);
				resolve(false);
			});
			
			req.on('timeout', () => {
				req.destroy();
				resolve(false);
			});
			
			req.write(postData);
			req.end();
		} catch (e) {
			console.warn('postJson fatal', e);
			resolve(false);
		}
	});
}

/**
 * Redact fields in an event object according to configured patterns
 */
function redactEvent(ev: any, patterns: string[]) {
	if (!ev || !patterns || patterns.length === 0) return;
	
	const regexes = patterns.map(p => new RegExp(p, 'i'));
	const walk = (obj: any): any => {
		if (obj == null) return obj;
		
		if (typeof obj === 'string') {
			for (const r of regexes) {
				if (r.test(obj)) {
					return '[REDACTED]';
				}
			}
			return obj;
		}
		
		if (Array.isArray(obj)) {
			return obj.map((item: any) => walk(item));
		}
		
		if (typeof obj === 'object') {
			const out: any = {};
			for (const k of Object.keys(obj)) {
				out[k] = walk(obj[k]);
			}
			return out;
		}
		
		return obj;
	};
	
	const redacted = walk(ev);
	// copy redacted fields back into ev
	Object.keys(redacted).forEach(k => ev[k] = redacted[k]);
}

/**
 * Start periodic flush interval
 */
function startFlushInterval(intervalMs = 5000) {
	if (flushIntervalHandle) clearInterval(flushIntervalHandle);
	
	flushIntervalHandle = setInterval(() => {
		const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
		const offline = cfg.get('offlineStoragePath', 'memory-server-activity/offline_events.jsonl') as string;
		const redact = cfg.get('redactPatterns', ['API_KEY', 'PRIVATE_KEY', 'PASSWORD', 'SECRET', 'TOKEN']) as string[];
		flushBuffer(offline, redact).catch(e => console.warn('flush interval error', e));
	}, intervalMs);
}

/**
 * Detect latest commit and register it
 */
function detectAndRegisterLatestCommit() {
	const workspaceRoot = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0]?.uri.fsPath;
	if (!workspaceRoot) return;
	
	exec('git log --pretty=format:"%H|%s|%an" -n 1', { cwd: workspaceRoot }, (err, stdout) => {
		if (err || !stdout) return;
		
		const [hash, message, author] = stdout.trim().split('|');
		exec(`git show --stat ${hash}`, { cwd: workspaceRoot }, (err2, statOut) => {
			if (err2 || !statOut) return;
			
			enqueueEvent({
				type: 'commit',
				hash,
				message,
				author,
				summary: statOut,
				workspace: getIngestWorkspace(),
				timestamp: Date.now()
			});
			lastGitHead = hash;
		});
	});
}

/**
 * Poll git HEAD to detect new commits
 */
function startGitPolling(pollIntervalMs = 10000) {
	const workspaceRoot = vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders[0]?.uri.fsPath;
	if (!workspaceRoot) return;
	
	setInterval(() => {
		exec('git rev-parse HEAD', { cwd: workspaceRoot }, (err, stdout) => {
			if (err || !stdout) return;
			
			const hash = stdout.trim();
			if (lastGitHead && hash !== lastGitHead) {
				exec(`git log --pretty=format:"%H|%an|%s" -n 1`, { cwd: workspaceRoot }, (err2, out2) => {
					if (err2 || !out2) return;
					
					const [h, author, message] = out2.trim().split('|');
					exec(`git show --stat ${h}`, { cwd: workspaceRoot }, (err3, statOut) => {
						if (err3 || !statOut) return;
						
						enqueueEvent({
							type: 'commit',
							hash: h,
							author,
							message,
							summary: statOut,
							workspace: getIngestWorkspace(),
							timestamp: Date.now()
						});
						lastGitHead = h;
					});
				});
			} else if (!lastGitHead) {
				lastGitHead = hash;
			}
		});
	}, pollIntervalMs);
}

/**
 * Generate activity summary from recent events
 */
function generateActivitySummary(events: any[]): string {
	const now = new Date();
	const eventTypes = new Map<string, number>();
	const files = new Set<string>();
	const languages = new Set<string>();
	
	let firstEventTime: Date | null = null;
	let lastEventTime: Date | null = null;
	
	for (const event of events) {
		const eventTime = new Date(event.timestamp);
		if (!firstEventTime || eventTime < firstEventTime) {
			firstEventTime = eventTime;
		}
		if (!lastEventTime || eventTime > lastEventTime) {
			lastEventTime = eventTime;
		}
		
		eventTypes.set(event.type, (eventTypes.get(event.type) || 0) + 1);
		
		if (event.file) {
			files.add(path.basename(event.file));
		}
		if (event.language) {
			languages.add(event.language);
		}
	}
	
	const timeSpan = firstEventTime && lastEventTime 
		? `${firstEventTime.toLocaleString()} - ${lastEventTime.toLocaleString()}`
		: 'Unknown';
	
	let summary = `# Memory-Server Activity Summary\n\n`;
	summary += `**Generated:** ${now.toLocaleString()}\n`;
	summary += `**Workspace:** ${getIngestWorkspace()}\n`;
	summary += `**Time Period:** ${timeSpan}\n`;
	summary += `**Total Events:** ${events.length}\n\n`;
	
	summary += `## Event Types\n\n`;
	const sortedTypes = Array.from(eventTypes.entries()).sort((a, b) => b[1] - a[1]);
	for (const [type, count] of sortedTypes) {
		summary += `- **${type}:** ${count}\n`;
	}
	
	if (languages.size > 0) {
		summary += `\n## Languages Used\n\n`;
		summary += Array.from(languages).sort().map(lang => `- ${lang}`).join('\n');
		summary += `\n`;
	}
	
	if (files.size > 0) {
		summary += `\n## Files Accessed\n\n`;
		const topFiles = Array.from(files).slice(0, 20);
		summary += topFiles.map(file => `- ${file}`).join('\n');
		if (files.size > 20) {
			summary += `\n- ... and ${files.size - 20} more files\n`;
		}
	}
	
	summary += `\n## Memory-Server Integration\n\n`;
	summary += `This activity summary was generated by the Memory-Server VSCode extension. `;
	summary += `All captured development activity is automatically stored in the **${getIngestWorkspace()}** workspace `;
	summary += `with intelligent auto-tagging for enhanced searchability and organization.\n\n`;
	summary += `The captured data helps Memory-Server provide more relevant code assistance, `;
	summary += `documentation suggestions, and contextual insights based on your actual development patterns.`;
	
	return summary;
}

/**
 * Simple action logger
 */
function logAction(action: string, meta?: any) {
	try {
		const timestamp = new Date().toISOString();
		console.log(`[Memory-Server Activity] ${timestamp} ${action}`, meta || '');
	} catch (e) {
		console.warn('logAction error', e);
	}
}

/**
 * Generate Terminal Activity Summary
 */
function generateTerminalSummary(events: any[]): string {
	const now = new Date();
	const commands = new Map<string, { count: number; success: number; failures: number }>();
	const terminals = new Set<string>();
	
	events.forEach(event => {
		if (event.type === 'terminalCommandEnd') {
			const cmd = event.commandLine.split(' ')[0];
			const current = commands.get(cmd) || { count: 0, success: 0, failures: 0 };
			current.count++;
			if (event.exitCode === 0) current.success++;
			else current.failures++;
			commands.set(cmd, current);
		}
		if (event.terminalName) {
			terminals.add(event.terminalName);
		}
	});

	let summary = `# Terminal Activity Summary\n\n`;
	summary += `**Generated:** ${now.toLocaleString()}\n`;
	summary += `**Workspace:** ${getIngestWorkspace()}\n`;
	summary += `**Total Terminal Events:** ${events.length}\n`;
	summary += `**Active Terminals:** ${terminals.size}\n\n`;

	if (commands.size > 0) {
		summary += `## Command Statistics\n\n`;
		const sortedCommands = Array.from(commands.entries()).sort((a, b) => b[1].count - a[1].count);
		for (const [cmd, stats] of sortedCommands) {
			const successRate = stats.count > 0 ? Math.round((stats.success / stats.count) * 100) : 0;
			summary += `- **${cmd}:** ${stats.count} executions (${successRate}% success)\n`;
		}
	}

	summary += `\n## Recent Terminal Activity\n\n`;
	const recentCommands = events.filter(e => e.type === 'terminalCommandStart').slice(-5);
	recentCommands.forEach(cmd => {
		const time = new Date(cmd.timestamp).toLocaleTimeString();
		summary += `- **[${time}]** \`${cmd.commandLine}\` in ${cmd.terminalName}\n`;
	});

	return summary;
}

/**
 * Generate File Activity Summary  
 */
function generateFileSummary(events: any[]): string {
	const now = new Date();
	const files = new Map<string, number>();
	const languages = new Set<string>();
	
	events.forEach(event => {
		if (event.file) {
			const filename = event.file.split('/').pop() || event.file;
			files.set(filename, (files.get(filename) || 0) + 1);
		}
		if (event.language) {
			languages.add(event.language);
		}
	});

	let summary = `# File Activity Summary\n\n`;
	summary += `**Generated:** ${now.toLocaleString()}\n`;
	summary += `**Workspace:** ${getIngestWorkspace()}\n`;
	summary += `**Total File Events:** ${events.length}\n`;
	summary += `**Languages Used:** ${languages.size}\n\n`;

	if (files.size > 0) {
		summary += `## Most Active Files\n\n`;
		const sortedFiles = Array.from(files.entries()).sort((a, b) => b[1] - a[1]).slice(0, 10);
		sortedFiles.forEach(([file, count]) => {
			summary += `- **${file}:** ${count} activities\n`;
		});
	}

	if (languages.size > 0) {
		summary += `\n## Languages\n\n`;
		Array.from(languages).sort().forEach(lang => {
			summary += `- ${lang}\n`;
		});
	}

	return summary;
}

/**
 * Generate Comprehensive Activity Summary with Terminal Details
 */
function generateComprehensiveActivitySummary(events: any[]): string {
	const now = new Date();
	const eventTypes = new Map<string, number>();
	const files = new Set<string>();
	const languages = new Set<string>();
	const terminalCommands = new Map<string, { count: number; success: number; failures: number }>();
	const terminals = new Set<string>();
	
	let firstEventTime: Date | null = null;
	let lastEventTime: Date | null = null;
	
	for (const event of events) {
		const eventTime = new Date(event.timestamp);
		if (!firstEventTime || eventTime < firstEventTime) {
			firstEventTime = eventTime;
		}
		if (!lastEventTime || eventTime > lastEventTime) {
			lastEventTime = eventTime;
		}
		
		eventTypes.set(event.type, (eventTypes.get(event.type) || 0) + 1);
		
		// Collect file information
		if (event.file) {
			files.add(path.basename(event.file));
		}
		if (event.language) {
			languages.add(event.language);
		}
		
		// Collect terminal command information
		if (event.type === 'terminalCommandEnd' && event.commandLine) {
			const cmd = event.commandLine.split(' ')[0];
			const current = terminalCommands.get(cmd) || { count: 0, success: 0, failures: 0 };
			current.count++;
			if (event.exitCode === 0) current.success++;
			else current.failures++;
			terminalCommands.set(cmd, current);
		}
		if (event.terminalName) {
			terminals.add(event.terminalName);
		}
	}
	
	const timeSpan = firstEventTime && lastEventTime 
		? `${firstEventTime.toLocaleString()} - ${lastEventTime.toLocaleString()}`
		: 'Unknown';
	
	let summary = `# Comprehensive Activity Summary\n\n`;
	summary += `**Generated:** ${now.toLocaleString()}\n`;
	summary += `**Workspace:** ${getIngestWorkspace()}\n`;
	summary += `**Time Period:** ${timeSpan}\n`;
	summary += `**Total Events:** ${events.length}\n`;
	summary += `**Active Terminals:** ${terminals.size}\n\n`;
	
	// Terminal Commands Section (most important for the user)
	if (terminalCommands.size > 0) {
		summary += `## 💻 Terminal Commands\n\n`;
		const sortedCommands = Array.from(terminalCommands.entries()).sort((a, b) => b[1].count - a[1].count);
		for (const [cmd, stats] of sortedCommands) {
			const successRate = stats.count > 0 ? Math.round((stats.success / stats.count) * 100) : 0;
			summary += `- **\`${cmd}\`:** ${stats.count} executions (${successRate}% success)\n`;
		}
		summary += `\n`;
	}
	
	// Event Types Overview
	summary += `## 📊 Event Types\n\n`;
	const sortedTypes = Array.from(eventTypes.entries()).sort((a, b) => b[1] - a[1]);
	for (const [type, count] of sortedTypes) {
		summary += `- **${type}:** ${count}\n`;
	}
	
	// Languages and Files
	if (languages.size > 0) {
		summary += `\n## 🔤 Languages Used\n\n`;
		summary += Array.from(languages).sort().map(lang => `- ${lang}`).join('\n');
		summary += `\n`;
	}
	
	if (files.size > 0) {
		summary += `\n## 📁 Files Accessed\n\n`;
		const topFiles = Array.from(files).slice(0, 15);
		summary += topFiles.map(file => `- ${file}`).join('\n');
		if (files.size > 15) {
			summary += `\n- ... and ${files.size - 15} more files\n`;
		}
	}
	
	// Recent Terminal Activity Detail
	const recentTerminalEvents = events.filter(event => 
		event.type.startsWith('terminal')
	).slice(-10);
	
	if (recentTerminalEvents.length > 0) {
		summary += `\n## 🕐 Recent Terminal Activity\n\n`;
		recentTerminalEvents.forEach((event, index) => {
			const time = new Date(event.timestamp).toLocaleTimeString();
			if (event.type === 'terminalCommandStart') {
				summary += `${index + 1}. **[${time}]** \`${event.commandLine}\` (started in ${event.terminalName})\n`;
			} else if (event.type === 'terminalCommandEnd') {
				const status = event.exitCode === 0 ? '✅' : '❌';
				summary += `${index + 1}. **[${time}]** ${status} \`${event.commandLine}\` (exit code: ${event.exitCode})\n`;
			}
		});
	}
	
	summary += `\n## 🔗 Memory-Server Integration\n\n`;
	summary += `This comprehensive summary was generated by the Memory-Server VSCode extension. `;
	summary += `All captured development activity is automatically stored in the **${getIngestWorkspace()}** workspace `;
	summary += `with intelligent auto-tagging for enhanced searchability and organization.\n\n`;
	summary += `**Terminal commands** and their outputs are captured in real-time, providing Memory-Server `;
	summary += `with context about your development workflow, build processes, and debugging sessions.`;
	
	return summary;
}

/**
 * Exported deactivate function
 */
export function deactivate() {
	// Flush is handled by dispose subscription
}