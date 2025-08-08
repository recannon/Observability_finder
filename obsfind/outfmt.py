import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
import sys
import subprocess
from .plotting import elevation_chart
from .latex import elevation_pdf
import tempfile
from pathlib import Path

def make_elevation_charts_pdf(eph_cut, twilight_list, target_plot_info, elevation_limit, mpc_code):
    """
    Creates elevation charts for each night in the ephemeris DataFrame and saves them as a PDF.

    Inputs
        eph_cut          : DataFrame with ephemerides for each target.
        twilight_list    : DataFrame with twilight times for each night.
        target_plot_info : DataFrame with target names, markers, and colours.
        elevation_limit  : Minimum elevation limit for plotting.
        mpc_code         : MPC code of the observatory.

    Output
        PDF file with elevation charts for each night.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        for _,row in twilight_list.iterrows():
        
            mask = eph_cut['night'] == row['night']
            eph_night = eph_cut[mask]        
            lunar_illum = eph_night['lunar_illum'].median()
            
            # Makes fig for each night
            elevation_chart(row,eph_night,target_plot_info,elevation_limit,show_plot=False,fig_path=tmpdir_path)
            # Makes pdf for each night
            elevation_pdf(row,mpc_code,lunar_illum,fig_path=tmpdir_path)
    
        subprocess.check_output([f"qpdf --empty --pages $(for i in {tmpdir_path}/elevation_????????.pdf; do echo $i 1-z; done) -- ./elevation.pdf"], shell=True)

#Error message output
def error_exit(message:str):
    logger.error(message)
    sys.exit(1)

custom_theme = Theme({
    'logging.level.debug': 'green',
    'logging.level.info': 'cyan',
    'logging.level.warning': 'yellow',
    'logging.level.error': 'bold red',
    'logging.level.critical': 'bold white on red',
    })

console = Console(theme=custom_theme)

logging.basicConfig(
    level='INFO',#DON'T CHANGE THIS, CHANGE IN BOTTOM LINE
    format='| %(message)s',
    datefmt='[%X]',
    handlers=[RichHandler(console=console,
                          show_time=False, show_path=False,
                          markup=True, rich_tracebacks=True)]
)

logger = logging.getLogger('observability_finder_logger')
logger.setLevel(logging.INFO)

