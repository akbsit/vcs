import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generic, TypeVar, List, Dict

from .configs import Config, GitUserConfig

T = TypeVar('T', bound=Config)

GIT_EXCLUDED = 'excluded'
GIT_ERROR = 'error'
GIT_FETCHED = 'fetched'
GIT_CLONED = 'cloned'


class Client(ABC, Generic[T]):
    def __init__(self, config: T) -> None:
        self.config = config

    @property
    def provider(self) -> str:
        return 'unknown'

    @property
    def account(self) -> str:
        return 'unknown'

    @abstractmethod
    def _fetch_repositories(self) -> List[Dict]:
        pass

    @abstractmethod
    def _repository_name(self, repository: Dict) -> str:
        pass

    @abstractmethod
    def _get_clone_url(self, repository: Dict) -> str:
        pass

    @abstractmethod
    def _has_commits(self, repository: Dict) -> bool:
        pass

    def sync(self) -> None:
        self._log_start()

        start_time = datetime.now()
        excluded, errors, fetched, cloned = [], [], [], []
        repositories = self._fetch_repositories()

        for repository in repositories:
            repository_name = self._repository_name(repository)

            if repository_name in self.config.exclude:
                logging.info(f"[{repository_name}] Skipped (in exclude list)")
                excluded.append(repository_name)
                continue

            result = self._clone_or_fetch(
                repository_name,
                self._get_clone_url(repository),
                self._get_local_path(repository),
                self._has_commits(repository),
            )

            if result == GIT_ERROR:
                errors.append(repository_name)
            elif result == GIT_FETCHED:
                fetched.append(repository_name)
            elif result == GIT_CLONED:
                cloned.append(repository_name)

        logging.info(f"Processing {self.provider} account completed")
        logging.info(f"🙈 Excluded: {len(excluded)}")
        logging.info(f"🟢 Fetched: {len(fetched)}")
        logging.info(f"🆕 Cloned: {len(cloned)}")
        logging.info(f"❌ Errors: {len(errors)}")

        if errors:
            logging.warning('Repositories with errors:')
            for name in errors: logging.warning(f" - {name}")

        self._log_end(start_time)

    def git(self) -> None:
        self._log_start()

        gitconfig = self.config.gitconfig

        if gitconfig is None:
            logging.info('Skipped (git configuration not found)')
            return

        start_time = datetime.now()
        repositories = self._fetch_repositories()

        for repository in repositories:
            repository_name = self._repository_name(repository)

            if repository_name in self.config.exclude:
                logging.info(f"[{repository_name}] Skipped (in exclude list)")
                continue

            self._update_gitconfig(
                repository_name,
                self._get_local_path(repository),
                gitconfig
            )

        self._log_end(start_time)

    def _get_local_path(self, repository: Dict) -> str:
        return os.path.join(
            './',
            self.provider,
            self.config.base_dir,
            self._repository_name(repository),
        )

    def _log_start(self) -> None:
        logging.info(f"Processing {self.provider}")
        logging.info(f"Account {self.account}")

    @staticmethod
    def _log_end(start_time: datetime) -> None:
        duration = (datetime.now() - start_time).total_seconds()
        logging.info(f"⏱ Total time: {duration:.2f}s")

    @staticmethod
    def _clone_or_fetch(repository_name: str, clone_url: str, local_path: str, has_commits: bool) -> str:
        try:
            os.makedirs(local_path, exist_ok=True)

            if os.path.exists(local_path) and os.listdir(local_path):
                logging.info(f"[{repository_name}] Fetching...")

                if has_commits:
                    subprocess.run(['git', '-C', local_path, 'fetch'], check=True)

                return GIT_FETCHED
            else:
                logging.info(f"[{repository_name}] Cloning...")

                subprocess.run(['git', 'clone', clone_url, local_path], check=True)

                return GIT_CLONED
        except subprocess.CalledProcessError as exception:
            logging.error(f"[{repository_name}] Git command failed: {exception}")
        except Exception as exception:
            logging.error(f"[{repository_name}] Unexpected error: {exception}")

        return GIT_ERROR

    @staticmethod
    def _update_gitconfig(repository_name: str, local_path: str, gitconfig: GitUserConfig) -> None:
        if not os.path.exists(os.path.join(local_path, '.git')):
            return

        try:
            subprocess.run(['git', '-C', local_path, 'config', 'user.name', gitconfig.name], check=True)
            subprocess.run(['git', '-C', local_path, 'config', 'user.email', gitconfig.email], check=True)

            logging.info(f"[{repository_name}] Set local git config (user.name / user.email)")
        except subprocess.CalledProcessError as exception:
            logging.error(f"[{repository_name}] Git command failed: {exception}")
        except Exception as exception:
            logging.error(f"[{repository_name}] Unexpected error: {exception}")
