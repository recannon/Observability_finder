import argparse
import itertools
import logging
import shutil
import subprocess
from pathlib import Path
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.time import Time, TimeDelta
import astropy.units as u
from astroquery.jplhorizons import Horizons
from astroquery.mpc import MPC as MPC_query
from rich.progress import Progress
from observability_funcs import twilight_times, figures, pdfs
from observability_funcs.outfmt import console, logger, error_exit

#Configure default parameters
DEFAULT_MPC_CODE = '809'         #Observatory MPC code
DEFAULT_ELEVATION_LIMIT = 30     #Minimum elevation angle (degrees)
DEFAULT_TIME_VISIBLE = 1         #Minimum time visible (hours)
DEFAULT_MAG_LIMIT = 25           #Maximum magnitude limit

def marker_list(target_names):
    #Marker set up now that number of targets that will be plotted is known
    marker_opt = ['o','v','s','X','<','P','*','h','>','H','+','^','x','D']
    colour_opt = ['b','g','r','c','m','y']
    markers    = list(itertools.product(marker_opt, colour_opt)) #List of unique tuples
    markerlist = [pair[0] for pair in markers[:len(target_names)]]
    colourlist = [pair[1] for pair in markers[:len(target_names)]]
    target_list_data = {'targets'  : target_names,
                        'markers'  : markerlist,
                        'colours'  : colourlist}
    target_plot_info = pd.DataFrame(data = target_list_data)

    return target_plot_info

