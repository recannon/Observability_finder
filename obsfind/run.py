import argparse
import logging
from .outfmt import logger
from .read_inputs import parse_args, validate_args, read_target_list, create_date_list
from .ephemeris import create_horizon_dataframe, limit_cuts, get_twilight_times
from .plotting import elevation_chart, marker_list

def main():
    args = parse_args()
    args = validate_args(args)
    target_list = read_target_list(args.target_file)
    logger.debug('Processed args and input file')
    date_list     = create_date_list(args.start_date, args.end_date)    
    twilight_list = get_twilight_times(args.mpc_code,date_list)

    # Create dataframe and apply cuts
    eph_df = create_horizon_dataframe(twilight_list, args.mpc_code, target_list)
    eph_cut = limit_cuts(eph_df, args.mag_limit, args.elevation_limit, args.time_visible_limit)

    # Save csv in output file
    eph_cut.to_csv(args.csv_output)
    
    target_plot_info = marker_list(eph_cut.target.unique())
        
    for i,row in twilight_list.iterrows():
        
        mask = (eph_cut['datetime'] >= row['sun_set']) & (eph_cut['datetime'] <= row['sun_rise'])
        eph_night = eph_cut[mask]        
        
        elevation_chart(row,eph_night,target_plot_info,args.elevation_limit,show_plot=False,fig_path=f'.')
        
    
    print('yay')
    return

if __name__ == '__main__':
    main()
