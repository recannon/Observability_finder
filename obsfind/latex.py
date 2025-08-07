from .outfmt import logger,error_exit
import subprocess
from pylatex import Document, Section, Tabular, NoEscape, Figure, Command
from pylatex.utils import bold, escape_latex
from pathlib import Path
import numpy as np
from astropy.time import Time

def elevation_pdf(twilight_times,mpc_code,lunar_illum,fig_path):
    
    night = twilight_times['night']

    sun_set   = Time(twilight_times['sun_set'])
    sun_rise  = Time(twilight_times['sun_rise'])
    twlt_set  = Time(twilight_times['astronomical_set'])
    twlt_rise = Time(twilight_times['astronomical_rise'])
    night_length_hours = (sun_rise - sun_set).sec / 3600
    twilight_length_hours = (twlt_rise - twlt_set).sec / 3600

    date_str_nohyphen = night.strftime('%Y%m%d')

    fig_path = Path(fig_path)
    fig_path.mkdir(parents=True, exist_ok=True)
    tex_filename = fig_path / f"elevation_{date_str_nohyphen}.tex"

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
        fig.add_image(str(fig_path / f"elevation_{date_str_nohyphen}.png"), width=NoEscape(r'0.9\textwidth'))

    info_text = (
        f"\\textbf{{{night.strftime('%Y-%b-%d')}}}\\\\\n"
        f"MPC code: {mpc_code}\\\\\n"
        f"Sunrise-Sunset: {sun_set.strftime('%H:%M')} - {sun_rise.strftime('%H:%M')} UT\\\\\n"
        f"Twilight-Twilight: {twlt_set.strftime('%H:%M')} - {twlt_rise.strftime('%H:%M')} UT\\\\\n"
        f"Night lasts: {night_length_hours:.1f} / {twilight_length_hours:.1f} hours.\\\\"
        f"Lunar Illumination: {lunar_illum/100:.2f}\\\\"
    )

    doc.append(NoEscape(r'\begin{flushleft}'))
    doc.append(NoEscape(info_text))
    doc.append(NoEscape(r'\end{flushleft}'))
    doc.append(NoEscape(r'\centering'))

    # #table
    # with doc.create(Tabular('lcccccc')) as table:
    #     table.add_hline()
    #     table.add_hline()
    #     table.add_row(['Target', 'RA', 'DEC', 'App_Mag', 'Rate', 'Vis', 'T-O-M'])
    #     table.add_hline()
    #     for _, target in df_night_summary.iterrows():
    #         if target['target'] == 'Moon':
    #             continue
    #         table.add_row([
    #             escape_latex(str(target['target'])),
    #             escape_latex(str(target['RA_str'])),
    #             escape_latex(str(target['DEC_str'])),
    #             f"{target['Mag']:.2f}",
    #             f"{target['rate']:.3f}",
    #             f"{target['T_Vis']:.2f}",
    #             f"{target['lunar_elong']:.1f}"
    #         ])
    #     table.add_hline()

    # Generate PDF
    doc.generate_pdf(fig_path / tex_filename.stem, clean_tex=False, clean=True, compiler='pdflatex', silent=True)