def observability_finder(start_date,end_date,MPC_code,limits,target_file,summary_file):

    #Read targets
    with open(target_file,'r') as f:
        target_list = [l.strip() for l in f.readlines() if l.strip()[0]!='#']

    #Unpack limits for readability
    mag_limit, time_visible_limit, elevation_limit = limits

    #Number of days to scan
    len_days = int((end_date-start_date).jd)
    dates_list = [start_date + TimeDelta(d,format='jd') for d in range(0,len_days+1)]

    #===Calling Horizons===
    #Create ephemerides dataframe for the whole period
    eph_all_targets = pd.DataFrame()

    epochs = {  'start' : start_date.strftime("%Y-%m-%d %H:00"),
                'stop'  : (end_date+TimeDelta(2,format="jd")).strftime("%Y-%m-%d %H:00"),
                'step'  : '15min'}

    #Horizons call for Moon
    moon_h = Horizons(id=301, location=MPC_code, epochs=epochs)
    try: #This fails if no ephemerides meet the criteria (I.E, not present in the sky during this time)
        moon_eph = moon_h.ephemerides(skip_daylight=True,quantities='1,8,9,24,25,47').to_pandas()
        moon_eph['target'] = 'Moon'
        moon_eph['datetime_str'] = pd.to_datetime(moon_eph['datetime_str'],format='%Y-%b-%d %H:%M')
        eph_all_targets = pd.concat([eph_all_targets,moon_eph])
    except:
        logger.debug(f'Cannot see Moon')

    with Progress(console=console,transient=True) as pb:
        t1 = pb.add_task('Calling Horizons', total=len(target_list), )

        for i,obj_name in enumerate(target_list):
            obj_h = Horizons(id=str(obj_name), location=MPC_code, epochs=epochs)
            try: #This fails if no ephemerides meet the criteria (I.E, not present in the sky during this time)
                eph = obj_h.ephemerides(skip_daylight=True,quantities='1,8,9,24,25,47').to_pandas()
                eph['target'] = obj_name
                eph['datetime_str'] = pd.to_datetime(eph['datetime_str'],format='%Y-%b-%d %H:%M')
                eph_all_targets = pd.concat([eph_all_targets,eph])
            except:
                logger.debug(f'Cannot see {obj_name}')
                continue 

            pb.update(t1,advance=1)

    #Create mag value
    if 'Tmag' in eph_all_targets.columns: #This won't be the case if there are 0 comets
        eph_all_targets['Mag'] = eph_all_targets['Tmag']
        eph_all_targets['Mag'] = eph_all_targets['Mag'].mask((eph_all_targets['Tmag'].isna()) | (eph_all_targets['Tmag'] == 0), eph_all_targets['V'])
    else:
        eph_all_targets['Mag'] = eph_all_targets['V']
    
    #Now apply the magnitude limit
    eph_all_targets = eph_all_targets[eph_all_targets['Mag'] < mag_limit].sort_values(by=['target', 'datetime_str']).reset_index(drop=True)

    #Then create elevation
    eph_all_targets = eph_all_targets.reset_index(drop=True)
    eph_all_targets['elevation'] = 90 - np.rad2deg(np.arccos(1 / eph_all_targets['airmass']))
    logger.info("Horizons call complete")

    #Generate dataframe of target names and plot info
    target_plot_info = marker_list(eph_all_targets['target'].unique())

    #Make temp file in current directory
    script_dir = Path(__file__).resolve().parent
    temp_dir = script_dir / 'temp'
    temp_dir.mkdir(exist_ok=True)

    #===Loop through nights===
    with Progress(console=console,transient=True) as pb:
        t1 = pb.add_task('Creating nightly plots', total=len(dates_list))

        df_summary = pd.DataFrame()
        for night in dates_list:
            sun_eph = twilight_times(night,MPC_code)

            #Data frame for times between sunset and sunrise
            night_mask = np.logical_and(sun_eph['set'].jd < eph_all_targets['datetime_jd'], eph_all_targets['datetime_jd'] < sun_eph['rise'].jd)
            eph_night = eph_all_targets[night_mask]

            #Summary is created by taking median values of each property per target per night
            df_night_summary = pd.DataFrame()
            for obj in eph_night['target'].unique():
                
                if obj=='Moon':
                    lunar_illum = eph_night_tar['lunar_illum'].median()

                eph_night_tar = eph_night[eph_night.target==obj]
                eph_night_tar_visible = eph_night_tar[eph_night_tar['elevation']>elevation_limit]
                if len(eph_night_tar_visible) == 0:
                    continue

                first_obs = eph_night_tar_visible['datetime_jd'].values[0]
                final_obs = eph_night_tar_visible['datetime_jd'].values[-1]
                time_visible = (final_obs - first_obs) * 24 #Units of hours
                if time_visible < time_visible_limit: #If less than limit, don't plot
                    if obj != 'Moon':
                        continue

                median_ra,median_dec = eph_night_tar['RA'].median(), eph_night_tar['DEC'].median()
                med_coord = SkyCoord(ra=median_ra*u.degree, dec=median_dec*u.degree, frame='icrs')

                #Night summary dataframe for each target
                tar_night_summary = {'target'      : obj,
                                     'date_str'    : night.strftime('%Y-%m-%d'),
                                     'datetime_str': night.to_datetime(),
                                     'alpha'       : eph_night_tar['alpha'].median(),
                                     'Mag'         : eph_night_tar['Mag'].median(),
                                     'rate'        : eph_night_tar['Sky_motion'].median(),
                                     'RA'          : median_ra,
                                     'DEC'         : median_dec,
                                     'RA_str'      : med_coord.ra.to_string(unit=u.hour, sep=':', precision=0),
                                     'DEC_str'     : med_coord.dec.to_string(sep=':', precision=0),
                                     'T_Vis'       : time_visible,
                                     'lunar_elong' : eph_night_tar['lunar_elong'].median(),
                                     'twlt_stt'    : sun_eph['astronomical_set'],
                                     'twlt_stp'    : sun_eph['astronomical_rise'],
                                     'nght_stt'    : sun_eph['set'],
                                     'nght_stp'    : sun_eph['rise']}
                df_tar_night_summary = pd.DataFrame(data=[tar_night_summary])
                df_night_summary = pd.concat([df_night_summary,df_tar_night_summary]).reset_index(drop=True)
            
            logger.debug(f"Completed night {night.strftime('%Y-%m-%d')}")

            #==Make Airmass plots==
            #Sort df_night_summary (which has one entry per target) by RA and DEC
            df_night_summary.sort_values(by=['RA','DEC'],inplace=True)
            figures.elevation_chart(night,sun_eph,eph_night,target_plot_info,elevation_limit,time_visible_limit,show_plot=False,fig_path=temp_dir)
            pdfs.elevation_chart(night,df_night_summary,MPC_code,lunar_illum,time_visible_limit,fig_path=temp_dir)

            df_summary = pd.concat([df_summary,df_night_summary]).reset_index(drop=True)
            pb.update(t1,advance=1)

    df_summary.sort_values(by=['target','date_str']).to_csv(summary_file)
    logger.info('Completed nightly plots')

    #Create one large pdf for all airmass pdfs
    subprocess.check_output([f"qpdf --empty --pages $(for i in {temp_dir}/airmass_????????.pdf; do echo $i 1-z; done) -- ./airmass.pdf"], shell=True)
    logger.debug('Made master airmass pdf')

    with Progress(console=console,transient=True) as pb:
        t1 = pb.add_task('Creating summary pdf plots', total=len(df_summary['target'].unique()))

        for obj in enumerate(df_summary['target'].unique()):



            pb.update(t1,advance=1)

    figures.summary_chart(df_summary,target_plot_info,time_visible_limit,target=False,show_plot=False,fig_path='./temp')

    #remove temp
    shutil.rmtree("temp")

    return True

