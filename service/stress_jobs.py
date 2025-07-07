"""Stress test script to submit random jobs for all applications."""
import argparse
import json
import os
import random
import time

# Ensure the service package root is on the import path when running directly
PACKAGE_PATH = os.path.abspath(os.path.dirname(__file__))
import sys
if PACKAGE_PATH not in sys.path:
    sys.path.insert(0, PACKAGE_PATH)

from flask import current_app

from .flask_app import app
from .models import db, User, Task
from .config_utils import load_config
from .tasks import schedule_task


_DEF_SAMPLE = "sample.s2p"


def _ensure_sample_file():
    """Create a minimal Touchstone file for S-parameter tasks."""
    base_dir = os.path.dirname(PACKAGE_PATH)
    path = os.path.join(base_dir, _DEF_SAMPLE)
    if os.path.exists(path):
        return path
    with open(path, "w") as f:
        f.write("# Hz S RI R 50\n")
        for i in range(1, 11):
            f.write(f"{i} 1 0 0 1\n")
    return path


def generate_params(task_type):
    """Return randomized parameters for a task type."""
    if task_type == "fractal":
        return {"depth": random.randint(1, 6)}
    if task_type == "primes":
        return {"n": random.randint(1000, 10000)}
    if task_type == "microstrip":
        return {
            "thickness": random.choice(["0.8", "1.6"]),
            "er": random.choice(["2.2", "4.4"]),
            "tand": random.choice(["0.001", "0.02"]),
            "width": random.choice(["2", "3"]),
            "length": random.choice(["10", "20"]),
            "srange": "0GHz 10GHz 201",
        }
    if task_type == "sparams":
        sample = _ensure_sample_file()
        return {
            "file": os.path.basename(sample),
            "plot": "xy",
            "parameter": "S",
            "operation": "db",
        }
    return {}


def main(iterations: int, rate: float, seed: int | None = None):
    random.seed(seed)
    with app.app_context():
        users = User.query.filter_by(is_admin=False).all()
        if not users:
            print("No non-admin users found.")
            return
        configs = load_config()
        task_types = list(configs.keys())
        base_dir = os.path.dirname(PACKAGE_PATH)
        for _ in range(iterations):
            user = random.choice(users)
            ttype = random.choice(task_types)
            params = generate_params(ttype)
            task = Task(
                user_id=user.id,
                task_type=ttype,
                parameters=json.dumps(params),
            )
            db.session.add(task)
            db.session.commit()

            if ttype == "sparams" and "file" in params:
                output_dir = os.path.join(base_dir, "outputs", str(task.id))
                os.makedirs(output_dir, exist_ok=True)
                sample_file = os.path.join(base_dir, params["file"])
                dest = os.path.join(output_dir, params["file"])
                if not os.path.exists(dest):
                    from shutil import copyfile
                    copyfile(sample_file, dest)

            schedule_task(task.id)
            delay = random.expovariate(rate)
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Submit random jobs for stress testing.")
    parser.add_argument("--iterations", type=int, default=10, help="Number of jobs to submit")
    parser.add_argument("--rate", type=float, default=1.0, help="Average jobs per second")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()
    main(args.iterations, args.rate, args.seed)
