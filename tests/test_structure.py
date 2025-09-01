import os


def test_project_structure_exists():
    required_dirs = [
        'config',
        'servers',
        'services',
        'api/rest',
        'api/websocket',
        'mcp',
        'models/shared',
        'models/profiles/dev',
        'models/profiles/productivity',
        'models/profiles/academic',
        'models/profiles/general',
        'tools',
        'logs/system',
        'logs/memory-server',
        'logs/llm-server',
        'logs/gui-server',
        'var/run',
        'var/state',
        'docs/development',
    ]
    for path in required_dirs:
        assert os.path.isdir(path), f"Missing directory: {path}"

