from pathlib import Path


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
