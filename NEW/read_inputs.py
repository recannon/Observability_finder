import argparse
import logging
from .outfmt import logger
from pathlib import Path

DEFAULT_MPC_CODE = '809'
DEFAULT_TARGET_FILE = './target_list.txt'
DEFAULT_OUTPUT_CSV = './output.csv'

def parse_args():
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='',
                                     epilog='')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Toggle flag for plotting')

    date_group = parser.add_argument_group('Input dates')
    date_group.add_argument('Start Date', type=-str, metavar='start_date',
                            help='Initial date to check observability from')
    date_group.add_argument('End Date', type=str, metavar='end_date',
                            help='Final date to check observability (inclusive)')

    mpc_group = parser.add_argument_group('Optional MPC code input: https://www.minorplanetcenter.net/iau/lists/ObsCodes.html')
    mpc_group.add_argument('-mpc', '--mpc-code', type=str,
                           help=f'Location for observation site: default = {DEFAULT_MPC_CODE}')

    file_group = parser.add_argument_group('Optional file names')
    file_group.add_argument('-targ', '--target-list', type=Path,
                            help=f'Name of the target list file. Default: {DEFAULT_TARGET_FILE}')
    file_group.add_argument('-csv', '--csv-output', type=Path,
                            help=f'Name of the output csv file. Default: {DEFAULT_OUTPUT_CSV}')

    limit_group = parser.add_argument_group('Optional inputs for limits')
    limit_group.add_argument_group('-mag', '--mag-limit', type=str,
                                   help='Upper limit of magnitude to be classed as visible [float]')
    limit_group.add_argument_group('-elv', '--elevation', type=str,
                                   help='Minimum elevation to be observable [float]')
    limit_group.add_argument_group('-tvis', '--time-visible', type=str,
                                   help='Minimum time visible per night to be included in observable list [float]')
    
    return parser.parse_args()

def validate_args(args):
    
    if args.verbose:
        logger.setLevel(logging.debug)

    return args

def read_target_list(fname):
    return target_list

def create_date_list(args):
    return date_list