from .outfmt import logger,error_exit
import subprocess
from pylatex import Document, Section, Tabular, NoEscape, Figure, Command
from pylatex.utils import bold, escape_latex
from pathlib import Path
import numpy as np

def elevation_chart(date,df_night_summary,MPC_code,lunar_illum,t_vis_min=1,fig_path='./temp'):
    '''
    Saves a latex file with name ./Night-Charts-tex/summary_{date_str_nohyphen}.tex to create the airmass pdf for the given night.

    Input
        date      : date in astropy.Time format
        eph       : dataframe output from Horizons call with all targets concatenated together.
                        Should contain atleast horizons quantities 2,3,8,9,19,20,23,24,25
        MPC_code  : MPC code for the observatory - https://www.minorplanetcenter.net/iau/lists/ObsCodes.html
        t_vis_min : time threshold, in hours, a target must be visible for more than in order to be plotted. 
        fig_path    : Folder directory within which you have set up Night-Charts and Night-summary directories    
        
    '''
    
    #Drop targets from the dataframe that don't appear at this date.
    df_night_summary = df_night_summary[df_night_summary['T_Vis'] >= t_vis_min].reset_index(drop=True)
    if df_night_summary.empty:
        logger.info(f"No targets visible longer than {t_vis_min} hours on {date.iso}")
        return

    sun_set  = df_night_summary['nght_stt'].iloc[0]
    sun_rise = df_night_summary['nght_stp'].iloc[0]
    twlt_set  = df_night_summary['twlt_stt'].iloc[0]
    twlt_rise = df_night_summary['twlt_stp'].iloc[0]
    night_length_hours = (sun_rise - sun_set).sec / 3600
    twilight_length_hours = (twlt_rise - twlt_set).sec / 3600

    date_str_nohyphen = date.strftime('%Y%m%d')

    fig_path = Path(fig_path)
    fig_path.mkdir(parents=True, exist_ok=True)
    tex_filename = fig_path / f"airmass_{date_str_nohyphen}.tex"

    #Latex setup
    doc = Document(documentclass='article', document_options='a4paper')
    doc.packages.append(Command('usepackage', 'geometry'))
    doc.packages.append(Command('geometry', 'margin=0.5in'))
    doc.packages.append(Command('usepackage', 'graphicx'))
    doc.packages.append(Command('usepackage', 'longtable'))
    doc.packages.append(Command('usepackage', 'fullpage'))
    doc.packages.append(Command('usepackage', 'caption'))
    doc.append(NoEscape(r'\captionsetup{belowskip=0pt}'))
    doc.append(NoEscape(r'\thispagestyle{empty}'))

    #figure
    with doc.create(Figure(position='t')) as fig:
        fig.add_image(str(fig_path / f"airmass_{date_str_nohyphen}.png"), width=NoEscape(r'0.9\textwidth'))

    info_text = (
        f"\\textbf{{{date.strftime('%Y-%b-%d')}}}\\\\\n"
        f"MPC code: {MPC_code}\\\\\n"
        f"Sunrise-Sunset: {sun_set.strftime('%H:%M')} - {sun_rise.strftime('%H:%M')} UT\\\\\n"
        f"Twilight-Twilight: {twlt_set.strftime('%H:%M')} - {twlt_rise.strftime('%H:%M')} UT\\\\\n"
        f"Night lasts: {night_length_hours:.1f} / {twilight_length_hours:.1f} hours.\\\\"
        f"Lunar Illumination: {lunar_illum/100:.2f}\\\\"
    )

    doc.append(NoEscape(r'\begin{flushleft}'))
    doc.append(NoEscape(info_text))
    doc.append(NoEscape(r'\end{flushleft}'))
    doc.append(NoEscape(r'\centering'))

    #table
    with doc.create(Tabular('lcccccc')) as table:
        table.add_hline()
        table.add_hline()
        table.add_row(['Target', 'RA', 'DEC', 'App_Mag', 'Rate', 'Vis', 'T-O-M'])
        table.add_hline()
        for _, target in df_night_summary.iterrows():
            if target['target'] == 'Moon':
                continue
            table.add_row([
                escape_latex(str(target['target'])),
                escape_latex(str(target['RA_str'])),
                escape_latex(str(target['DEC_str'])),
                f"{target['Mag']:.2f}",
                f"{target['rate']:.3f}",
                f"{target['T_Vis']:.2f}",
                f"{target['lunar_elong']:.1f}"
            ])
        table.add_hline()

    # Generate PDF
    doc.generate_pdf(fig_path / tex_filename.stem, clean_tex=False, clean=True, compiler='pdflatex', silent=True)