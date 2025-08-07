import matplotlib.pyplot as plt
import numpy as np
from .outfmt import error_exit,logger
import datetime
import pandas as pd
import itertools
import tempfile
from pathlib import Path
from .latex import elevation_pdf
import subprocess

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

def make_elevation_charts_pdf(eph_cut,twilight_list,target_plot_info,elevation_limit,mpc_code):
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        for _,row in twilight_list.iterrows():
        
            mask = eph_cut['night'] == row['night']
            eph_night = eph_cut[mask]        
            lunar_illum = eph_night['lunar_illum'].median()
            
            # Makes fig for each night
            elevation_chart(row,eph_night,target_plot_info,elevation_limit,show_plot=False,fig_path=tmpdir_path)
            #Makes pdf for each night
            elevation_pdf(row,mpc_code,lunar_illum,fig_path=tmpdir_path)
    
        subprocess.check_output([f"qpdf --empty --pages $(for i in {tmpdir_path}/elevation_????????.pdf; do echo $i 1-z; done) -- ./elevation.pdf"], shell=True)


def elevation_chart(twilight_times,eph_night,target_plot_info,elevation_limit,show_plot=False,fig_path='./temp_airmass'):

    night = twilight_times['night']

    #Create figure
    fig, ax = plt.subplots(figsize=(18,15))
    ax = plt.gca()

    elevation_ticks = [tick for tick in np.arange(0, 91, 10) if tick>=elevation_limit]
    airmass_values = 1 / np.sin(np.radians(elevation_ticks))
    airmass_labels = [f'{a:.2f}' for a in airmass_values]

    #Plot targets above threshold
    for obj in eph_night['target'].unique():
        
        eph_night_tar = eph_night[eph_night.target==obj]

        if obj == 'Moon (301)':
            eph_night_tar.plot(x='datetime_str', y='elevation',
                            label='Moon', ax=ax,
                            linestyle='--', color='black', marker='', lw=7, alpha=0.75)
        else:
            colour = target_plot_info[target_plot_info['targets']==obj]['colours'].values[0]
            marker = target_plot_info[target_plot_info['targets']==obj]['markers'].values[0]
            eph_night_tar.plot(x='datetime_str', y='elevation',
                            label=obj, ax=ax,
                            marker=marker, color=colour, markersize=8)
    
    #Format plot
    ax.axvspan(twilight_times['sun_set'].isoformat(), twilight_times['civil_set'].isoformat(), alpha=.30)
    ax.axvspan(twilight_times['civil_set'].isoformat(), twilight_times['nautical_set'].isoformat(), alpha=.20)
    ax.axvspan(twilight_times['nautical_set'].isoformat(), twilight_times['astronomical_set'].isoformat(), alpha=.10)
    ax.axvspan(twilight_times['astronomical_rise'].isoformat(), twilight_times['nautical_rise'].isoformat(), alpha=.10)
    ax.axvspan(twilight_times['nautical_rise'].isoformat(), twilight_times['civil_rise'].isoformat(), alpha=.20)
    ax.axvspan(twilight_times['civil_rise'].isoformat(), twilight_times['sun_rise'].isoformat(), alpha=.30)
    # ax.axhspan(0,elevation_limit,alpha=.5,color='grey')
    ax.set_xlabel(f"Universal Time (hours) - Night begins on {night.strftime('%d %b %Y')} UT", fontsize=20)
    ax.set_ylabel("Elevation", fontsize=20)
    ax.set_ylim(elevation_limit,90)
    ax.set_yticks(elevation_ticks)
    ax.xaxis.set_ticks_position('both')
    ax.yaxis.set_tick_params(direction='in', labelsize=20)
    ax.xaxis.set_tick_params(labeltop=True, which='both', direction='in', labelsize=20)
    ax.set_xlim(twilight_times['sun_set'].isoformat(), twilight_times['sun_rise'].isoformat())
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_yticks(elevation_ticks)
    ax2.set_yticklabels(airmass_labels)
    ax2.set_ylabel("Airmass", fontsize=20)
    ax2.yaxis.set_tick_params(direction='in', labelsize=20)

    # ax.legend(bbox_to_anchor=(1.1, 1), loc='upper left',prop={'size': 20})
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15),
              ncol=6, prop={'size': 20})

    plt.grid(which='both',axis='both')
    plt.tight_layout()
    if fig_path:
        plt.savefig(f'{fig_path}/elevation_{night.strftime("%Y%m%d")}.png')
    if show_plot:
        plt.show()
    plt.close()

    return