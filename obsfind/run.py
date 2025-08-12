from pathlib import Path
from .outfmt import logger, console, df2csv
from .read_inputs import parse_args, validate_args, read_target_list, create_date_list
from .ephemeris import create_horizon_dataframe, limit_cuts, get_twilight_times
from .plotting import marker_list
from .create_output import make_elevation_charts_pdf, make_summary_charts_pdf


def main():
    args = parse_args()
    args = validate_args(args)
    target_list = read_target_list(args.target_file)
    logger.debug('Processed args and input file')
    date_list     = create_date_list(args.start_date, args.end_date)    
    twilight_list = get_twilight_times(args.mpc_code,date_list)

    # Create dataframe and apply cuts
    eph_df, twilight_list = create_horizon_dataframe(twilight_list, args.mpc_code, target_list)
    eph_cut, twilight_list = limit_cuts(eph_df, args.mag_limit, args.elevation_limit, args.time_visible_limit, twilight_list)

    df2csv(eph_cut,args.output_base,'eph.csv','Ephemeris')
        
    target_plot_info = marker_list(eph_cut.target.unique())
    
    night_summaries = make_elevation_charts_pdf(eph_cut, twilight_list, target_plot_info, args.elevation_limit, args.mpc_code, args.output_base)
    
    df2csv(night_summaries,args.output_base,'summary.csv','Summary')
    
    make_summary_charts_pdf(night_summaries,target_plot_info,args.output_base)
        
    console.print('yay')
    return

if __name__ == '__main__':
    main()
