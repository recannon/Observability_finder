import pandas as pd
import datetime
from astropy.time import Time, TimeDelta
from astroquery.jplhorizons import Horizons
from astroquery.mpc import MPC as MPC_query
from rich.progress import Progress
from .outfmt import console, logger, error_exit
import ephem
import numpy as np


def create_horizon_dataframe(twilight_times:pd.DataFrame, mpc_code:str, target_list:list[str]) -> pd.DataFrame:
  
    """
    Calls JPL Horizons for a list of targets and returns a DataFrame with ephemerides.

    Inputs
        start_date  : astropy Time() object for the start date of the ephemerides.
        end_date    : astropy Time() object for the end date of the ephemerides.
        mpc_code    : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
        target_list : list of target names (strings) to query.

    Output
        eph_all_targets : DataFrame with ephemerides for all targets.
    """
    
    start_date = twilight_times['night'].iloc[0]
    end_date = twilight_times['night'].iloc[-1]
    epochs = {  'start' : Time(start_date).strftime("%Y-%m-%d %H:00"),
                'stop'  : (Time(end_date) + TimeDelta(2,format="jd")).strftime("%Y-%m-%d %H:00"),
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
    
    # Create time visible column in DataFrame
    eph_all_targets['datetime'] = pd.to_datetime(eph_all_targets['datetime_str'])
        
    # Loop over nights and mask the relevant rows
    eph_all_targets['night'] = None
    for i, date in twilight_times.iterrows():            
        mask = (eph_all_targets['datetime'] >= date['sun_set']) & (eph_all_targets['datetime'] <= date['sun_rise'])
        eph_all_targets.loc[mask, 'night'] = date['night']
        
    # Drop rows not assigned to any night
    eph_all_targets = eph_all_targets.dropna(subset=['night'])
        
    eph_all_targets['night'] = pd.to_datetime(eph_all_targets['night'])    
        
    return eph_all_targets


def call_horizons_obj(obj_name:str, mpc_code:str, epochs:dict) -> pd.DataFrame:
    """
    Calls JPL Horizons for a single object and returns a DataFrame with ephemerides.

    Inputs
        obj_name    : Name of the object to query.
        mpc_code    : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
        epochs      : Dictionary with 'start', 'stop', and 'step' keys for the time range.

    Output
        eph         : DataFrame with ephemerides for the object.
    """
    obj_h = Horizons(id=str(obj_name), location=mpc_code, epochs=epochs)
    try: 
        # Fails if no ephemerides meet the criteria (I.E, not present in the sky during this time)
        eph = obj_h.ephemerides(skip_daylight=True, quantities='1,8,9,24,25,47').to_pandas()
        eph['target'] = obj_name
        eph['datetime_str'] = pd.to_datetime(eph['datetime_str'], format='%Y-%b-%d %H:%M')
    except:
        logger.debug(f'Cannot see {obj_name}')
    
    return eph


def limit_cuts(eph_df, mag_limit, elevation_limit, t_vis_limit):
    """
    

    """
    # Create mag value
    if 'Tmag' in eph_df.columns: #This won't be the case if there are 0 comets
        eph_df['Mag'] = eph_df['Tmag']
        eph_df['Mag'] = eph_df['Mag'].mask((eph_df['Tmag'].isna()) | (eph_df['Tmag'] == 0), eph_df['V'])
    else:
        eph_df['Mag'] = eph_df['V']
    # Apply the magnitude limit
    eph_df_cut = eph_df[eph_df['Mag'] < mag_limit].sort_values(by=['target', 'datetime_str']).reset_index(drop=True)

    # Apply elevation cuts
    eph_df_elev = eph_df_cut[eph_df_cut['elevation'] > elevation_limit]
    
    # Apply time visible cuts (0.25 = 15 mins / 1 hour)
    t_vis_counts    = eph_df_elev.groupby(['target', 'night']).size()
    t_vis_dur       = t_vis_counts.mul(0.25).reset_index(name='duration_hours')
    targets_visible = t_vis_dur[t_vis_dur['duration_hours'] >= t_vis_limit]    
    
    eph_df_cut = eph_df_cut.merge(targets_visible, on=['target', 'night'], how='inner')    
    
    return eph_df_cut


def get_twilight_times(mpc_code:str, date_list:list[Time]) -> dict[datetime]:

    obs_sites   = MPC_query.get_observatory_codes()
    rho_cos_phi = obs_sites[obs_sites['Code']==mpc_code]['cos'].value
    rho_sin_phi = obs_sites[obs_sites['Code']==mpc_code]['sin'].value
    rho         = np.sqrt(rho_cos_phi**2 + rho_sin_phi**2)
    phi         = np.arcsin(rho_sin_phi/rho)
    site_lat = np.rad2deg(phi)[0]
    site_lon = obs_sites[obs_sites['Code']==mpc_code]['Longitude'].value[0]

    MPC_site      = ephem.Observer()
    MPC_site.lon  = str(site_lon)
    MPC_site.lat  = str(site_lat)
    
    #Adjust for local_noon calc
    if site_lon > 180:
        site_lon -= 360  

    twilight_definitions = {
            'civil': '-6',
            'nautical': '-12',
            'astronomical': '-18'
        }
    all_night_info = []

    for night in date_list:

        night_info = {'night': night.to_datetime()}

        # Approximate local noon (in UT)      
        approx_local_noon = night + TimeDelta(0.5, format='jd') - TimeDelta((site_lon/360), format='jd') 
        MPC_site.date     = approx_local_noon.iso

        MPC_site.horizon = 0
        sunset        = MPC_site.next_setting(ephem.Sun())
        MPC_site.date = sunset
        sunrise       = MPC_site.next_rising(ephem.Sun())
                
        night_info['sun_set']  = sunset.datetime()
        night_info['sun_rise'] = sunrise.datetime()
        
        for name, angle in twilight_definitions.items():
                        
            MPC_site.horizon = angle
            twilight_set  = MPC_site.next_setting(ephem.Sun(), use_center=True)
            twilight_rise = MPC_site.next_rising(ephem.Sun(), use_center=True)
            night_info[f'{name}_set']  = twilight_set.datetime()
            night_info[f'{name}_rise'] = twilight_rise.datetime()

        all_night_info.append(night_info)

    all_night_info = pd.DataFrame(all_night_info)

    return all_night_info