import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
import sys

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

# logging.getLogger('urllib3').setLevel(logging.WARNING)
# logging.getLogger('requests').setLevel(logging.WARNING)

# #Matplotlib spam
# logging.getLogger('matplotlib').setLevel(logging.WARNING)
# logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
# logging.getLogger('matplotlib.backends.backend_pdf').setLevel(logging.WARNING)
# logging.getLogger('matplotlib').setLevel(logging.INFO)

# #Annoying things on import
# logging.getLogger('pooch').setLevel(logging.WARNING)
# logging.getLogger('numcodecs').setLevel(logging.WARNING)
# logging.getLogger('zarr').setLevel(logging.WARNING)
# logging.getLogger('dask').setLevel(logging.WARNING)
logger = logging.getLogger('observability_finder_logger')
logger.setLevel(logging.INFO)

