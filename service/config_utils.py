import os
import yaml
import ast
from flask import current_app


def load_config():
    """Load task configuration from YAML file.

    The path is resolved relative to the project root so the function
    works regardless of the current working directory when the
    application starts.
    """
    base_dir = os.path.dirname(os.path.dirname(__file__))
    config_path = os.path.join(base_dir, 'task_config.yaml')
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_task_description(task_type):
    """Return the module level docstring from a task's script."""
    configs = load_config()
    conf = configs.get(task_type)
    if not conf:
        return ''
    script_rel = conf.get('script_path')
    if not script_rel:
        return ''
    script_path = os.path.join(current_app.root_path, script_rel)
    try:
        with open(script_path, 'r') as f:
            module = ast.parse(f.read())
        return ast.get_docstring(module) or ''
    except FileNotFoundError:
        return ''
