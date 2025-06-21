import logging
from typing import List, Dict

import requests

from .client import Client
from .configs import GitlabConfig


class GitlabClient(Client[GitlabConfig]):
    @property
    def provider(self) -> str:
        return 'gitlab'

    @property
    def account(self) -> str:
        return self.config.username

    def _fetch_repositories(self) -> List[Dict]:
        logging.info('Fetching all accessible repositories...')

        repositories = []
        page = 1
        per_page = 100

        while True:
            url = f"https://gitlab.com/api/v4/projects?membership=true&per_page={per_page}&page={page}"

            response = requests.get(url, headers={'PRIVATE-TOKEN': self.config.token})

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
        return repository['path_with_namespace']

    def _get_clone_url(self, repository: Dict) -> str:
        return repository['ssh_url_to_repo']

    def _has_commits(self, repository: Dict) -> bool:
        repository_id = repository['id']

        url = f"https://gitlab.com/api/v4/projects/{repository_id}/repository/commits"

        response = requests.get(url, headers={'PRIVATE-TOKEN': self.config.token})

        if response.status_code != 200:
            return False

        data = response.json()

        return bool(data)
