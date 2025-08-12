import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import itertools
import matplotlib.dates as mdates
from .outfmt import logger

def marker_list(target_names):
    """
    Creates a list of markers and colours for plotting targets.

    Inputs
        target_names : List of target names to be plotted.

    Output
        DataFrame with target names, markers, and colours.
    """
    # Marker set up now that number of targets that will be plotted is known
    marker_opt = ['o','v','s','X','<','P','*','h','>','H','+','^','x','D']
    colour_opt = ['b','g','r','c','m','y']
    markers    = list(itertools.product(marker_opt, colour_opt))  # List of unique tuples
    markerlist = [pair[0] for pair in markers[:len(target_names)]]
    colourlist = [pair[1] for pair in markers[:len(target_names)]]
    target_list_data = {'targets'  : target_names,
                        'markers'  : markerlist,
                        'colours'  : colourlist}
    target_plot_info = pd.DataFrame(data = target_list_data)

    return target_plot_info


def elevation_chart(twilight_times, eph_night, target_plot_info, elevation_limit, show_plot=False, fig_path='./temp_airmass'):
    """
    Creates an elevation chart for a given night.
    
    Inputs
        twilight_times : DataFrame with twilight times for the night.
        eph_night      : DataFrame with ephemerides for the night.
        target_plot_info : DataFrame with target names, markers, and colours.
        elevation_limit : Minimum elevation limit for plotting.
        show_plot      : Boolean to show the plot (default: False).
        fig_path       : Path to save the figure (default: './temp_airmass').

    Output
        Saves the elevation chart as a PNG file if fig_path is provided.
    """
    night = twilight_times['night']

    # Create figure
    fig, ax = plt.subplots(figsize=(22,15))
    ax = plt.gca()

    elevation_ticks = [tick for tick in np.arange(0, 91, 10) if tick>=elevation_limit]
    airmass_values = 1 / np.sin(np.radians(elevation_ticks))
    airmass_labels = [f'{a:.2f}' for a in airmass_values]

    # Plot targets above threshold
    for obj in eph_night['target'].unique():
        
        eph_night_tar = eph_night[eph_night.target==obj]

        if obj == 'Moon':
            eph_night_tar.plot(x='datetime_str', y='elevation',
                            label='Moon', ax=ax,
                            linestyle='--', color='black', marker='', lw=7, alpha=0.75)
        else:
            colour = target_plot_info[target_plot_info['targets']==obj]['colours'].values[0]
            marker = target_plot_info[target_plot_info['targets']==obj]['markers'].values[0]
            eph_night_tar.plot(x='datetime_str', y='elevation',
                            label=obj, ax=ax,
                            marker=marker, color=colour, markersize=8)
    
    #Check if times actually exist (Won't if never sets)
    set_list = ['sun_set', 'civil_set', 'nautical_set', 'astronomical_set']
    twilight_times[set_list] = twilight_times[set_list].apply(pd.to_datetime).ffill()
    rise_list = ['sun_rise', 'civil_rise', 'nautical_rise', 'astronomical_rise']
    twilight_times[rise_list] = twilight_times[rise_list].apply(pd.to_datetime).ffill()

    # Format plot
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



def summary_chart(night_summaries,target_plot_info,target=False,fig_path='./temp_summary'):
    """
    Creates and saves a multi-panel summary chart for one or more targets.

    Inputs
        night_summaries  : DataFrame containing nightly summary data for each target,
                        including columns such as 'datetime_str', 'duration_hours',
                        'Mag', 'alpha', 'Sky_motion', 'RA', and 'DEC'.
        target_plot_info : DataFrame mapping targets to plot colours and markers.
                        Must contain 'targets', 'colours', and 'markers' columns.
        target           : (optional) Specific target name to plot. If provided,
                        only this target will be plotted; otherwise all targets
                        in night_summaries are included.
        fig_path         : Directory path to save the output figure PNG file.

    Output
        Saves a PNG image in fig_path containing:
            - Six subplots showing time visible, rate of motion, magnitude, RA,
            phase angle, and DEC as functions of date.
            - For all-target plots: includes a legend above the subplots.
            - For single-target plots: no legend is shown.
    """
    
    #File names and plotting targets
    if target:
        targets_to_plot = [target]
        file_name = f"summary_{target.replace(' ','').replace('C/','C')}"
    else:
        targets_to_plot = night_summaries['target'].unique()
        file_name = "all_tar_summary"

    #Create figure and plot
    date_fmt = mdates.DateFormatter('%m-%d')
    fig, axes = plt.subplots(nrows=3,ncols=2,figsize=(28,30))
    for obj in targets_to_plot:
        
        tar_summary = night_summaries[night_summaries.target==obj]

        # if obj == 'Moon':
            # eph_night_tar.plot(x='datetime_str', y='elevation',
                            # label='Moon', ax=ax,
                            # linestyle='--', color='black', marker='', lw=7, alpha=0.75)
        # else:
        colour = target_plot_info[target_plot_info['targets']==obj]['colours'].values[0]
        marker = target_plot_info[target_plot_info['targets']==obj]['markers'].values[0]
        
        step = 3
        date = tar_summary['datetime_str'][::step]
        axes[0,0].plot(date, tar_summary.duration_hours[::step],   label=obj, marker=marker, color=colour, linewidth=4, markersize=15)
        axes[1,0].plot(date, tar_summary.Mag[::step],       label=obj, marker=marker, color=colour, linewidth=4, markersize=15)
        axes[2,0].plot(date, tar_summary.alpha[::step],   label=obj, marker=marker, color=colour, linewidth=4, markersize=15)
        axes[0,1].plot(date, tar_summary.Sky_motion[::step],    label=obj, marker=marker, color=colour, linewidth=4, markersize=15)
        axes[1,1].plot(date, tar_summary.RA[::step],  label=obj, marker=marker, color=colour, linewidth=4, markersize=15)
        axes[2,1].plot(date, tar_summary.DEC[::step], label=obj, marker=marker, color=colour, linewidth=4, markersize=15)

    #Format plot
    ylabels = [ 'Time visible / Hours',
                'Rate of motion / arcsec per min',
                'Estimated magnitude (V/Tmag)',
                'Apparent RA / degrees',
                'Phase angle / degrees',
                'Apparent DEC / degrees']
    for ax, ylab in zip(axes.flatten(),ylabels):
        ax.xaxis.set_major_formatter(date_fmt)
        
        for spn in ax.spines: #Black edges
            ax.spines[spn].set_linewidth(5)
            ax.spines[spn].set_color('black')

        # ax.xaxis.set_ticks(xticks)
        ax.xaxis.set_ticks_position('both')
        ax.yaxis.set_ticks_position('both')
        ax.xaxis.set_tick_params(direction='in', labelsize=30, which='both',color='black',length=10,width=5)
        ax.yaxis.set_tick_params(direction='in', labelsize=30, which='both',color='black',length=10,width=5)
        ax.set_ylabel(f'{ylab}',fontsize=30,labelpad=10)
        ax.grid(which='both',axis='both')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        
    axes[2,0].set_xlabel('Date',fontsize=30,labelpad=10)
    axes[2,1].set_xlabel('Date',fontsize=30,labelpad=10)

    if not target: #Do not plot legend if individual target plot
        fig.legend(np.unique(night_summaries['target']), loc='lower center', bbox_to_anchor=(0.5, 1.00), ncol=2,prop={'size':30})

    fig.subplots_adjust(wspace=0.2, hspace=0.1)
    fig.savefig(f'{fig_path}/{file_name}.png',bbox_inches='tight')
    logger.debug(f'Saving {fig_path}/{file_name}.png')

    plt.close()