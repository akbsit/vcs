import argparse

from command import process

if __name__ == '__main__':
    console = argparse.ArgumentParser()
    console.add_argument('--provider')

    args = console.parse_args()

    process(lambda client: client.git(), args.provider)
