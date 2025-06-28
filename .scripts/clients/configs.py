from abc import ABC
from dataclasses import dataclass
from typing import List


@dataclass
class Config(ABC):
    username: str
    exclude: List[str]


@dataclass
class BitbucketConfig(Config):
    password: str
    base_dir: str


@dataclass
class GithubConfig(Config):
    token: str
    base_dir: str


@dataclass
class GitlabConfig(Config):
    token: str
    base_dir: str
