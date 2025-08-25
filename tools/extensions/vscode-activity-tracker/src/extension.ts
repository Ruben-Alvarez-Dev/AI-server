// VS Code extensibility API
import * as vscode from 'vscode';
import * as https from 'https';
import * as http from 'http';
import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';

// Default Memory-Server API endpoint
const DEFAULT_MEMORY_SERVER_API_URL = 'http://localhost:8001/api/v1/documents/activity';

// In-memory buffer and state
let eventsBuffer: any[] = [];
let flushing = false;
let flushIntervalHandle: NodeJS.Timeout | undefined;
let lastGitHead: string | undefined;
let isShuttingDown = false;
let activityTreeProvider: MemoryServerActivityTreeProvider;
let isCapturing = true;
let currentWorkspace = 'code';

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
				new ActivityItem('Recent Activity', vscode.TreeItemCollapsibleState.Expanded, 'activity'),
				new ActivityItem('Activity Summary', vscode.TreeItemCollapsibleState.None, 'activitySummary'),
				new ActivityItem('Offline Data', vscode.TreeItemCollapsibleState.None, 'offlineData')
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
			const workspaces = ['code', 'research', 'projects', 'personal'];
			return Promise.resolve(workspaces.map(ws => 
				new ActivityItem(
					`${ws.charAt(0).toUpperCase() + ws.slice(1)} ${ws === currentWorkspace ? '(active)' : ''}`,
					vscode.TreeItemCollapsibleState.None,
					'workspaceItem',
					{
						command: 'memoryServerActivity.switchWorkspace',
						title: `Switch to ${ws}`,
						arguments: [ws]
					}
				)
			));
		} else if (element.contextValue === 'config') {
			const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
			return Promise.resolve([
				new ActivityItem(`Max File Size: ${cfg.get('maxFileSizeBytes', 1048576)} bytes`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Terminal Capture: ${cfg.get('captureTerminalCommands', false) ? 'On' : 'Off'}`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Excluded Patterns: ${(cfg.get('excludedPatterns', []) as string[]).length} items`, vscode.TreeItemCollapsibleState.None, 'configItem'),
				new ActivityItem(`Flush Interval: ${cfg.get('flushInterval', 5000)}ms`, vscode.TreeItemCollapsibleState.None, 'configItem')
			]);
		} else if (element.contextValue === 'activity') {
			const recentEvents = eventsBuffer.slice(-5).reverse();
			return Promise.resolve(recentEvents.map(event => 
				new ActivityItem(`${event.type} - ${new Date(event.timestamp).toLocaleTimeString()}`, vscode.TreeItemCollapsibleState.None, 'activityItem')
			));
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
	
	currentWorkspace = cfg.get('workspace', 'code') as string;

	// Ensure offline directory exists
	try {
		const offlineDir = path.dirname(offlinePath);
		if (offlineDir && offlineDir !== '.') {
			fs.mkdirSync(offlineDir, { recursive: true });
		}
	} catch (e) {
		console.warn('Could not create offline directory', e);
	}

	logAction('activate', { apiUrl, enabled, workspace: currentWorkspace });

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

	// Refresh tree view periodically
	setInterval(() => {
		activityTreeProvider.refresh();
	}, 5000);

	// Register configuration change listener
	context.subscriptions.push(
		vscode.workspace.onDidChangeConfiguration(event => {
			if (event.affectsConfiguration('memoryServerActivity')) {
				const newCfg = vscode.workspace.getConfiguration('memoryServerActivity');
				const newWorkspace = newCfg.get('workspace', 'code') as string;
				
				if (newWorkspace !== currentWorkspace) {
					currentWorkspace = newWorkspace;
					enqueueEvent({
						type: 'workspaceChange',
						oldWorkspace: currentWorkspace,
						newWorkspace: newWorkspace,
						timestamp: Date.now()
					});
				}
				
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
				const workspaces = ['code', 'research', 'projects', 'personal'];
				workspace = await vscode.window.showQuickPick(workspaces, {
					placeHolder: 'Select workspace for development activities',
					canPickMany: false
				});
			}
			
			if (workspace && workspace !== currentWorkspace) {
				const oldWorkspace = currentWorkspace;
				currentWorkspace = workspace;
				
				// Update configuration
				const cfg = vscode.workspace.getConfiguration('memoryServerActivity');
				await cfg.update('workspace', workspace, vscode.ConfigurationTarget.Global);
				
				enqueueEvent({
					type: 'workspaceSwitch',
					oldWorkspace: oldWorkspace,
					newWorkspace: workspace,
					timestamp: Date.now()
				});
				
				vscode.window.showInformationMessage(`Switched to ${workspace} workspace`);
				activityTreeProvider.refresh();
			}
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
• Workspace: ${currentWorkspace}
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
			const recentEvents = eventsBuffer.slice(-50);
			if (recentEvents.length === 0) {
				vscode.window.showInformationMessage('No recent activity to summarize');
				return;
			}

			const summary = generateActivitySummary(recentEvents);
			
			// Show summary in a new document
			const doc = await vscode.workspace.openTextDocument({
				content: summary,
				language: 'markdown'
			});
			vscode.window.showTextDocument(doc);
			
			enqueueEvent({
				type: 'summaryGenerated',
				eventCount: recentEvents.length,
				timestamp: Date.now()
			});
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

	// Document activity listeners
	context.subscriptions.push(
		vscode.workspace.onDidChangeTextDocument(event => {
			if (!isCapturing) return;
			
			enqueueEvent({
				type: 'edit',
				file: event.document.uri.fsPath,
				language: event.document.languageId,
				changes: event.contentChanges.length,
				workspace: currentWorkspace,
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
				workspace: currentWorkspace,
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
				workspace: currentWorkspace,
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
				workspace: currentWorkspace,
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
				workspace: currentWorkspace,
				timestamp: Date.now() 
			});
		})
	);

	// Terminal listeners
	context.subscriptions.push(
		vscode.window.onDidOpenTerminal(terminal => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'openTerminal', 
				name: terminal.name,
				workspace: currentWorkspace,
				timestamp: Date.now() 
			});
		})
	);

	context.subscriptions.push(
		vscode.window.onDidCloseTerminal(terminal => {
			if (!isCapturing) return;
			
			enqueueEvent({ 
				type: 'closeTerminal', 
				name: terminal.name,
				workspace: currentWorkspace,
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
				type: session.type,
				workspace: currentWorkspace,
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
				type: session.type,
				workspace: currentWorkspace,
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
				workspace: currentWorkspace,
				timestamp: Date.now()
			});
		})
	);

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
 * Enqueue an event into the in-memory buffer
 */
function enqueueEvent(event: any) {
	if (!isCapturing) return;
	
	try {
		// Attach metadata
		event._received_at = Date.now();
		event.workspace = event.workspace || currentWorkspace;
		event.vscode_version = vscode.version;
		
		eventsBuffer.push(event);
		
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
			workspace: currentWorkspace,
			events: toSend,
			source: 'vscode-extension',
			auto_tag: cfg.get('autoTag', true),
			metadata: {
				vscode_version: vscode.version,
				extension_version: '1.0.0',
				platform: process.platform,
				arch: process.arch
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
			workspace: currentWorkspace,
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
				workspace: currentWorkspace,
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
							workspace: currentWorkspace,
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
	summary += `**Workspace:** ${currentWorkspace}\n`;
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
	summary += `All captured development activity is automatically stored in the **${currentWorkspace}** workspace `;
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
 * Exported deactivate function
 */
export function deactivate() {
	// Flush is handled by dispose subscription
}