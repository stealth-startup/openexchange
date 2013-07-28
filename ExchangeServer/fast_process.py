__author__ = 'Rex'

if __name__ == "__main__":
    from exchange_server import process_next_block

    while process_next_block():
        print '\n' + '='*30 + '\n'