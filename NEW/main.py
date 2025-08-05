import argparse
import logging
from .outfmt import logger
from .read_inputs import parse_args, validate_args, read_target_list, create_date_list
from .obs_find import call_horizons, limit_cuts

#===Functions for parsing args below this point===


def main():
    args = parse_args()
    args = validate_args(args)
    
    date_list = create_date_list(args)
    
    fname,limits,days = *args
    
    target_list = read_target_list(fname)
    
    csv = call_horizons(target_list,*args)
    
    csv = limit_cuts(csv,limits)
    
    return csv
    
    for day in date_list:
        twilight_times = twilight_times()
        plot()
        create_summary()
        latex()
        
    
    return

if __name__ == '__main__':
    main()
