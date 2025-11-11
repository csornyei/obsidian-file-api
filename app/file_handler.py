from pathlib import Path
from typing import Literal

import yaml

from .env import BASE_DIR


class FileHandler:
    def __init__(self, base_folder: str):
        path = Path(base_folder)
        if not path.exists() or not path.is_dir():
            raise ValueError(
                f"The provided base_folder '{base_folder}' is not a valid directory."
            )

        self.base_folder = base_folder

    def __filter(self, items: list[Path]) -> list[Path]:
        items = filter(
            lambda x: not any(part.startswith(".") for part in x.parts), items
        )
        items = map(lambda x: x.as_posix(), items)
        return list(items)

    def list_files(self, file_path: str, all: bool = False) -> list[str]:
        if Path(file_path).is_absolute():
            raise ValueError("The file_path must be a relative path.")

        full_path = Path(self.base_folder) / file_path
        if not full_path.exists() or not full_path.is_dir():
            raise ValueError(
                f"The provided file_path '{file_path}' is not a valid directory within the base folder."
            )

        if all:
            files = [
                p.relative_to(self.base_folder)
                for p in full_path.rglob("*.md")
                if p.is_file()
            ]
        else:
            files = [
                p.relative_to(self.base_folder)
                for p in full_path.iterdir()
                if p.suffix == ".md" and p.is_file()
            ]

        return self.__filter(files)

    def list_dirs(self, dir_path: str, all: bool = False) -> list[str]:
        if Path(dir_path).is_absolute():
            raise ValueError("The dir_path must be a relative path.")

        full_path = Path(self.base_folder) / dir_path
        if not full_path.exists() or not full_path.is_dir():
            raise ValueError(
                f"The provided dir_path '{dir_path}' is not a valid directory within the base folder."
            )

        if all:
            dirs = [
                p.relative_to(self.base_folder)
                for p in full_path.rglob("*")
                if p.is_dir()
            ]
            return self.__filter(dirs)
        else:
            dirs = [
                p.relative_to(self.base_folder)
                for p in full_path.iterdir()
                if p.is_dir()
            ]
            return self.__filter(dirs)

    def read_file(self, file_path: str) -> list[str]:
        if Path(file_path).is_absolute():
            raise ValueError("The file_path must be a relative path.")

        full_path = Path(self.base_folder) / file_path
        if not full_path.exists() or not full_path.is_file():
            raise ValueError(
                f"The provided file_path '{file_path}' is not a valid file within the base folder."
            )

        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        lines = content.splitlines()

        return lines

    def get_frontmatter(self, file_path: str) -> dict:
        lines = self.read_file(file_path)
        frontmatter: str = []

        if lines[0].strip() == "---":
            for line in lines[1:]:
                line = line.strip()
                if line == "---":
                    break
                frontmatter.append(line)

        if not frontmatter:
            return {}

        frontmatter_str = "\n".join(frontmatter)
        return yaml.safe_load(frontmatter_str)

    def get_text_content(self, file_path: str) -> list[str]:
        lines = self.read_file(file_path)

        content: list[str] = []
        status: Literal["before_frontmatter", "in_frontmatter", "after_frontmatter"] = (
            "before_frontmatter"
        )

        for line in lines:
            stripped_line = line.strip()
            if stripped_line == "---":
                match status:
                    case "before_frontmatter":
                        status = "in_frontmatter"
                    case "in_frontmatter":
                        status = "after_frontmatter"
                    case "after_frontmatter":
                        pass
                continue

            if status == "after_frontmatter" or status == "before_frontmatter":
                content.append(line)

        return content

    def write_file(
        self, file_path: str, frontmatter: dict | None, content: list[str] | None
    ) -> None:
        if Path(file_path).is_absolute():
            raise ValueError("The file_path must be a relative path.")

        full_path = Path(self.base_folder) / file_path
        if not full_path.parent.exists():
            raise ValueError(
                f"The directory for the provided file_path '{file_path}' does not exist within the base folder."
            )

        if full_path.exists():
            raise ValueError(
                f"The file '{file_path}' already exists. Overwriting is not allowed."
            )

        lines = []

        if frontmatter:
            lines.append("---")
            frontmatter_str = yaml.safe_dump(frontmatter, sort_keys=False).strip()
            lines.extend(frontmatter_str.splitlines())
            lines.append("---")

        if content:
            lines.extend(content)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def __update_file(
        self, file_path: str, frontmatter: dict | None, content: list[str] | None
    ) -> None:
        """
        Once the frontmatter and the new content are ready, this method reconstructs the file by:
        - Starting with the frontmatter section, enclosed by "---" markers.
        - Appending the existing content of the file.
        - Adding any new content provided.
        """
        if Path(file_path).is_absolute():
            raise ValueError("The file_path must be a relative path.")

        full_path = Path(self.base_folder) / file_path
        if not full_path.exists() or not full_path.is_file():
            raise ValueError(
                f"The provided file_path '{file_path}' is not a valid file within the base folder."
            )

        lines = ["---"]

        if frontmatter:
            frontmatter_str = yaml.safe_dump(frontmatter, sort_keys=False).strip()
            lines.extend(frontmatter_str.splitlines())

        lines.append("---")

        current_lines = self.get_text_content(file_path)

        lines.extend(current_lines)

        if content:
            lines.extend(content)

        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def update_frontmatter(self, file_path: str, frontmatter: dict) -> None:
        original_fm = self.get_frontmatter(file_path)

        updated_fm = {**original_fm, **frontmatter}

        if original_fm == updated_fm:
            return

        self.__update_file(file_path, updated_fm, None)


def get_file_handler(base_folder: str = BASE_DIR) -> FileHandler:
    return FileHandler(base_folder=base_folder)
