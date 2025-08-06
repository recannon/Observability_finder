import pandas as pd
from astropy.time import Time, TimeDelta
from astroquery.jplhorizons import Horizons
from astroquery.mpc import MPC as MPC_query
from rich.progress import Progress
from .outfmt import console, logger, error_exit
import ephem
import numpy as np


def create_horizon_dataframe(start_date:Time, end_date:Time, mpc_code:str, target_list:list[str]) -> pd.DataFrame:
    '''
    Calls JPL Horizons for a list of targets and returns a DataFrame with ephemerides.

    Inputs
        start_date  : astropy Time() object for the start date of the ephemerides.
        end_date    : astropy Time() object for the end date of the ephemerides.
        mpc_code    : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
        target_list : list of target names (strings) to query.

    Output
        eph_all_targets : DataFrame with ephemerides for all targets.
    '''
    epochs = {  'start' : start_date.strftime("%Y-%m-%d %H:00"),
                'stop'  : (end_date + TimeDelta(2,format="jd")).strftime("%Y-%m-%d %H:00"),
                'step'  : '15min'}

    # Append moon to target_list
    if '301' not in target_list:
        target_list += ['301']
    
    # Empty list of ephemeride dataframes
    eph_list = []
    
    # Call horizons for each object
    with Progress(console=console, transient=True) as pb:
        t1 = pb.add_task('Calling Horizons', total=len(target_list))
        for i,obj_name in enumerate(target_list):
            
            logger.debug(f'Searching for {obj_name}')
            eph = call_horizons_obj(obj_name, mpc_code, epochs)
            eph_list.append(eph)

            pb.update(t1,advance=1)

    # Concatenate DataFrames
    eph_all_targets = pd.concat(eph_list)
    
    # Create elevation (horizon has airmass)
    eph_all_targets = eph_all_targets.reset_index(drop=True)
    eph_all_targets['elevation'] = 90 - np.rad2deg(np.arccos(1 / eph_all_targets['airmass']))
    logger.info("Horizons call complete")
    
    return eph_all_targets


def call_horizons_obj(obj_name:str, mpc_code:str, epochs:dict) -> pd.DataFrame:
    '''
    Calls JPL Horizons for a single object and returns a DataFrame with ephemerides.

    Inputs
        obj_name    : Name of the object to query.
        mpc_code    : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
        epochs      : Dictionary with 'start', 'stop', and 'step' keys for the time range.

    Output
        eph         : DataFrame with ephemerides for the object.
    '''
    obj_h = Horizons(id=str(obj_name), location=mpc_code, epochs=epochs)
    try: 
        # Fails if no ephemerides meet the criteria (I.E, not present in the sky during this time)
        eph = obj_h.ephemerides(skip_daylight=True, quantities='1,8,9,24,25,47').to_pandas()
        eph['target'] = obj_name
        eph['datetime_str'] = pd.to_datetime(eph['datetime_str'], format='%Y-%b-%d %H:%M')
    except:
        logger.debug(f'Cannot see {obj_name}')
    
    return eph


def limit_cuts(eph_df, mag_limit, elevation_limit):
    '''
    

    '''
    # Create mag value
    if 'Tmag' in eph_df.columns: #This won't be the case if there are 0 comets
        eph_df['Mag'] = eph_df['Tmag']
        eph_df['Mag'] = eph_df['Mag'].mask((eph_df['Tmag'].isna()) | (eph_df['Tmag'] == 0), eph_df['V'])
    else:
        eph_df['Mag'] = eph_df['V']
    # Apply the magnitude limit
    eph_df_cut = eph_df[eph_df['Mag'] < mag_limit].sort_values(by=['target', 'datetime_str']).reset_index(drop=True)

    # Apply elevation cuts
    eph_df_cut = eph_df_cut[eph_df_cut['elevation'] > elevation_limit]
    
    return eph_df_cut


def get_twilight_times(mpc_code:str, date:Time) -> dict[Time]:
    '''
    Calculates times of setting and rising of the Sun, and the start and end times of civil, nautical, and astronomical twilight.
        
    Input
        date        : astropy Time() object for the day for which the following night should be checked.
        MPC_code    : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
    
    Output
        Dictionary object
            'set'               : set
            'rise'              : rise
            'civil_set'         : civil_set
            'civil_rise'        : civil_rise
            'nautical_rise'     : nautical_rise
            'nautical_set'      : nautical_set
            'astronomical_rise' : astronomical_rise
            'astronomical_set'  : astronomical_set

            All values are astropy.Time objects.
    '''    

    # Load MPC latitude and longitude and manipulate units
    obs_sites   = MPC_query.get_observatory_codes()
    rho_cos_phi = obs_sites[obs_sites['Code']==mpc_code]['cos'].value
    rho_sin_phi = obs_sites[obs_sites['Code']==mpc_code]['sin'].value
    rho         = np.sqrt(rho_cos_phi**2 + rho_sin_phi**2)
    phi         = np.arcsin(rho_sin_phi/rho)
    
    # Site latitude and longitude
    site_lat = np.rad2deg(phi)[0]
    site_lon = obs_sites[obs_sites['Code']==mpc_code]['Longitude'].value[0]

    # Create MPC_site for ephem package
    MPC_site      = ephem.Observer()
    MPC_site.lon  = str(site_lon)
    MPC_site.lat  = str(site_lat)
    MPC_site.date = date.iso

    # Keep counting sunsets and sunrises from the sun set after given time.
    MPC_site.horizon  = '0'   # Horizon
    set               = Time(MPC_site.next_setting(ephem.Sun(), start=date.iso).datetime())
    rise              = Time(MPC_site.next_rising( ephem.Sun(), start=set.iso ).datetime())
    MPC_site.horizon  = '-6'  # Civil twilight
    civil_set         = Time(MPC_site.next_setting(ephem.Sun(), start=set.iso, use_center=True).datetime())
    civil_rise        = Time(MPC_site.next_rising( ephem.Sun(), start=set.iso, use_center=True).datetime())
    MPC_site.horizon  = '-12' # Nautical twilight
    nautical_set      = Time(MPC_site.next_setting(ephem.Sun(), start=set.iso, use_center=True).datetime())
    nautical_rise     = Time(MPC_site.next_rising( ephem.Sun(), start=set.iso, use_center=True).datetime())
    MPC_site.horizon  = '-18' # Astronomical twilight
    astronomical_set  = Time(MPC_site.next_setting(ephem.Sun(), start=set.iso, use_center=True).datetime())
    astronomical_rise = Time(MPC_site.next_rising( ephem.Sun(), start=set.iso, use_center=True).datetime())

    return {
        'set'               : set,
        'rise'              : rise,
        'civil_set'         : civil_set,
        'civil_rise'        : civil_rise,
        'nautical_rise'     : nautical_rise,
        'nautical_set'      : nautical_set,
        'astronomical_rise' : astronomical_rise,
        'astronomical_set'  : astronomical_set
    }