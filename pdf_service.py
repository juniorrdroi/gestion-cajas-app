import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generar_pdf_remito(sede, solicitante, df_cajas_seleccionadas):
    """Genera un archivo PDF binario del remito para descargar en Streamlit."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Encabezado
    titulo_style = ParagraphStyle('Titulo', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1)
    story.append(Paragraph("REMITO DE RETIRO DE DOCUMENTACIÓN", titulo_style))
    story.append(Spacer(1, 15))

    # Metadatos del envío
    meta_text = f"""
    <b>Origen / Sede:</b> {sede}<br/>
    <b>Solicitante:</b> {solicitante}<br/>
    <b>Cantidad de Cajas:</b> {len(df_cajas_seleccionadas)}
    """
    story.append(Paragraph(meta_text, styles['Normal']))
    story.append(Spacer(1, 15))

    # Tabla de Cajas seleccionadas
    data_tabla = [["N° Caja", "Código Etiquetas", "Detalle de Contenido"]]
    for _, fila in df_cajas_seleccionadas.iterrows():
        nro = str(fila.get('nro_caja', ''))
        cod = str(fila.get('codigo_barra', ''))
        cont = str(fila.get('contenido', ''))
        data_tabla.append([nro, cod, cont])

    t = Table(data_tabla, colWidths=[80, 120, 340])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#004085')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 40))

    # Bloque para firmas físicas
    firmas_data = [
        ["____________________________", "____________________________"],
        ["Firma del Retirante (Transporte)", "Firma del Entregante (Sede)"],
        ["Aclaración: ", "Aclaración: "],
        ["DNI: ", "DNI: "]
    ]
    t_firmas = Table(firmas_data, colWidths=[270, 270])
    t_firmas.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('FONTSIZE', (0, 0), (-1, -1), 9)]))
    story.append(t_firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()