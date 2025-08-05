import pandas as pd
from astropy.time import Time, TimeDelta
from astroquery.jplhorizons import Horizons
from rich.progress import Progress
from .outfmt import console, logger, error_exit


def call_horizons(start_date,end_date,mpc_code,target_list):
    '''
    '''
    epochs = {  'start' : start_date.strftime("%Y-%m-%d %H:00"),
                'stop'  : (end_date+TimeDelta(2,format="jd")).strftime("%Y-%m-%d %H:00"),
                'step'  : '15min'}

    # Append moon to target_list
    if '301' not in target_list:
        target_list += ['301']
    
    # Empty list of ephemeride dataframes
    eph_list = []
    
    #Call horizons for each object
    with Progress(console=console,transient=True) as pb:
        t1 = pb.add_task('Calling Horizons', total=len(target_list))
        for i,obj_name in enumerate(target_list):
            
            logger.debug(f'Searching for {obj_name}')
            eph = call_horizons_obj(obj_name,mpc_code,epochs)
            eph_list.append(eph)

            pb.update(t1,advance=1)

    # Concatenate DataFrames
    eph_all_targets = pd.concat(eph_list)
        
    return eph_all_targets


def call_horizons_obj(obj_name,mpc_code,epochs):
    '''
    '''
    obj_h = Horizons(id=str(obj_name), location=mpc_code, epochs=epochs)
    try: #This fails if no ephemerides meet the criteria (I.E, not present in the sky during this time)
        eph = obj_h.ephemerides(skip_daylight=True,quantities='1,8,9,24,25,47').to_pandas()
        eph['target'] = obj_name
        eph['datetime_str'] = pd.to_datetime(eph['datetime_str'],format='%Y-%b-%d %H:%M')
    except:
        logger.debug(f'Cannot see {obj_name}')
    
    return eph


def limit_cuts(csv,limits):
    return csv


def twilight_times():
    return twilight_times