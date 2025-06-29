import json
import logging
from typing import Callable, Any

from clients.bitbucket_client import BitbucketClient
from clients.configs import BitbucketConfig, GithubConfig, GitlabConfig, GitUserConfig
from clients.github_client import GithubClient
from clients.gitlab_client import GitlabClient
from utils.logger import setup_logger


def process(action: Callable[[Any], None], provider: str) -> None:
    setup_logger()

    try:
        config = json.load(open('config.json', encoding='utf-8'))

        logging.info('Loaded file config')

        def prepare_config(cfg: dict, cls):
            gitconfig = cfg.get('gitconfig')

            if gitconfig: cfg['gitconfig'] = GitUserConfig(**gitconfig)

            return cls(**cfg)

        if provider is None or provider == 'bitbucket':
            for config_item in config.get('bitbucket'):
                action(BitbucketClient(prepare_config(config_item, BitbucketConfig)))

        if provider is None or provider == 'github':
            for config_item in config.get('github'):
                action(GithubClient(prepare_config(config_item, GithubConfig)))

        if provider is None or provider == 'gitlab':
            for config_item in config.get('gitlab'):
                action(GitlabClient(prepare_config(config_item, GitlabConfig)))
    except Exception as exception:
        logging.error(exception)
