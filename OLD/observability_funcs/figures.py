import matplotlib.pyplot as plt
import numpy as np
from .outfmt import error_exit,logger
from .twilight_times import twilight_times
import datetime

def elevation_chart(date,sun_eph,eph_night,target_plot_info,elevation_limit,time_visible_limit,show_plot=False,fig_path='./temp_airmass'):

    #Create figure
    fig, ax = plt.subplots(figsize=(18,15))
    ax = plt.gca()

    elevation_ticks = [tick for tick in np.arange(0, 91, 10) if tick>=elevation_limit]
    airmass_values = 1 / np.sin(np.radians(elevation_ticks))
    airmass_labels = [f'{a:.2f}' for a in airmass_values]

    #Plot targets above threshold
    for obj in eph_night['target'].unique():
        eph_night_tar = eph_night[eph_night.target==obj]

        eph_night_tar_visible = eph_night_tar[eph_night_tar['elevation']>elevation_limit]
        if len(eph_night_tar_visible) == 0:
            continue
        first_obs = eph_night_tar_visible['datetime_jd'].values[0]
        final_obs = eph_night_tar_visible['datetime_jd'].values[-1]
        time_visible = (final_obs - first_obs) * 24 #Units of hours

        if time_visible < time_visible_limit:
            continue

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
    
    #Format plot
    ax.axvspan(sun_eph['set'].iso, sun_eph['civil_set'].iso, alpha=.30)
    ax.axvspan(sun_eph['civil_set'].iso, sun_eph['nautical_set'].iso, alpha=.20)
    ax.axvspan(sun_eph['nautical_set'].iso, sun_eph['astronomical_set'].iso, alpha=.10)
    ax.axvspan(sun_eph['astronomical_rise'].iso, sun_eph['nautical_rise'].iso, alpha=.10)
    ax.axvspan(sun_eph['nautical_rise'].iso, sun_eph['civil_rise'].iso, alpha=.20)
    ax.axvspan(sun_eph['civil_rise'].iso, sun_eph['rise'].iso, alpha=.30)
    # ax.axhspan(0,elevation_limit,alpha=.5,color='grey')
    ax.set_xlabel(f"Universal Time (hours) - Night begins on {date.strftime('%d %b %Y')} UT", fontsize=20)
    ax.set_ylabel("Elevation", fontsize=20)
    ax.set_ylim(elevation_limit,90)
    ax.set_yticks(elevation_ticks)
    ax.xaxis.set_ticks_position('both')
    ax.yaxis.set_tick_params(direction='in', labelsize=20)
    ax.xaxis.set_tick_params(labeltop=True, which='both', direction='in', labelsize=20)
    ax.set_xlim(sun_eph['set'].iso, sun_eph['rise'].iso)
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
    plt.savefig(f'{fig_path}/airmass_{date.strftime("%Y%m%d")}.png')
    if show_plot:
        plt.show()
    plt.close()

    return


