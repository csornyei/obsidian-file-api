import sys
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text())

project_data = data.get("project")
version = project_data.get("version") if project_data else None

if not version:
    print("Could not find version in pyproject.toml", file=sys.stderr)
    sys.exit(1)

print(version)
