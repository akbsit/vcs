import logging
from typing import List, Dict

import requests

from .client import Client
from .configs import GithubConfig


class GithubClient(Client[GithubConfig]):
    @property
    def provider(self) -> str:
        return 'github'

    @property
    def account(self) -> str:
        return self.config.username

    def _fetch_repositories(self) -> List[Dict]:
        logging.info('Fetching all accessible repositories...')

        repositories = []
        page = 1
        per_page = 100

        while True:
            url = f"https://api.github.com/user/repos?per_page={per_page}&page={page}"

            response = requests.get(url, headers={
                'Authorization': f"token {self.config.token}"
            })

            if response.status_code != 200:
                logging.warning(f"Failed to fetch repositories: {response.status_code}")
                break

            page_repositories = response.json()

            if not page_repositories:
                break

            repositories.extend(page_repositories)
            page += 1

        return repositories

    def _repository_name(self, repository: Dict) -> str:
        return repository['full_name']

    def _get_clone_url(self, repository: Dict) -> str:
        return repository['ssh_url']

    def _has_commits(self, repository: Dict) -> bool:
        url = f"https://api.github.com/repos/{self._repository_name(repository)}/commits"

        response = requests.get(url, headers={
            'Authorization': f"token {self.config.token}"
        })

        if response.status_code != 200:
            return False

        return True
