import json
import logging

from clients.bitbucket_client import BitbucketClient
from clients.configs import BitbucketConfig, GithubConfig, GitlabConfig
from clients.github_client import GithubClient
from clients.gitlab_client import GitlabClient
from utils.logger import setup_logger


def sync() -> None:
    setup_logger()

    try:
        config = json.load(open('config.json', encoding='utf-8'))

        logging.info('Loaded file config')

        bitbucket_configs = config.get('bitbucket')
        for config_item in bitbucket_configs:
            BitbucketClient(BitbucketConfig(**config_item)).sync()

        github_configs = config.get('github')
        for config_item in github_configs:
            GithubClient(GithubConfig(**config_item)).sync()

        gitlab_configs = config.get('gitlab')
        for config_item in gitlab_configs:
            GitlabClient(GitlabConfig(**config_item)).sync()
    except Exception as exception:
        logging.error(exception)


if __name__ == '__main__':
    sync()
