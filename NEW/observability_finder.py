import argparse
import logging

def observability_finder():
    return

#===Functions for parsing args below this point===
def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='',
                                     epilog='')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')

    return parser.parse_args()

def main():
    args = parse_args()
    observability_finder()
    return

if __name__ == '__main__':
    main()
