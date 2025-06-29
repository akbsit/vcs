from abc import ABC
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GitUserConfig:
    name: str
    email: str


@dataclass
class Config(ABC):
    username: str
    exclude: List[str]


@dataclass
class BitbucketConfig(Config):
    password: str
    base_dir: str
    gitconfig: Optional[GitUserConfig] = None


@dataclass
class GithubConfig(Config):
    token: str
    base_dir: str
    gitconfig: Optional[GitUserConfig] = None


@dataclass
class GitlabConfig(Config):
    token: str
    base_dir: str
    gitconfig: Optional[GitUserConfig] = None
