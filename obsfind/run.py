import argparse
import logging
from .outfmt import logger
from .read_inputs import parse_args, validate_args, read_target_list, create_date_list
from .horizons_call import create_horizon_dataframe, limit_cuts

def main():
    args = parse_args()
    args = validate_args(args)
    target_list = read_target_list(args.target_file)
    logger.debug('Processed args and input file')
    date_list   = create_date_list(args.start_date, args.end_date)    

    # Create dataframe and apply cuts
    eph_df = create_horizon_dataframe(args.start_date, args.end_date, args.mpc_code, target_list)
    eph_cut = limit_cuts(eph_df, args.mag_limit, args.elevation_limit)

    # Save csv in output file
    eph_cut.to_csv(args.csv_output)
    
    # return csv
    
    # for day in date_list:
    #     twilight_times = twilight_times()
    #     plot()
    #     create_summary()
    #     latex()
    
    print('yay')
    return

if __name__ == '__main__':
    main()
