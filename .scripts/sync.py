import json
import logging

from sync_bitbucket import sync_bitbucket
from sync_github import sync_github
from sync_gitlab import sync_gitlab
from utils.logger import setup_logger


def sync() -> None:
    try:
        setup_logger()

        config = json.load(open('config.json', encoding='utf-8'))

        logging.info('Loaded file config')

        sync_bitbucket(config.get('bitbucket'))
        sync_github(config.get('github'))
        sync_gitlab(config.get('gitlab'))
    except Exception as exception:
        logging.error(exception)


if __name__ == '__main__':
    sync()
