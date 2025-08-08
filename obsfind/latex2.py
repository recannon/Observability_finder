from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from astropy.time import Time

def create_pdf(twilight_times,mpc_code,lunar_illum,pdf_path):
    
    night_str = twilight_times['night'].strftime('%Y-%b-%d')
    night_str_nohyphen = twilight_times['night'].strftime('%Y%m%d')
    sun_set, sun_rise = twilight_times['sun_set'], twilight_times['sun_rise']
    twlt_set, twlt_rise = twilight_times['astronomical_set'], twilight_times['astronomical_rise']

    fig_name = f'{pdf_path}/elevation_{night_str_nohyphen}.png'
    pdf_name = f'{pdf_path}/elevation_{night_str_nohyphen}.pdf'

    doc = SimpleDocTemplate(pdf_name, pagesize=letter,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
       
    # Calculate time deltas in hours as floats
    night_length_hours = (Time(sun_rise) - Time(sun_set)).to_value('hour')
    twilight_length_hours = (Time(twlt_rise) - Time(twlt_set)).to_value('hour')

    # If lunar_illum is a percentage as a float or int, no problem
    # Otherwise, convert if needed:
    # lunar_illum_float = lunar_illum if isinstance(lunar_illum, (float,int)) else lunar_illum.to_value()

    # Add image
    im = Image(fig_name)
    im._restrictSize(450, 300)  # max width and height in points
    story.append(im)
    story.append(Spacer(1, 12))

    info_text = f"""
    <b>{night_str}</b><br/>
    MPC code: {mpc_code}<br/>
    Sunrise-Sunset: {sun_set.strftime('%H:%M')} - {sun_rise.strftime('%H:%M')} UT<br/>
    Twilight-Twilight: {twlt_set.strftime('%H:%M')} - {twlt_rise.strftime('%H:%M')} UT<br/>
    Night lasts: {night_length_hours:.1f} / {twilight_length_hours:.1f} hours<br/>
    Lunar Illumination: {lunar_illum/100:.2f}
    """
    story.append(Paragraph(info_text, styles['Normal']))
    story.append(Spacer(1, 12))

    # # Prepare table data
    # data = [['Target', 'RA', 'DEC', 'App_Mag']]
    # for _, target in twilight_times.iterrows():
    #     if target['target'] == 'Moon':
    #         continue
    #     row = [
    #         str(target['night']),
    #         str(target['sun_rise']),
    #         str(target['sun_set']),
    #         f"{target['astronomical_rise']:.2f}",
    #     ]
    #     data.append(row)

    # Create and style table
    # table = Table(data, colWidths=[70, 60, 60, 60])
    # style = TableStyle([
    #     ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    #     ('TEXTCOLOR',(0, 0), (-1, 0), colors.whitesmoke),
    #     ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    #     ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    #     ('BOTTOMPADDING', (0,0), (-1,0), 8),
    #     ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    # ])
    # table.setStyle(style)
    # story.append(table)

    # Build PDF
    doc.build(story)