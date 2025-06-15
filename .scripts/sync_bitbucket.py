import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

GIT_ERROR = 'error'
GIT_PULLED = 'pulled'
GIT_CLONED = 'cloned'


@dataclass
class BitbucketConfig:
    username: str
    password: str
    base_dir: str


def fetch_workspaces(config: BitbucketConfig) -> List[str]:
    logging.info('Fetching all accessible workspaces...')

    url = 'https://api.bitbucket.org/2.0/workspaces'

    workspaces = []

    while url:
        response = requests.get(url, auth=(config.username, config.password))

        if response.status_code != 200:
            logging.warning(f"Failed to fetch workspaces: {response.status_code}")
            break

        data = response.json()
        workspaces.extend([ws['slug'] for ws in data['values']])
        url = data.get('next')

    return workspaces


def fetch_repositories(workspace: str, config: BitbucketConfig) -> List[Dict]:
    logging.info('Fetching all accessible repositories...')

    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=100"

    repositories = []

    while url:
        response = requests.get(url, auth=(config.username, config.password))

        if response.status_code != 200:
            logging.warning(f"Failed to fetch repositories: {response.status_code}")
            break

        data = response.json()
        repositories.extend(data['values'])
        url = data.get('next')

    return repositories


def repository_has_commits(repository: Dict, config: BitbucketConfig) -> bool:
    commits_url = repository['links']['commits']['href']
    response = requests.get(commits_url, auth=(config.username, config.password))

    if response.status_code != 200:
        logging.warning(f"Failed to fetch commits for {repository['full_name']}")
        return False

    data = response.json()

    return bool(data.get('values'))


def clone_or_pull_repository(repository: Dict, config: BitbucketConfig) -> str:
    clone_url = next(link['href'] for link in repository['links']['clone'] if link['name'] == 'ssh')
    workspace = repository['workspace']['slug']

    if not clone_url or not workspace:
        logging.warning(f"Failed {clone_url} or {workspace} not provided")
        return GIT_ERROR

    repository_name = repository['name']

    local_path = os.path.join(f"./bitbucket/{config.base_dir}", workspace, repository_name)
    os.makedirs(local_path, exist_ok=True)

    if os.path.exists(local_path) and os.listdir(local_path):
        logging.info(f"[{workspace}/{repository_name}] Pulling...")

        if repository_has_commits(repository, config):
            subprocess.run(['git', '-C', local_path, 'fetch'], check=True)
            subprocess.run(['git', '-C', local_path, 'pull'], check=True)

        return GIT_PULLED
    else:
        logging.info(f"[{workspace}/{repository_name}] Cloning...")

        subprocess.run(['git', 'clone', clone_url, local_path], check=True)

        return GIT_CLONED


def process_item(item: Dict[str, Any]) -> None:
    logging.info(f"Processing bitbucket account: {item.get('username')}")

    config = BitbucketConfig(
        username=item.get('username'),
        password=item.get('password'),
        base_dir=item.get('base_dir')
    )

    start_time = datetime.now()

    errors = []
    pulled = []
    cloned = []

    workspaces = fetch_workspaces(config)

    for workspace in workspaces:
        repositories = fetch_repositories(workspace, config)

        for repository in repositories:
            result = clone_or_pull_repository(repository, config)
            full_name = f"{workspace}/{repository['name']}"

            if result == GIT_ERROR:
                errors.append(full_name)
            elif result == GIT_PULLED:
                pulled.append(full_name)
            elif result == GIT_CLONED:
                cloned.append(full_name)

    logging.info('Processing bitbucket account completed')
    logging.info(f"🟢 Pulled: {len(pulled)}")
    logging.info(f"🆕 Cloned: {len(cloned)}")
    logging.info(f"❌ Errors: {len(errors)}")

    if errors:
        logging.warning('Repositories with errors:')
        for name in errors: logging.warning(f" - {name}")

    duration = (datetime.now() - start_time).total_seconds()
    logging.info(f"⏱ Total time: {duration:.2f}s")


def sync_bitbucket(config_list: Optional[List[Dict[str, Any]]]) -> None:
    if config_list is None:
        logging.warning('Bitbucket configs not found')
        return

    for config in config_list: process_item(config)
