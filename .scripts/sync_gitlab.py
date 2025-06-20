import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

GIT_ERROR = 'error'
GIT_FETCHED = 'fetched'
GIT_CLONED = 'cloned'


@dataclass
class GitlabConfig:
    username: str
    token: str
    base_dir: str


def fetch_repositories(config: GitlabConfig) -> List[Dict]:
    logging.info('Fetching all accessible repositories...')

    repositories = []
    page = 1
    per_page = 100

    while True:
        url = f"https://gitlab.com/api/v4/projects?membership=true&per_page={per_page}&page={page}"

        response = requests.get(url, headers={'PRIVATE-TOKEN': config.token})

        if response.status_code != 200:
            logging.warning(f"Failed to fetch repositories: {response.status_code}")
            break

        page_repositories = response.json()

        if not page_repositories:
            break

        repositories.extend(page_repositories)
        page += 1

    return repositories


def repository_has_commits(repository: Dict, config: GitlabConfig) -> bool:
    repository_id = repository['id']

    url = f"https://gitlab.com/api/v4/projects/{repository_id}/repository/commits"

    response = requests.get(url, headers={'PRIVATE-TOKEN': config.token})

    if response.status_code != 200:
        return False

    data = response.json()

    return bool(data)


def clone_or_fetch_repository(repository: Dict, config: GitlabConfig) -> str:
    clone_url = repository['ssh_url_to_repo']

    if not clone_url:
        logging.warning(f"Failed {clone_url} not provided")
        return GIT_ERROR

    repository_name = repository['path_with_namespace']

    local_path = os.path.join(f"./gitlab/{config.base_dir}", repository_name)
    os.makedirs(local_path, exist_ok=True)

    if os.path.exists(local_path) and os.listdir(local_path):
        logging.info(f"[{repository_name}] Fetching...")

        if repository_has_commits(repository, config):
            subprocess.run(['git', '-C', local_path, 'fetch'], check=True)

        return GIT_FETCHED
    else:
        logging.info(f"[{repository_name}] Cloning...")

        subprocess.run(['git', 'clone', clone_url, local_path], check=True)

        return GIT_CLONED


def process_item(item: Dict[str, Any]) -> None:
    logging.info(f"Processing gitlab account: {item.get('username')}")

    config = GitlabConfig(
        username=item.get('username'),
        token=item.get('token'),
        base_dir=item.get('base_dir')
    )

    start_time = datetime.now()

    errors = []
    fetched = []
    cloned = []

    repositories = fetch_repositories(config)

    for repository in repositories:
        result = clone_or_fetch_repository(repository, config)
        full_name = f"{repository['path_with_namespace']}"

        if result == GIT_ERROR:
            errors.append(full_name)
        elif result == GIT_FETCHED:
            fetched.append(full_name)
        elif result == GIT_CLONED:
            cloned.append(full_name)

    logging.info('Processing gitlab account completed')
    logging.info(f"🟢 Fetched: {len(fetched)}")
    logging.info(f"🆕 Cloned: {len(cloned)}")
    logging.info(f"❌ Errors: {len(errors)}")

    if errors:
        logging.warning('Repositories with errors:')
        for name in errors: logging.warning(f" - {name}")

    duration = (datetime.now() - start_time).total_seconds()
    logging.info(f"⏱ Total time: {duration:.2f}s")


def sync_gitlab(config_list: Optional[List[Dict[str, Any]]]) -> None:
    if config_list is None:
        logging.warning('Gitlab configs not found')
        return

    for config in config_list: process_item(config)
