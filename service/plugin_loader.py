import os
import json
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
APP_DIR = os.path.join(BASE_DIR, 'apps')
REGISTRY_FILE = os.path.join(BASE_DIR, 'app_registry.json')


def load_registry():
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_registry(reg):
    with open(REGISTRY_FILE, 'w') as f:
        json.dump(reg, f, indent=2)


def scan_plugins():
    """Scan the apps directory and return plugin info."""
    registry = load_registry()
    plugins = {}
    changed = False
    if not os.path.isdir(APP_DIR):
        return plugins
    for name in os.listdir(APP_DIR):
        pdir = os.path.join(APP_DIR, name)
        if not os.path.isdir(pdir):
            continue
        meta_path = os.path.join(pdir, 'metadata.json')
        runner_path = os.path.join(pdir, 'runner.py')
        if not os.path.exists(meta_path) or not os.path.exists(runner_path):
            continue
        with open(meta_path) as f:
            metadata = json.load(f)
        cfg_path = os.path.join(pdir, 'config.yaml')
        config = {}
        if os.path.exists(cfg_path):
            with open(cfg_path) as cf:
                config = yaml.safe_load(cf) or {}
        enabled = registry.get(name, True)
        if name not in registry:
            registry[name] = True
            changed = True
        plugins[name] = {
            'metadata': metadata,
            'config': config,
            'enabled': enabled,
            'path': pdir,
        }
    if changed:
        save_registry(registry)
    return plugins
