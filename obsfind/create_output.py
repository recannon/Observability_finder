from .plotting import elevation_chart, summary_chart
from .make_pdfs import create_elevation_pdf, create_summary_pdf
import tempfile
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from astropy.coordinates import SkyCoord
import astropy.units as u
import pandas as pd
from .outfmt import logger, console
from rich.progress import Progress

def make_elevation_charts_pdf(eph_cut, twilight_list, target_plot_info, elevation_limit, mpc_code, base_out_name=''):
    """
    Creates elevation charts for each night in the ephemeris DataFrame and saves them as a PDF.

    Inputs
        eph_cut          : DataFrame with ephemerides for each target.
        twilight_list    : DataFrame with twilight times for each night.
        target_plot_info : DataFrame with target names, markers, and colours.
        elevation_limit  : Minimum elevation limit for plotting.
        mpc_code         : MPC code of the observatory.
        base_out_name    : Base name for the output files (default: '').

    Output
        PDF file with elevation charts for each night.
    """
    
    summary_list = []
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        with Progress(console=console, transient=True) as pb:
            t1 = pb.add_task('Making nightly plots', total=len(twilight_list))
            for i,row in twilight_list.iterrows():
            
                logger.debug(f'Processing {row["night"]}')
            
                mask = eph_cut['night'] == row['night']
                eph_night = eph_cut[mask]
                
                no_targets_visible = len(eph_night.targetname.unique())
                logger.debug(f'{no_targets_visible} targets visible')
                        
                summary_df = (
                    eph_night
                    .groupby("target")[eph_night.columns.difference(["target"])]
                    .apply(lambda df: summarize_target(df, row, tar_name=df.name))
                    .reset_index(drop=True)
                )
                
                # summary_df["lunar_illum"] = lunar_illum
                summary_df["lunar_illum"] = row['lunar_illum']
                summary_df = summary_df[summary_df['target'] != 'Moon']
                summary_df = summary_df.sort_values(by='RA_str')
                summary_list.append(summary_df)
                
                # Makes fig for each night
                elevation_chart(row,eph_night,target_plot_info,elevation_limit,show_plot=False,fig_path=tmpdir_path)
                # Makes pdf for each night
                create_elevation_pdf(row,summary_df,mpc_code,pdf_path=tmpdir_path)

                pb.update(t1,advance=1)
    
        #Mergers pdfs together
        pdf_name_format = "elevation_????????.pdf"
        pdf_files = sorted(tmpdir_path.glob(pdf_name_format))
        writer = PdfWriter()
        for pdf_file in pdf_files:
            reader = PdfReader(str(pdf_file))
            for page in reader.pages:
                writer.add_page(page)

        output_path = Path(f"./{base_out_name}elevation.pdf")
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        logger.info(f"Elevation charts saved to {output_path.resolve()}")

    eph_summary = pd.concat(summary_list)
    eph_summary = eph_summary.sort_values(by=['target', 'datetime_str'])

    return eph_summary

def summarize_target(group,twilight_info=None,tar_name=None):

    """
    Summarizes the ephemeris data for a target by calculating median values.
    
    Inputs
        group         : DataFrame group for a specific target.
        twilight_info : Optional DataFrame with twilight times for the night.

    Output
        Series with median values for the target.
    """
    
    medians = group.agg({
        'alpha': 'median',
        'Mag': 'median',
        'Sky_motion': 'median',
        'RA': 'median',
        'DEC': 'median',
        'lunar_elong': 'median',
        'duration_hours': 'median',
    })

    target = tar_name
    night = group['night'].iloc[0]
    med_coord = SkyCoord(ra=medians['RA']*u.deg, dec=medians['DEC']*u.deg, frame='icrs')

    return pd.Series({
        'target'      : target,
        'date_str'    : night.strftime('%Y-%m-%d'),
        'datetime_str': pd.to_datetime(night),
        **medians,
        'RA_str'      : med_coord.ra.to_string(unit=u.hour, sep=':', precision=0, pad=True),
        'DEC_str'     : med_coord.dec.to_string(sep=':', precision=0, pad=True),
        'twlt_stt'    : twilight_info['astronomical_set'],
        'twlt_stp'    : twilight_info['astronomical_rise'],
        'nght_stt'    : twilight_info['sun_set'],
        'nght_stp'    : twilight_info['sun_rise']
    })
    
def make_summary_charts_pdf(night_summaries, target_plot_info, base_out_name=''):
    """
    Generates summary charts for all targets and compiles them into a PDF.

    Inputs
        night_summaries  : DataFrame containing nightly summary data for each target,
                        used to generate the plots.
        target_plot_info : DataFrame mapping targets to plot colours and markers.
                        Must contain 'targets', 'colours', and 'markers' columns.
        base_out_name    : (optional) String prefix for the output PDF filename.

    Output
        Saves a PDF file in the current directory named '<base_out_name>summary.pdf',
        containing:
            - A first page with the all-target summary chart.
            - One page per target (excluding the Moon) with its corresponding chart.
        Temporary PNG plot files are created in a temporary directory and deleted
        automatically after the PDF is built.
    """
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
    
        #Summary for everything
        summary_chart(night_summaries,target_plot_info,fig_path=tmpdir_path)
    
        with Progress(console=console, transient=True) as pb:
            t1 = pb.add_task('Making summary plots', total=len(target_plot_info))
            
            #Summary chart per object
            for obj in target_plot_info['targets']:
                if obj=='Moon':
                    continue
                logger.debug(f'Processing summary for {obj}')
                summary_chart(night_summaries,target_plot_info,target=obj,fig_path=tmpdir_path)
                pb.update(t1, advance=1)
        
        #Create pdf
        pdf_name = Path(f'./{base_out_name}summary.pdf')
        create_summary_pdf(pdf_name,tmpdir_path)
        logger.info(f"Summary charts saved to {pdf_name.resolve()}")

    return