from typing import TypedDict

class ModMetadata(TypedDict):
    name: str
    uuid: str
    author: str
    description: str
    version: str
    tags: list[str]