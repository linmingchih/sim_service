import os
import yaml
import ast
from flask import current_app

from .plugin_loader import scan_plugins


def load_config(enabled_only: bool = True):
    """Load plugin configurations.

    Parameters are gathered from each plugin's ``config.yaml``. The
    return value mirrors the old ``task_config.yaml`` structure so
    existing code can consume it with minimal changes.
    """
    plugins = scan_plugins()
    service_root = os.path.dirname(__file__)
    configs: dict[str, dict] = {}
    for name, info in plugins.items():
        if enabled_only and not info["enabled"]:
            continue
        cfg = info.get("config", {})
        script = cfg.get("script", "runner.py")
        script_rel = os.path.relpath(os.path.join(info["path"], script), service_root)
        configs[name] = {
            "venv_python": cfg.get("venv_python", "python"),
            "script_path": script_rel,
            "params_def": cfg.get("parameters", {}),
            "metadata": info.get("metadata", {}),
            "result_keep": cfg.get("result_keep"),
        }
    return configs


def get_task_description(task_type: str) -> str:
    """Return the module level docstring from a plugin's runner."""
    configs = load_config(enabled_only=False)
    conf = configs.get(task_type)
    if not conf:
        return ""
    script_rel = conf.get("script_path")
    if not script_rel:
        return ""
    script_path = os.path.join(current_app.root_path, script_rel)
    try:
        with open(script_path, "r") as f:
            module = ast.parse(f.read())
        return ast.get_docstring(module) or ""
    except FileNotFoundError:
        return ""
