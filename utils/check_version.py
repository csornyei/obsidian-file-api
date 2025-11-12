import sys
import tomllib
from pathlib import Path

data = tomllib.loads(Path("pyproject.toml").read_text())

version = data.get("project").get("version")

if not version:
    print("Could not find version in pyproject.toml", file=sys.stderr)
    sys.exit(1)

print(version)
