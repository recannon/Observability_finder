import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
import sys
from pathlib import Path

#Error message output
def error_exit(message:str):
    """Outputs an error message and exits the program.

    Inputs
        message : Error message to be displayed.
    
    Output
        Exits the program with an error code.
    """
    logger.error(message)
    sys.exit(1)

def df2csv(df,base_name,file_name,contents):
    # Save csv in output file
    output_path = Path(f'./{base_name}{file_name}').resolve()
    df.to_csv(output_path)
    logger.info(f"{contents} saved to {output_path}")
    return

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