#===Functions for parsing args below this point===
def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Check the observability of a list of solar system objects",
                                     epilog='Cannot accept limits in both airmass and elevation')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable verbose output (sets log level to DEBUG)")

    #Start and end dates
    date_group = parser.add_argument_group("Dates (inclusive) to check between. Format YYYY-MM-DD")
    date_group.add_argument('start_date',
                            help="Initial date in range to check. Night of observation commencing at site")
    date_group.add_argument('end_date',
                            help="Final date in range to check. Night of observation commencing at site")

    #Additional info
    info_group = parser.add_argument_group("Additional limits that can be applied to filter targets")
    info_group.add_argument('-mag', '--mag-limit',
                            help="Upper limit in (V) magnitude. Default 25")
    info_group.add_argument('-time', '--time-visible',
                            help='Time [hours] under which a target is not observable on a given night. Default 1')
    info_group.add_argument('-mpc', '--mpc-code', type=str,
                            help="MPC site to check from. Defaults to 809 (La Silla)")
    info_group.add_argument('-air','--airmass-limit',
                            help='Limit on airmass that can be observed, and plotted. Default 2')
    info_group.add_argument('-el','--elevation-limit',
                            help='Limit on elevation [degrees] that can be observed, and plotted. Default 30')

    #Input files
    file_group = parser.add_argument_group("File inputs/outputs")
    file_group.add_argument("-tar", "--target-list", type=Path, default=Path('./target_list.txt'),
                            help="[INPUT] List of targets. Each target on a new line. Default ./targetlist.txt")
    file_group.add_argument("-sum", "--summary-file", type=Path, default=Path('./obs_summary.csv'),
                            help="[OUTPUT] Summary csv of nightly medians for each target. Default ./obs_summary.csv")

    return parser.parse_args()

def check_type(name:str, val:str, req_type:type):
    try: 
        val = req_type(val)
    except:
        error_exit(f'{name} value cannot be read into a {req_type}')
    return val

def validate_args(args):
    #Check verbose
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug('Verbose: Set level to DEBUG')

    #Check dates format
    try:
        args.start_date = Time(args.start_date,format='iso')
        args.end_date   = Time(args.end_date,format='iso')
    except:
        error_exit('Cannot convert dates to astropy.time.Time objects')

    #Check mag and apply default value if none
    if not args.mag_limit:
        args.mag_limit = DEFAULT_MAG_LIMIT
    else:
        args.mag_limit = check_type('--mag-limit',args.mag_limit,float)

    #Check time and apply default value if none
    if not args.time_visible:
        args.time_visible = DEFAULT_TIME_VISIBLE
    else:
        args.time_visible = check_type('--time-visible',args.time_visible,float)
        if args.time_visible <= 0:
            error_exit('--time-visible must be positive') 

    #Check airmass/elevation
    if not args.airmass_limit and not args.elevation_limit:
        args.elevation_limit = DEFAULT_ELEVATION_LIMIT
    elif args.airmass_limit and args.elevation_limit:
        error_exit('Cannot accept separate limits for airmass and elevation')        
    elif args.elevation_limit:
        args.elevation_limit = check_type('--elevation-limit',args.elevation_limit,float)
        if args.elevation_limit < 0:
            error_exit('--elevation-limit must be positive')
        elif args.elevation_limit == 0:
            args.elevation_limit == 0.001 #To avoid dividing by 0
    elif args.airmass_limit:
        args.airmass_limit = check_type('--airmass-liimit',args.airmass_limit,float)
        if args.airmass_limit < 1:
            error_exit('--airmass-limit must be greater than 1')
        # args.elevation_limit = 90 - np.rad2deg(np.cos(args.airmass_limit))
        args.elevation_limit = 90 - np.rad2deg(np.arccos(1 / args.airmass_limit))
        logger.debug(f'Elevation limit set to {args.elevation_limit:.2f} degrees')
    else:
        error_exit('This message should not appear so it is time to cry')

    #Check MPC codes
    if not args.mpc_code:
        args.mpc_code = DEFAULT_MPC_CODE
    elif len(args.mpc_code) != 3:
        error_exit('Input MPC code does not have 3 characters')

    obs_sites = MPC_query.get_observatory_codes()
    logger.info(f"Selected observatory: {obs_sites[obs_sites['Code']==args.mpc_code]['Name'].value[0]}")

    return args

def main():

    args = parse_args()
    args = validate_args(args)

    limits = [args.mag_limit,args.time_visible,args.elevation_limit]

    observability_finder(args.start_date,args.end_date,args.mpc_code,limits,args.target_list,args.summary_file)

    return

if __name__ == '__main__':
    main()
