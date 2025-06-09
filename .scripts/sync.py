import json
import logging
import os
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

logging_format = "%(asctime)s [%(levelname)s] %(message)s"

logging.basicConfig(level=logging.INFO, format=logging_format)
logging.basicConfig(level=logging.ERROR, format=logging_format)
logging.basicConfig(level=logging.WARNING, format=logging_format)

GIT_ERROR = 'error'
GIT_PULLED = 'pulled'
GIT_CLONED = 'cloned'


def fetch_bitbucket_workspaces(username: str, password: str) -> List[str]:
    logging.info('Fetching all accessible workspaces...')

    url = 'https://api.bitbucket.org/2.0/workspaces'

    workspaces = []

    while url:
        response = requests.get(url, auth=(username, password))

        if response.status_code != 200:
            logging.warning(f"Failed to fetch workspaces: {response.status_code}")
            break

        data = response.json()
        workspaces.extend([ws['slug'] for ws in data['values']])
        url = data.get('next')

    return workspaces


def fetch_bitbucket_repositories(workspace: str, username: str, password: str) -> List[Dict]:
    logging.info('Fetching all accessible repositories...')

    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}?pagelen=100"

    repositories = []

    while url:
        response = requests.get(url, auth=(username, password))

        if response.status_code != 200:
            logging.warning(f"Failed to fetch repositories: {response.status_code}")
            break

        data = response.json()
        repositories.extend(data['values'])
        url = data.get('next')

    return repositories


def clone_or_pull_bitbucket_repository(repository: Dict) -> str:
    clone_url = next(link['href'] for link in repository['links']['clone'] if link['name'] == 'ssh')
    workspace = repository['workspace']['slug']

    if not clone_url or not workspace:
        logging.warning(f"Failed {clone_url} or {workspace} not provided")
        return GIT_ERROR

    repository_name = repository['name']

    local_path = os.path.join('./bitbucket', workspace, repository_name)
    os.makedirs(local_path, exist_ok=True)

    if os.path.exists(local_path) and os.listdir(local_path):
        logging.info(f"[{workspace}/{repository_name}] Pulling...")

        subprocess.run(['git', '-C', local_path, 'pull'], check=True)

        return GIT_PULLED
    else:
        logging.info(f"[{workspace}/{repository_name}] Cloning...")

        subprocess.run(['git', 'clone', clone_url, local_path], check=True)

        return GIT_CLONED


def process_bitbucket_item(item: Dict[str, Any]) -> None:
    logging.info(f"Processing bitbucket account: {item.get('username')}")

    start_time = datetime.now()

    errors = []
    pulled = []
    cloned = []

    workspaces = fetch_bitbucket_workspaces(item.get('username'), item.get('password'))

    for workspace in workspaces:
        repositories = fetch_bitbucket_repositories(workspace, item.get('username'), item.get('password'))

        for repository in repositories:
            result = clone_or_pull_bitbucket_repository(repository)
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

    for config in config_list: process_bitbucket_item(config)


def sync() -> None:
    try:
        config = json.load(open('config.json', encoding='utf-8'))

        logging.info('Loaded file config')

        sync_bitbucket(config.get('bitbucket'))
    except Exception as exception:
        logging.error(exception)


if __name__ == '__main__':
    sync()
