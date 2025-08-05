import argparse
import logging
from code.outfmt import logger
from code.read_inputs import parse_args, validate_args, read_target_list, create_date_list
from code.obs_find import call_horizons, limit_cuts

#===Functions for parsing args below this point===
def main():
    args = parse_args()
    args = validate_args(args)
    target_list = read_target_list(args.target_file)
    date_list   = create_date_list(args.start_date, args.end_date)    

    eph = call_horizons(args.start_date, args.end_date, args.mpc_code, target_list)
    eph.to_csv(args.csv_output)
    
    # csv = limit_cuts(csv, limits)
    
    # return csv
    
    # for day in date_list:
    #     twilight_times = twilight_times()
    #     plot()
    #     create_summary()
    #     latex()
        
    return

if __name__ == '__main__':
    main()
