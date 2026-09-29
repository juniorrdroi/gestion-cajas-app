import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Diccionario centralizado de correos por sede
MAILS_SEDES = {
    'Casa Central': 'archivocentral@tuempresa.com',
    'Azcuénaga': 'soporte@gedyt.com.ar',
    'Facturación': 'soporte@gedyt.com.ar',
    'RRHH': 'soporte@gedyt.com.ar',
    'Contabilidad': 'soporte@gedyt.com.ar',
    'Ineba Endoscopia': 'soporte@gedyt.com.ar',
    'Finochietto': 'soporte@gedyt.com.ar',
    'Compras': 'soporte@gedyt.com.ar',
    'Tesorería': 'soporte@gedyt.com.ar',
    'Santa Fe': 'soporte@gedyt.com.ar',
    'Vof': 'soporte@gedyt.com.ar',
    'Fleming': 'soporte@gedyt.com.ar',
    'Juncal PB': 'soporte@gedyt.com.ar',
    'Itac': 'soporte@gedyt.com.ar',
    'Ineba 3P': 'soporte@gedyt.com.ar',
    'Default': 'soporte@gedyt.com.ar' # Correo por defecto si no matchea
}

def enviar_notificacion_email(nro_caja, sede, solicitante, periodo, contenido, codigo_barra=""):
    """
    Envía una notificación por mail al destinatario correspondiente según la sede.
    """
    # Se busca el mail de la sede o se usa el de Casa Central por defecto
    destinatario = MAILS_SEDES.get(sede, MAILS_SEDES['Default'])

    # Configuración de tu servidor SMTP (Ejemplo con Microsoft 365 / Outlook)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "soporte@gedyt.com.ar"
    sender_password = "poch apgx sgfh dfpi"

    asunto = f"📦 Alta de Caja N° {nro_caja} - Sede: {sede}"
    cuerpo = f"""
    Hola,

    Se ha completado la registración de contenido para una nueva caja:

    • N° Caja Interno: {nro_caja}
    • Código / Etiqueta: {codigo_barra or 'Sin código'}
    • Sede / Departamento: {sede}
    • Solicitante: {solicitante}
    • Período Documental: {periodo}
    • Detalle Contenido: {contenido}

    Saludos,
    Sistema de Gestión de Archivo
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar correo a {destinatario}: {e}")
        return False