from command import process

if __name__ == '__main__':
    process(lambda client: client.git())
