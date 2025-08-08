from .plotting import elevation_chart
from .latex import create_pdf
import tempfile
from pathlib import Path
from pypdf import PdfWriter, PdfReader
from .outfmt import logger, error_exit

def make_elevation_charts_pdf(eph_cut, twilight_list, target_plot_info, elevation_limit, mpc_code, base_out_name=''):
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
        
        for i,row in twilight_list.iterrows():
        
            mask = eph_cut['night'] == row['night']
            eph_night = eph_cut[mask]        
            lunar_illum = eph_night['lunar_illum'].median()
            
            # Makes fig for each night
            elevation_chart(row,eph_night,target_plot_info,elevation_limit,show_plot=False,fig_path=tmpdir_path)
            # Makes pdf for each night
            create_pdf(row,mpc_code,lunar_illum,pdf_path=tmpdir_path)
    
        pdf_name_format = "elevation_????????.pdf"
        pdf_files = sorted(tmpdir_path.glob(pdf_name_format))

        writer = PdfWriter()

        for pdf_file in pdf_files:
            reader = PdfReader(str(pdf_file))
            for page in reader.pages:
                writer.add_page(page)

        output_path = "./" + base_out_name + "elevation.pdf"
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            logger.info(f"Elevation charts saved to {output_path}")
 

    return