import argparse
import logging
from .outfmt import logger
from pathlib import Path
import numpy as np
from astropy.time import Time, TimeDelta
from astroquery.mpc import MPC as MPC_query
from .outfmt import logger, error_exit


# Configure default parameters
DEFAULT_TARGET_FILE = './target_list.txt'
DEFAULT_OUTPUT_CSV  = './output.csv'
DEFAULT_MPC_CODE    = '809'      # Observatory MPC code
DEFAULT_ELEVATION_LIMIT = 30     # Minimum elevation angle (degrees)
DEFAULT_TIME_VISIBLE    = 1      # Minimum time visible (hours)
DEFAULT_MAG_LIMIT       = 25     # Maximum magnitude limit


def parse_args() -> argparse.Namespace:
    '''Parse command-line arguments.'''
    parser = argparse.ArgumentParser(description='',
                                     epilog='')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output (sets log level to DEBUG)')
    parser.add_argument('-p', '--plot', action='store_true',
                        help='Toggle flag for plotting')

    date_group = parser.add_argument_group('Input dates. Format: YYYY-MM-DD')
    date_group.add_argument('start_date', type=str,
                            help='Initial date to check observability from')
    date_group.add_argument('end_date', type=str,
                            help='Final date to check observability (inclusive)')

    mpc_group = parser.add_argument_group('Optional MPC code input: https://www.minorplanetcenter.net/iau/lists/ObsCodes.html')
    mpc_group.add_argument('-mpc', '--mpc-code', type=str,
                           help=f'Location for observation site: default = {DEFAULT_MPC_CODE}')

    file_group = parser.add_argument_group('Optional file names')
    file_group.add_argument('-targ', '--target-file', type=Path, 
                            help=f'Name of the target list file. Default: {DEFAULT_TARGET_FILE}')
    file_group.add_argument('-csv', '--csv-output', type=Path,
                            help=f'Name of the output csv file. Default: {DEFAULT_OUTPUT_CSV}')

    limit_group = parser.add_argument_group('Optional inputs for limits')
    limit_group.add_argument('-mag', '--mag-limit', type=str,
                                   help=f'Upper limit of magnitude to be classed as visible [float]. Defautlt: {DEFAULT_MAG_LIMIT}')
    limit_group.add_argument('-elv', '--elevation-limit', type=str,
                                   help=f'Minimum elevation to be observable [float]. Default: {DEFAULT_ELEVATION_LIMIT}')
    limit_group.add_argument('-air', '--airmass-limit', type=str,
                                   help=f'Maximum airmass to be observable [float]. Use this only if no elevation is specified.')
    limit_group.add_argument('-tvis', '--time-visible-limit', type=str,
                                   help=f'Minimum time visible per night to be included in observable list [float]. Default: {DEFAULT_TIME_VISIBLE}')
    
    return parser.parse_args()


def check_type(name:str, val:str, req_type:type):
    '''
    '''
    try: 
        val = req_type(val)
    except:
        error_exit(f'{name} value cannot be read into a {req_type}')
    return val


def validate_args(args:argparse.Namespace) -> argparse.Namespace:
    '''
    '''
    # Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    # Check dates format
    try:
        args.start_date = Time(args.start_date, format='iso')
        args.end_date   = Time(args.end_date, format='iso')
    except:
        error_exit('Cannot convert dates to astropy.time.Time objects. Check time input')

    # Check mag and apply default value if none
    if not args.mag_limit:
        args.mag_limit = DEFAULT_MAG_LIMIT
    else:
        args.mag_limit = check_type('--mag-limit', args.mag_limit, float)

    # Check time and apply default value if none
    if not args.time_visible_limit:
        args.time_visible_limit = DEFAULT_TIME_VISIBLE
    else:
        args.time_visible_limit = check_type('--time-visible', args.time_visible_limit, float)
        if args.time_visible_limit <= 0:
            error_exit('--time-visible must be positive') 

    # Check airmass/elevation
    if not args.airmass_limit and not args.elevation_limit:
        args.elevation_limit = DEFAULT_ELEVATION_LIMIT
    elif args.airmass_limit and args.elevation_limit:
        error_exit('Cannot accept separate limits for airmass and elevation')        
    elif args.elevation_limit:
        args.elevation_limit = check_type('--elevation-limit', args.elevation_limit, float)
        if args.elevation_limit < 0:
            error_exit('--elevation-limit must be positive')
        # To avoid dividing by 0
        elif args.elevation_limit == 0:
            args.elevation_limit == 0.001 
    elif args.airmass_limit:
        args.airmass_limit = check_type('--airmass-liimit', args.airmass_limit, float)
        if args.airmass_limit < 1:
            error_exit('--airmass-limit must be greater than 1')
        args.elevation_limit = 90 - np.rad2deg(np.arccos(1 / args.airmass_limit))
        logger.debug(f'Elevation limit set to {args.elevation_limit:.2f} degrees')
    else:
        error_exit('This message should not appear so it is time to cry')

    # Check MPC codes
    if not args.mpc_code:
        args.mpc_code = DEFAULT_MPC_CODE
    elif len(args.mpc_code) != 3:
        error_exit('Input MPC code does not have 3 characters')

    obs_sites = MPC_query.get_observatory_codes()
    logger.info(f"Selected observatory: {obs_sites[obs_sites['Code']==args.mpc_code]['Name'].value[0]}")

    # Check if input file exists
    if not args.target_file:
        args.target_file = Path(DEFAULT_TARGET_FILE).resolve()
    if not args.target_file.is_file():
        error_exit(f'Cannot find {args.target_file}')
        
    # Check if output file exists
    if not args.csv_output:
        args.csv_output = Path(DEFAULT_OUTPUT_CSV).resolve()
         
    return args


def read_target_list(fname:Path) -> list[str]:
    '''
    Read input target list file.
    fname : input file (Path)
    ----
    Return : target list (array)

    '''
    with open(fname,'r') as f:
        # Read all targets in file avoiding lines starting with '#'
        target_list = [l.strip() for l in f.readlines() if l.strip()[0]!='#']
    return target_list


def create_date_list(start_date:Time, end_date:Time) -> list[Time]:
    '''
    '''
    # Number of days to scan
    len_days = int((end_date - start_date).jd)
    date_list = [start_date + TimeDelta(d,format='jd') for d in range(0,len_days+1)]
    return date_list