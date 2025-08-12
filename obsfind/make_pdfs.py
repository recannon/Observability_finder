from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from astropy.time import Time
from .outfmt import logger

def create_elevation_pdf(twilight_times,summary_df,mpc_code,pdf_path):

    """
    Creates a PDF with elevation chart and summary table for a given night.

    Inputs
        twilight_times : DataFrame with twilight times for the night.
        summary_df     : DataFrame with summary information for the night.
        mpc_code       : MPC code for the observatory.
        pdf_path       : Path to save the PDF file.
        
    Output
        Saves the PDF file with elevation chart and summary table.
    """
    
    night_str = twilight_times['night'].strftime('%Y-%b-%d')
    night_str_nohyphen = twilight_times['night'].strftime('%Y%m%d')
    sun_set, sun_rise = twilight_times['sun_set'], twilight_times['sun_rise']
    twlt_set, twlt_rise = twilight_times['astronomical_set'], twilight_times['astronomical_rise']

    fig_name = f'{pdf_path}/elevation_{night_str_nohyphen}.png'
    pdf_name = f'{pdf_path}/elevation_{night_str_nohyphen}.pdf'

    # lunar_illum_val = summary_df['lunar_illum'].iloc[0] #They're all the same anyway
    lunar_illum_val = twilight_times['lunar_illum']

    doc = SimpleDocTemplate(pdf_name, pagesize=letter,
                            rightMargin=20, leftMargin=20,
                            topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []
       
    # Calculate time deltas in hours as floats
    night_length_hours = (Time(sun_rise) - Time(sun_set)).to_value('hour')
    twilight_length_hours = (Time(twlt_rise) - Time(twlt_set)).to_value('hour')

    # If lunar_illum is a percentage as a float or int, no problem
    # Otherwise, convert if needed:
    # lunar_illum_float = lunar_illum if isinstance(lunar_illum, (float,int)) else lunar_illum.to_value()

    #===Figure===
    im = Image(fig_name)
    im._restrictSize(450, 300)  # max width and height in points
    story.append(im)
    story.append(Spacer(1, 12))

    #===Info text===
    info_text = f"""
    <b>{night_str}</b><br/>
    MPC code: {mpc_code}<br/>
    Sunrise-Sunset: {sun_set.strftime('%H:%M')} - {sun_rise.strftime('%H:%M')} UT<br/>
    Twilight-Twilight: {twlt_set.strftime('%H:%M')} - {twlt_rise.strftime('%H:%M')} UT<br/>
    Night lasts: {night_length_hours:.1f} / {twilight_length_hours:.1f} hours<br/>
    Lunar Illumination: {lunar_illum_val/100:.2f}
    """
    # Create a custom style based on 'Normal'
    text_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName='Helvetica')
    story.append(Paragraph(info_text, text_style))
    story.append(Spacer(1, 12))

    #===Table===
    decimal_format = {
        'RA_str': '{}',         # Already a string, no formatting needed
        'DEC_str': '{}',        # Already a string, no formatting needed
        'Mag': '{:.2f}',        # 2 decimal places
        'Sky_motion': '{:.2f}', # 2 decimal places
        'alpha': '{:.1f}',      # 1 decimal places
        'lunar_elong': '{:.2f}',# 2 decimal place
        'target': '{}'          # string, no formatting
    }

    columns = ['target', 'duration_hours', 'RA_str', 'DEC_str', 'Mag', 'Sky_motion', 'alpha', 'lunar_elong']
    column_names = ['Target', 'T-Vis', 'RA','DEC','V/T-Mag','Sky Mot.', 'Alpha', 'T-O-M']
    data = [column_names]  # header row

    for _, row in summary_df.iterrows():
        formatted_row = []
        for col in columns:
            val = row[col]
            fmt = decimal_format.get(col, '{}')
            try:
                formatted_val = fmt.format(val)
            except Exception:
                formatted_val = str(val)
            formatted_row.append(formatted_val)
        data.append(formatted_row)
        
    table = Table(data, repeatRows=1)
    
    style = TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.black),  # under header
        ('LINEABOVE', (0, 0), (-1, 0), 0.5, colors.black),  # top rule
        ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.black),# bottom rule
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ])
    
    table.setStyle(style)
    story.append(table)

    doc.build(story)
    
    return

def create_summary_pdf(pdf_name,tmpdir_path):
    
    doc = SimpleDocTemplate(str(pdf_name), pagesize=letter,
                            rightMargin=20, leftMargin=20,
                            topMargin=20, bottomMargin=20)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="CenteredBold",
        parent=styles["Heading1"],
        alignment=1,  # 0=left, 1=center, 2=right
        fontName="Helvetica-Bold"
    )    
    
    story = []
       
    # All target summary pdf
    all_target_summary = tmpdir_path / 'all_tar_summary.png'
    
    # At top of pdf
    im = Image(all_target_summary)
    im._restrictSize(doc.width,doc.height*0.9)
    story.append(im)
    story.append(PageBreak())
    
    # Then append all other targets
    target_summaries = list(tmpdir_path.glob('summary_*'))
    for i, fig in enumerate(target_summaries):
        
        obj_name = str(fig).split('_')[-1][:-4]

        story.append(Paragraph(obj_name, title_style))
        story.append(Spacer(1, 12))
        im = Image(fig)
        im._restrictSize(doc.width, doc.height*0.9)
        story.append(im)

        # Add page break except after last figure
        if i < len(list(target_summaries)) - 1:
            story.append(PageBreak())
    
    doc.build(story)

    return