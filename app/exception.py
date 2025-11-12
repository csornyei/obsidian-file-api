import json
from typing import Union


class CustomError(Exception):
    status_code: int
    message: str

    def __init__(self, status_code: int, message: Union[str, dict]):
        if isinstance(message, dict):
            message = json.dumps(message)

        super().__init__(message)

        self.status_code = status_code
        self.message = message

    def to_response(self):
        return {
            "status_code": self.status_code,
            "message": self.message,
        }
