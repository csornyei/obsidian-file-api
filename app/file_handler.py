from pathlib import Path
from typing import Literal

import yaml

from .env import BASE_DIR
from .exception import CustomError


class FileHandler:
    def __init__(self, base_folder: str):
        path = Path(base_folder)
        if not path.exists() or not path.is_dir():
            raise ValueError(
                f"The provided base_folder '{base_folder}' is not a valid directory."
            )

        self.base_folder = base_folder

    def __raise_absolute_path_error(self, path: str) -> bool:
        if Path(path).is_absolute():
            raise CustomError(
                status_code=400, message="The path must be a relative path."
            )
        return False

    def __raise_not_exist_error(self, path: str) -> bool:
        full_path = Path(self.base_folder) / path
        if not full_path.exists():
            raise CustomError(
                status_code=404,
                message=f"The provided path '{path}' does not exist within the base folder.",
            )
        return False

    def __raise_not_file_error(self, path: str) -> bool:
        full_path = Path(self.base_folder) / path
        if not full_path.is_file():
            raise CustomError(
                status_code=404,
                message=f"The provided file_path '{path}' is not a valid file within the base folder.",
            )
        return False

    def __raise_not_dir_error(self, path: str) -> bool:
        full_path = Path(self.base_folder) / path
        if not full_path.is_dir():
            raise CustomError(
                status_code=404,
                message=f"The provided dir_path '{path}' is not a valid directory within the base folder.",
            )
        return False

    def __filter(self, items: list[Path]) -> list[Path]:
        items = filter(
            lambda x: not any(part.startswith(".") for part in x.parts), items
        )
        items = map(lambda x: x.as_posix(), items)
        return list(items)

    def list_files(self, file_path: str, all: bool = False) -> list[str]:
        self.__raise_absolute_path_error(file_path)
        self.__raise_not_exist_error(file_path)
        self.__raise_not_dir_error(file_path)

        full_path = Path(self.base_folder) / file_path

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
        self.__raise_absolute_path_error(dir_path)
        self.__raise_not_exist_error(dir_path)
        self.__raise_not_dir_error(dir_path)

        full_path = Path(self.base_folder) / dir_path

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
        self.__raise_absolute_path_error(file_path)
        self.__raise_not_exist_error(file_path)
        self.__raise_not_file_error(file_path)

        if not file_path.endswith(".md"):
            raise CustomError(
                status_code=400,
                message="Only markdown (.md) files can be read.",
            )

        full_path = Path(self.base_folder) / file_path

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
        self.__raise_absolute_path_error(file_path)

        full_path = Path(self.base_folder) / file_path
        if not full_path.parent.exists():
            raise CustomError(
                status_code=404,
                message=f"The directory '{Path(file_path).parent}' does not exist within the base folder.",
            )

        if full_path.exists():
            raise CustomError(
                status_code=400,
                message=f"The file '{file_path}' already exists. Overwriting is not allowed.",
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
        self.__raise_absolute_path_error(file_path)
        self.__raise_not_exist_error(file_path)
        self.__raise_not_file_error(file_path)

        full_path = Path(self.base_folder) / file_path

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

    def update_content(self, file_path: str, content: list[str]) -> None:
        original_fm = self.get_frontmatter(file_path)

        self.__update_file(file_path, original_fm, content)


def get_file_handler(base_folder: str = BASE_DIR) -> FileHandler:
    return FileHandler(base_folder=base_folder)
