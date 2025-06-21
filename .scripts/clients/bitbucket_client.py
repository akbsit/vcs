import logging
from typing import List, Dict

import requests

from .client import Client
from .configs import BitbucketConfig


class BitbucketClient(Client[BitbucketConfig]):
    @property
    def provider(self) -> str:
        return 'bitbucket'

    @property
    def account(self) -> str:
        return self.config.username

    def _fetch_repositories(self) -> List[Dict]:
        repositories = []

        workspaces = self._fetch_workspaces()
        for workspace in workspaces:
            logging.info('Fetching all accessible repositories...')

            url = f"https://api.bitbucket.org/2.0/repositories/{workspace}"

            while url:
                response = requests.get(url, auth=(self.config.username, self.config.password))

                if response.status_code != 200:
                    logging.warning(f"Failed to fetch repositories: {response.status_code}")
                    break

                data = response.json()
                repositories.extend(data['values'])
                url = data.get('next')

        return repositories

    def _repository_name(self, repository: Dict) -> str:
        return repository['full_name']

    def _has_commits(self, repository: Dict) -> bool:
        commits_url = repository['links']['commits']['href']
        response = requests.get(commits_url, auth=(self.config.username, self.config.password))

        if response.status_code != 200:
            logging.warning(f"Failed to fetch commits for {self._repository_name(repository)}")
            return False

        data = response.json()

        return bool(data.get('values'))

    def _get_clone_url(self, repository: Dict) -> str:
        return next(link['href'] for link in repository['links']['clone'] if link['name'] == 'ssh')

    def _fetch_workspaces(self) -> List[str]:
        logging.info('Fetching all accessible workspaces...')

        url = 'https://api.bitbucket.org/2.0/workspaces'

        workspaces = []

        while url:
            response = requests.get(url, auth=(self.config.username, self.config.password))

            if response.status_code != 200:
                logging.warning(f"Failed to fetch workspaces: {response.status_code}")
                break

            data = response.json()
            workspaces.extend([ws['slug'] for ws in data['values']])
            url = data.get('next')

        return workspaces
