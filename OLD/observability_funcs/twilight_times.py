from astropy.time import Time
from .outfmt import logger,error_exit
from astroquery.mpc import MPC as MPC_query
import numpy as np
import ephem

def twilight_times(date,MPC_code):
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

    #Load MPC latitude and longitude and manipulate units
    obs_sites   = MPC_query.get_observatory_codes()
    rho_cos_phi = obs_sites[obs_sites['Code']==MPC_code]['cos'].value
    rho_sin_phi = obs_sites[obs_sites['Code']==MPC_code]['sin'].value
    rho         = np.sqrt(rho_cos_phi**2 + rho_sin_phi**2)
    phi         = np.arcsin(rho_sin_phi/rho)
    
    #Site latitude and longitude
    site_lat = np.rad2deg(phi)[0]
    site_lon = obs_sites[obs_sites['Code']==MPC_code]['Longitude'].value[0]

    #Create MPC_site for ephem package
    MPC_site      = ephem.Observer()
    MPC_site.lon  = str(site_lon)
    MPC_site.lat  = str(site_lat)
    MPC_site.date = date.iso

    #Keep counting sunsets and sunrises from the sun set after given time.
    MPC_site.horizon  = '0' #Horizon
    set               = Time(MPC_site.next_setting(ephem.Sun(),start=date.iso).datetime())
    rise              = Time(MPC_site.next_rising(ephem.Sun(),start=set.iso).datetime())
    MPC_site.horizon  = '-6' #Civil twilight
    civil_set         = Time(MPC_site.next_setting(ephem.Sun(),start=set.iso,use_center=True).datetime())
    civil_rise        = Time(MPC_site.next_rising(ephem.Sun(),start=set.iso,use_center=True).datetime())
    MPC_site.horizon  = '-12' #Nautical twilight
    nautical_set      = Time(MPC_site.next_setting(ephem.Sun(),start=set.iso,use_center=True).datetime())
    nautical_rise     = Time(MPC_site.next_rising(ephem.Sun(),start=set.iso,use_center=True).datetime())
    MPC_site.horizon  = '-18' #Astronomical twilight
    astronomical_set  = Time(MPC_site.next_setting(ephem.Sun(),start=set.iso,use_center=True).datetime())
    astronomical_rise = Time(MPC_site.next_rising(ephem.Sun(),start=set.iso,use_center=True).datetime())

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