def summary_chart(df_summary_all,target_plot_info,time_visible_limit,target=False,show_plot=False,fig_path='./temp'):

    #File names and plotting targets
    if target:
        targets_to_plot = [target]
        file_name = f"summary_{target.replace(' ','').replace('C/','C')}"
    else:
        targets_to_plot = df_summary_all['target'].unique()
        file_name = "all_tar_summary"

    fig, axes = plt.subplots(2, 2, sharex=True,figsize=(30, 20))

    for obj in targets_to_plot:

        df_tar = df_summary_all[df_summary_all['target']==obj].reset_index(drop=True)

        plot_properties = ['T_Vis','Mag','rate','alpha']
        for i, ax in enumerate(axes.flatten()):

            if obj == 'Moon':
                if i == 0:
                    df_tar.plot(x='datetime_str', y=plot_properties[i],
                                label='Moon', ax=ax,
                                linestyle='--', color='black', marker='', lw=7, alpha=0.75)
                else:
                    continue
            else:
                marker = target_plot_info.loc[target_plot_info['targets'] == obj, 'markers'].values[0]
                colour = target_plot_info.loc[target_plot_info['targets'] == obj, 'colours'].values[0]
                df_tar.plot(x='datetime_str', y=plot_properties[i],
                                label=obj, ax=ax,
                                marker=marker, color=colour, markersize=8)

            ax.set_ylabel(plot_properties[i],fontsize=20)

        for ax in axes.flatten():
            ax.set_xlabel('Date',fontsize=20)
            ax.xaxis.set_ticks_position('both')
            ax.yaxis.set_ticks_position('both')
            ax.xaxis.set_tick_params(direction='in', labelsize=30, which='major',color='black',length=10,width=1)
            ax.yaxis.set_tick_params(direction='in', labelsize=30, which='major',color='black',length=10,width=1)
            ax.grid(which='major',axis='both')

        axes[0,0].set_ylim(time_visible_limit,12)


    fig.savefig(f'sum.png',bbox_inches='tight')

    # #Create figure and plot
    # fig, axes = plt.subplots(nrows=3,ncols=6,figsize=(28,30))
    # for obj in targets_to_plot:


        
    #     if obj == 'Moon':
    #         axes[0,0].plot(date,df_plot.T_Vis,  label=obj,marker=marker,color=colour,linewidth=4,markersize=15)
    #         axes[1,0].plot(date,df_plot.V,      label=obj,marker=marker,color=colour,linewidth=4,markersize=15)
    #         axes[2,0].plot(date,df_plot.alpha,  label=obj,marker=marker,color=colour,linewidth=4,markersize=15)
    #         axes[0,1].plot(date,df_plot.rate,   label=obj,marker=marker,color=colour,linewidth=4,markersize=15)
    #         axes[1,1].plot(date,df_plot.RA_app, label=obj,marker=marker,color=colour,linewidth=4,markersize=15)
    #         axes[2,1].plot(date,df_plot.DEC_app,label=obj,marker=marker,color=colour,linewidth=4,markersize=15)


    #     marker = target_list.loc[target_list['targets'] == obj, 'markers'].values[0]
    #     colour = target_list.loc[target_list['targets'] == obj, 'colours'].values[0]

    #     df_plot = df_summary_all[df_summary_all['target']==obj_name].reset_index(drop=True)
        
    #     date = [datetime.strptime(date_str,'%Y-%m-%d') for date_str in df_plot.date_str]
    #     axes[0,0].plot(date,df_plot.T_Vis,  label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)
    #     axes[1,0].plot(date,df_plot.V,      label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)
    #     axes[2,0].plot(date,df_plot.alpha,  label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)
    #     axes[0,1].plot(date,df_plot.rate,   label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)
    #     axes[1,1].plot(date,df_plot.RA_app, label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)
    #     axes[2,1].plot(date,df_plot.DEC_app,label=obj_name,marker=marker,color=colour,linewidth=4,markersize=15)

    # #Format plot
    # ylabels = [ 'Time visible / Hours',
    #             'Rate of motion / arcsec per min',
    #             'Estimated magnitude (V/Tmag)',
    #             'Apparent RA / degrees',
    #             'Phase angle / degrees',
    #             'Apparent DEC / degrees']
    # for ax, ylab in zip(axes.flatten(),ylabels):
    #     for spn in ax.spines: #Black edges
    #         ax.spines[spn].set_linewidth(5)
    #         ax.spines[spn].set_color('black')

    #     if len(df_summary_all.date_str) > 60:
    #         xticks = [date for date in np.unique(df_summary_all['date_str']) if date[-2:]=='01']
    #     else:
    #         xticks = np.unique(df_summary_all['date_str'])

    #     ax.xaxis.set_ticks(xticks)
    #     ax.xaxis.set_ticks_position('both')
    #     ax.yaxis.set_ticks_position('both')
    #     ax.xaxis.set_tick_params(direction='in', labelsize=30, which='both',color='black',length=10,width=5)
    #     ax.yaxis.set_tick_params(direction='in', labelsize=30, which='both',color='black',length=10,width=5)
    #     ax.set_ylabel(f'{ylab}',fontsize=30,labelpad=10)
    #     ax.grid(which='both',axis='both')
    #     plt.gca().invert_yaxis()
    #     plt.tight_layout()
        
    # axes[2,0].set_xlabel('Date',fontsize=30,labelpad=10)
    # axes[2,1].set_xlabel('Date',fontsize=30,labelpad=10)

    # if not target: #Do not plot legend if individual target plot
    #     fig.legend(np.unique(df_summary_all['target']), loc='lower center', bbox_to_anchor=(0.5, 1.00), ncol=2,prop={'size':30})

    # fig.subplots_adjust(wspace=0.2, hspace=0.1)
    # fig.savefig(f'{fig_path}/Nights-summary-png/{file_name}.png',bbox_inches='tight')

    # if show_plot:
    #     fig.show()
    # plt.close()