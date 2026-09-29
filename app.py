# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
import base64
from pdf_service import generar_pdf_remito

from email_service import enviar_notificacion_email
from database import (
    init_db, migrar_desde_excel, autenticar_usuario, obtener_usuarios_por_sede,
    obtener_cajas, insertar_caja, actualizar_caja, eliminar_caja,
    vincular_codigo_barra, obtener_caja_por_identificador,
    obtener_estadisticas, obtener_cajas_como_dataframe, obtener_cajas_por_sede,
    siguiente_nro_caja, registrar_actividad, obtener_log,
    solicitar_retiro_masivo_cajas, registrar_log_envio,
    reiniciar_base_de_pruebas, crear_pedido_cajas, obtener_pedidos_cajas, 
    actualizar_estado_pedido, registrar_etiqueta_proveedor, obtener_etiquetas_disponibles,
    despachar_pedido_con_etiquetas, obtener_cajas_pendientes_de_llenar
)

from auditoria import (
    auditar_con_datos_reales,
    SOLICITANTES_OK, SEDES_DPTOS_OK, SEDES_SOLICITANTES, ESTADOS_OK
)

st.set_page_config(
    page_title="Gestión de Archivo y Cajas - Gedyt",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

@st.cache_resource
def bootstrap_ambos_entornos():
    init_db(entorno="produccion")
    init_db(entorno="pruebas")
    
    excel_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'importar_cajas.xlsx')
    #if os.path.exists(excel_path):
    # Imprimimos la ruta exacta que está buscando para ver el error
    print(f"🔍 Buscando el archivo Excel exactamente en: {excel_path}")

    migrar_desde_excel(excel_path, entorno="produccion")

    return True

bootstrap_ambos_entornos()

if 'entorno' not in st.session_state:
    st.session_state['entorno'] = 'produccion'

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

LOGO_B64 = get_base64_image("logo_gedyt.png")

# ==============================================================================
# ESTILOS CSS CON TIPOGRAFÍAS CORPORATIVAS
# ==============================================================================
st.markdown('''
<style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Source+Sans+Pro:wght@400;600&display=swap');

    .stApp {
        background-color: #FFFFFF;
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6, .main-title {
        font-family: 'Montserrat', sans-serif !important;
        color: #1E3E6B !important;
        font-weight: 700 !important;
    }
    
    .env-banner-prod {
        background: linear-gradient(90deg, #1E3E6B, #2d5893);
        color: #FFFFFF; padding: 8px 16px; border-radius: 8px;
        font-weight: 700; font-size: 0.85rem; display: inline-block; margin-bottom: 14px;
        font-family: 'Montserrat', sans-serif; letter-spacing: 0.5px;
    }
    .env-banner-test {
        background: linear-gradient(90deg, #71BAB4, #539d97);
        color: #FFFFFF; padding: 8px 16px; border-radius: 8px;
        font-weight: 700; font-size: 0.85rem; display: inline-block; margin-bottom: 14px;
        font-family: 'Montserrat', sans-serif; letter-spacing: 0.5px;
    }

    .metric-card {
        background-color: #FEFCF3; border-radius: 12px; padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        border: 1px solid #E0DFDE; border-left: 6px solid #1E3E6B;
        margin-bottom: 12px; transition: transform 0.2s ease;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-card.success { border-left-color: #71BAB4; }
    .metric-card.warning { border-left-color: #d99a38; }
    .metric-card.purple { border-left-color: #5c4e8c; }

    .metric-title { font-size: 0.82rem; font-weight: 700; text-transform: uppercase; color: #1E3E6B; margin-bottom: 6px; font-family: 'Montserrat', sans-serif; }
    .metric-value { font-size: 2.1rem; font-weight: 800; color: #1E3E6B; line-height: 1.1; font-family: 'Montserrat', sans-serif; }
    .metric-subtitle { font-size: 0.80rem; color: #64748b; margin-top: 6px; font-family: 'Source Sans Pro', sans-serif; }

    div.stButton > button,
    div.stFormSubmitButton > button {
        background-color: #1E3E6B !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:hover,
    div.stFormSubmitButton > button:hover {
        background-color: #71BAB4 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 8px rgba(30, 62, 107, 0.25) !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #FEFCF3 !important;
        border-right: 1px solid #E0DFDE !important;
        font-family: 'Source Sans Pro', sans-serif !important;
    }

    .gedyt-header-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        margin-bottom: 15px;
    }
    .gedyt-logo-img {
        height: 65px;
        width: auto;
    }
    .gedyt-text-block {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
    }
    .gedyt-brand-title {
        font-family: 'Montserrat', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        color: #1E3E6B;
        line-height: 0.9;
        margin: 0;
    }
    .gedyt-brand-sub {
        font-family: 'Source Sans Pro', sans-serif;
        font-size: 0.88rem;
        color: #1E3E6B;
        font-weight: 600;
        border-top: 1.5px solid #1E3E6B;
        padding-top: 2px;
        margin-top: 4px;
        letter-spacing: 0.2px;
    }
</style>
''', unsafe_allow_html=True)

def mostrar_banner_entorno():
    entorno = st.session_state['entorno']
    if entorno == "produccion":
        st.markdown('<div class="env-banner-prod">🟢 ENTORNO DE PRODUCCIÓN (Datos Reales)</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="env-banner-test">🟡 MODO DE PRUEBAS / SIMULACIÓN (Datos de Test)</div>', unsafe_allow_html=True)

def render_logo_header(size="normal"):
    img_tag = f'<img src="data:image/png;base64,{LOGO_B64}" class="gedyt-logo-img" style="height: {"65px" if size=="normal" else "45px"};" />' if LOGO_B64 else ''
    font_size = "2.8rem" if size=="normal" else "1.9rem"
    sub_size = "0.88rem" if size=="normal" else "0.70rem"
    
    st.markdown(f'''
        <div class="gedyt-header-container">
            {img_tag}
            <div class="gedyt-text-block">
                <span class="gedyt-brand-title" style="font-size: {font_size};">Gedyt</span>
                <span class="gedyt-brand-sub" style="font-size: {sub_size};">Gastroenterología Diagnóstica y Terapéutica</span>
            </div>
        </div>
    ''', unsafe_allow_html=True)

# ==============================================================================
# LOGIN CON SELECCIÓN LIBRE DE ENTORNO
# ==============================================================================
def mostrar_login():
    st.markdown('<div style="margin-top:30px; margin-bottom:10px;">', unsafe_allow_html=True)
    render_logo_header(size="normal")
    st.markdown('<h2 style="text-align:center; color:#1E3E6B; margin-top:15px; font-size: 1.8rem;">Gestión de Archivo y Custodia</h2><p style="text-align:center; color:#64748b; font-size:1.1rem; margin-top:-10px;">Casa Central</p></div>', unsafe_allow_html=True)
    
    _, col_login, _ = st.columns([1, 1.8, 1])
    with col_login:
        st.markdown("### 🔐 Iniciar Sesión")
        
        entorno_sel = st.selectbox(
            "🌍 Seleccionar Entorno de Trabajo:",
            ["🟢 Producción (Datos Reales)", "🟡 Modo Pruebas / Simulación"],
            index=0 if st.session_state['entorno'] == 'produccion' else 1
        )
        st.session_state['entorno'] = 'produccion' if "Producción" in entorno_sel else 'pruebas'

        with st.form("login_form"):
            username = st.text_input("👤 Usuario", placeholder="admin_central, azcuenaga, rrhh...")
            password = st.text_input("🔑 Contraseña", type="password", placeholder="Tu contraseña...")
            submit = st.form_submit_button("Ingresar", use_container_width=True, type="primary")
            
            if submit:
                user = autenticar_usuario(username, password, entorno=st.session_state['entorno'])
                if user:
                    st.session_state['usuario'] = user
                    st.session_state['logged_in'] = True
                    registrar_actividad(username, 'LOGIN', f"Inicio de sesión en {st.session_state['entorno']}", entorno=st.session_state['entorno'])
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos en este entorno.")

def cerrar_sesion():
    if 'usuario' in st.session_state:
        registrar_actividad(st.session_state['usuario']['username'], 'LOGOUT', 'Cierre de sesión', entorno=st.session_state['entorno'])
    for key in ['usuario', 'logged_in']:
        st.session_state.pop(key, None)
    st.rerun()

# ==============================================================================
# SIDEBAR
# ==============================================================================
def mostrar_sidebar(usuario):
    with st.sidebar:
        render_logo_header(size="small")
        st.caption("Casa Central")

        st.caption("⚙️ ENTORNO ACTIVO:")
        opcion_entorno = st.radio(
            "Cambiar Entorno:",
            ["🟢 Producción", "🟡 Pruebas"],
            index=0 if st.session_state['entorno'] == 'produccion' else 1,
            label_visibility="collapsed"
        )
        nuevo_val = 'produccion' if "Producción" in opcion_entorno else 'pruebas'
        if nuevo_val != st.session_state['entorno']:
            st.session_state['entorno'] = nuevo_val
            st.rerun()

        st.markdown("---")

        if usuario['rol'] in ['admin', 'admin_sede_central']:
            tipo_admin = "Admin Sede Central" if usuario['rol'] == 'admin_sede_central' else "Admin Master"
            st.markdown(f"**🛡️ {tipo_admin}:** {usuario['nombre_completo']}")
            modulo = st.radio(
                "📌 Módulo:",
                [
                    "📊 Dashboard General", 
                    "✅ Verificación y Precintos", 
                    "🚚 Pedidos de Cajas a Sedes",
                    "🏷️ Stock de Insumos (Etiquetas y Precintos)", 
                    "📋 Gestión de Cajas", 
                    "➕ Cargar Caja", 
                    "🔍 Auditoría Master", 
                    "📜 Log de Actividad"
                ]
            )
            
            if st.session_state['entorno'] == 'pruebas':
                st.markdown("---")
                if st.button("🔄 Restaurar Datos de Prueba", use_container_width=True):
                    reiniciar_base_de_pruebas()
                    st.toast("Datos de prueba restaurados a su estado inicial.", icon="🔄")
                    st.rerun()
        else:
            st.markdown(f"**👤 Operador:** {usuario['nombre_completo']}")
            st.caption(f"📍 Sede: **{usuario['sede_asignada']}**")
            modulo = st.radio("📌 Módulo:", ["📋 Mis Cajas", "➕ Cargar Contenido a Caja Enviada", "📦 Solicitar Cajas a Sede"])

        st.markdown("---")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            cerrar_sesion()
        return modulo

def mostrar_kpis(stats):
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(f'<div class="metric-card"><div class="metric-title">📄 Total Cajas</div><div class="metric-value">{stats["total"]}</div><div class="metric-subtitle">En este entorno</div></div>', unsafe_allow_html=True)
    with k2: st.markdown(f'<div class="metric-card success"><div class="metric-title">✅ Completadas</div><div class="metric-value">{stats["completadas"]}</div><div class="metric-subtitle">Listas para acopio</div></div>', unsafe_allow_html=True)
    with k3: st.markdown(f'<div class="metric-card warning"><div class="metric-title">⏳ Pendientes</div><div class="metric-value">{stats["pendientes"]}</div><div class="metric-subtitle">Pendientes de entrega</div></div>', unsafe_allow_html=True)
    with k4: st.markdown(f'<div class="metric-card purple"><div class="metric-title">📦 No Asignadas</div><div class="metric-value">{stats["no_asignadas"]}</div><div class="metric-subtitle">Sin sede fija</div></div>', unsafe_allow_html=True)

# ==============================================================================
# VISTAS
# ==============================================================================
def formulario_carga(usuario, sede_fija=None):
    mostrar_banner_entorno()
    st.subheader("➕ Registrar Contenido de Caja")
    es_admin = (usuario['rol'] in ['admin', 'admin_sede_central'])
    sede_actual = sede_fija if sede_fija else usuario.get('sede_asignada', 'Casa Central')

    if not es_admin:
        cajas_pendientes = obtener_cajas_pendientes_de_llenar(sede_actual, entorno=st.session_state['entorno'])
        if not cajas_pendientes:
            st.info("ℹ️ No tienes cajas enviadas por Casa Central pendientes de cargar contenido. Si necesitas más insumos, solicita un pedido en '📦 Solicitar Cajas a Sede'.")
            return
        
        st.write("Selecciona la caja que recibiste físicamente para completar sus datos:")
        
        mapeo_cajas = {
            f"Etiqueta/Caja: {c['codigo_barra']} (N° Interno: {c['nro_caja']}) - Precintos: {c.get('precinto_inicio','')}/{c.get('precinto_fin','')}": c 
            for c in cajas_pendientes
        }
        sel_caja_key = st.selectbox("📦 Cajas recibidas en tu sede pendientes de carga:", list(mapeo_cajas.keys()))
        caja_sel = mapeo_cajas[sel_caja_key]

        with st.form("form_carga_operador", clear_on_submit=True):
            f1, f2 = st.columns(2)
            with f1:
                solics = SEDES_SOLICITANTES.get(sede_actual, SOLICITANTES_OK)
                solicitante = st.selectbox("👤 Solicitante / Responsable:", solics)
                
                # 1. OBSERVACIONES (Arriba - 1 línea)
                obs = st.text_input("📝 Observaciones:", placeholder="Notas o aclaraciones adicionales...")
                
                # 2. CALENDARIOS OBLIGATORIOS OPERADOR
                st.markdown("#### 📅 Período de la Documentación (Obligatorio)")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_desde = st.date_input("Fecha Desde *", value=None, format="DD/MM/YYYY")
                with col_f2:
                    fecha_hasta = st.date_input("Fecha Hasta *", value=None, format="DD/MM/YYYY")

            with f2:
                st.caption("🔒 Precintos asignados por Casa Central para este kit:")
                p1 = st.text_input("🔢 Precinto 1:", value=caja_sel.get('precinto_inicio', ''), help="Precinto enviado en el sobre por Casa Central")
                p2 = st.text_input("🔢 Precinto 2:", value=caja_sel.get('precinto_fin', ''), help="Precinto enviado en el sobre por Casa Central")
                
           # 3. CONTENIDO DETALLADO (Abajo - Más amplio)
            contenido = st.text_area("📂 Contenido detallado:", placeholder="Ej: Facturas Historias Clínicas...", height=120)

            # Definición de la ventana emergente de confirmación (dialog)
            # Definición de la ventana emergente de confirmación (dialog)
            # Definición de la ventana emergente (modal)
            @st.dialog("⚠️ Confirmar Registro de Contenido")
            def confirmar_envio_dialog(datos_caja):
                st.warning("Por favor revisá los datos antes de guardar de forma definitiva:")
                st.markdown(f"**📦 Caja N°:** `{datos_caja['nro_caja']}`")
                st.markdown(f"**🏷️ Etiqueta:** `{datos_caja['codigo_barra'] or 'Sin etiqueta'}`")
                st.markdown(f"**👤 Solicitante:** {datos_caja['solicitante']}")
                st.markdown(f"**📅 Período:** {datos_caja['f_desde_str']} al {datos_caja['f_hasta_str']}")
                st.markdown(f"**📂 Contenido:** {datos_caja['contenido']}")
                st.markdown(f"**📝 Observaciones:** {datos_caja['obs'] or 'Sin observaciones'}")
                st.markdown("---")
                
                # Columnas para organizar los botones de acción
                col_b1, col_b2 = st.columns(2)
                
                with col_b1:
                    # Uso de width="stretch" para eliminar la advertencia de Streamlit
                    if st.button("✅ Confirmar y Guardar", type="primary", key="btn_modal_confirmar", width="stretch"):
                        # 1. Guardar datos en la BD
                        actualizar_caja(datos_caja['nro_caja'], {
                            'codigo_barra': datos_caja['codigo_barra'],
                            'sede_dpto': datos_caja['sede_actual'],
                            'solicitante': datos_caja['solicitante'],
                            'contenido': datos_caja['contenido_completo'],
                            'precinto_inicio': datos_caja['p1'],
                            'precinto_fin': datos_caja['p2'],
                            'estado': 'pendiente de entrega',
                            'observaciones': datos_caja['obs'],
                            'modificado_por': usuario['username']
                        }, entorno=st.session_state['entorno'])

                        # 2. Envío de e-mail de notificación
                        try:
                            mail_exito = enviar_notificacion_email(
                                nro_caja=datos_caja['nro_caja'],
                                sede=datos_caja['sede_actual'],
                                solicitante=datos_caja['solicitante'],
                                periodo=f"{datos_caja['f_desde_str']} al {datos_caja['f_hasta_str']}",
                                contenido=datos_caja['contenido'],
                                codigo_barra=datos_caja['codigo_barra']
                            )
                            if mail_exito:
                                st.toast("✅ Guardado y notificación enviada por e-mail.", icon="📦")
                            else:
                                st.toast("⚠️ Guardado en BD, pero no se pudo enviar el e-mail.", icon="📩")
                        except Exception as e:
                            print(f"❌ Error en envío de correo: {e}")
                            st.toast("⚠️ Guardado en BD correctamente.", icon="💾")

                        # 3. Forzar el cierre de la ventana y refrescar la app
                        st.rerun()

                with col_b2:
                    if st.button("❌ Cancelar", key="btn_modal_cancelar", width="stretch"):
                        st.rerun()

            # Botón del formulario principal y validaciones
            if st.form_submit_button("💾 Guardar Contenido de Caja", use_container_width=True, type="primary"):
                # Validaciones del Operador
                if not contenido.strip():
                    st.error("⚠️ Completá el detalle del contenido.")
                elif fecha_desde is None:
                    st.error("⚠️ Seleccioná la **Fecha Desde** de la documentación.")
                elif fecha_hasta is None:
                    st.error("⚠️ Seleccioná la **Fecha Hasta** de la documentación.")
                elif fecha_hasta < fecha_desde:
                    st.error("⚠️ La **Fecha Hasta** no puede ser anterior a la **Fecha Desde**.")
                else:
                    f_desde_str = fecha_desde.strftime("%d/%m/%Y")
                    f_hasta_str = fecha_hasta.strftime("%d/%m/%Y")
                    contenido_completo = f"{contenido.strip()} [Período: {f_desde_str} al {f_hasta_str}]"

                    # Despliega el modal emergente de confirmación
                    confirmar_envio_dialog({
                        'nro_caja': caja_sel['nro_caja'],
                        'codigo_barra': caja_sel['codigo_barra'],
                        'sede_actual': sede_actual,
                        'solicitante': solicitante,
                        'contenido': contenido.strip(),
                        'contenido_completo': contenido_completo,
                        'f_desde_str': f_desde_str,
                        'f_hasta_str': f_hasta_str,
                        'p1': (p1 or '').strip(),
                        'p2': (p2 or '').strip(),
                        'obs': (obs or '').strip()
                    })
    else:
        # 1. Sacamos la elección de Sede AFUERA del formulario para que sea dinámica
        sede_sel = st.selectbox("🏢 Sede / Departamento:", SEDES_DPTOS_OK)
        
        # 2. Filtramos los solicitantes basados en la sede elegida
        solics = SEDES_SOLICITANTES.get(sede_sel, SOLICITANTES_OK)
        
        # 3. Abrimos el formulario para el resto de los datos a cargar
        with st.form("form_nueva_caja_admin", clear_on_submit=True):
            f1, f2 = st.columns(2)
            
            with f1:
                # Las opciones de 'solics' ya están actualizadas correctamente
                solicitante = st.selectbox("👤 Solicitante:", solics)
                contenido = st.text_input("📂 Contenido:", placeholder="Ej: Facturas Mayo 2024")
                
            # (Acá seguramente tenés tu columna f2 con los precintos y el st.form_submit_button)
                
                # --- CALENDARIOS OBLIGATORIOS ADMIN ---
                st.markdown("#### 📅 Período de la Documentación (Obligatorio)")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    fecha_desde_adm = st.date_input("Fecha Desde *", value=None, format="DD/MM/YYYY", key="adm_fd")
                with col_f2:
                    fecha_hasta_adm = st.date_input("Fecha Hasta *", value=None, format="DD/MM/YYYY", key="adm_fh")

            with f2:
                nro_caja = st.text_input("📦 Nº de Caja (Interno):", value=siguiente_nro_caja(entorno=st.session_state['entorno']))
                codigo_barra = st.text_input("🏷️ Código de Barra / Etiqueta Proveedor:")
                p1, p2 = st.columns(2)
                with p1: p_ini = st.text_input("🔢 Precinto 1:")
                with p2: p_fin = st.text_input("🔢 Precinto 2:")
                
            obs = st.text_area("📝 Observaciones:")

            if st.form_submit_button("💾 Guardar Caja Directa", use_container_width=True, type="primary"):
                # Validaciones del Admin
                if not contenido.strip() or not nro_caja.strip():
                    st.error("Completá contenido y número de caja.")
                elif fecha_desde_adm is None:
                    st.error("⚠️ Seleccioná la **Fecha Desde** de la documentación.")
                elif fecha_hasta_adm is None:
                    st.error("⚠️ Seleccioná la **Fecha Hasta** de la documentación.")
                elif fecha_hasta_adm < fecha_desde_adm:
                    st.error("⚠️ La **Fecha Hasta** no puede ser anterior a la **Fecha Desde**.")
                else:
                    f_desde_str = fecha_desde_adm.strftime("%d/%m/%Y")
                    f_hasta_str = fecha_hasta_adm.strftime("%d/%m/%Y")
                    contenido_completo = f"{contenido.strip()} [Período: {f_desde_str} al {f_hasta_str}]"

                    ok = insertar_caja({
                        'nro_caja': nro_caja.strip(),
                        'codigo_barra': codigo_barra.strip(),
                        'sede_dpto': sede_sel,
                        'solicitante': solicitante,
                        'contenido': contenido_completo,
                        'precinto_inicio': p_ini.strip(),
                        'precinto_fin': p_fin.strip(),
                        'estado': 'completada',
                        'observaciones': obs.strip(),
                        'cargado_por': usuario['username']
                    }, entorno=st.session_state['entorno'])
                    if ok:
                        st.toast(f"✅ Caja {nro_caja} registrada correctamente.", icon="📦")
                        st.rerun()
                    else:
                        st.error("❌ Ya existe una caja con ese número.")

def vista_operador_solicitar_cajas(usuario):
    mostrar_banner_entorno()
    st.title("📦 Solicitar Envío de Cajas a Sede")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📝 Nuevo Pedido de Cajas")
        with st.form("form_pedido_cajas", clear_on_submit=True):
            # Diccionario con el personal asignado a cada sede
            INTEGRANTES_POR_SEDE = {
                "Azcuénaga": ["Soledad Massat", "Tania Lopez"],
                "Facturación": ["Verónica Scapin", "Pamela Cortez"],
                "RRHH": ["Candela García", "Miranda Caruso"],
                "Ineba Endoscopia": ["Celeste Rodriguez"],
                "Finochietto": ["Carla Maciel"],
                "Compras": ["Valeria Moreno"],
                "Santa Fe": ["Verónica Martinez", "Kalil Marpez"],
                "Vof": ["Cynthia Rosales", "Matías Conte"],
                "Fleming": ["Mariela Mashchio"],
                "Juncal PB": ["Vilma Rodriguez"],
                "Itac": ["Celeste Llanos"],
                "Ineba 3P": ["Florencia Meza"]
            }

            # Obtener integrantes según la sede asignada al usuario
            raw_actual = usuario.get('sede_asignada', '').lower().replace("operador", "").strip()

            #Buscar coincidencia parcial si la sede tiene nombres compuestos
            opciones_solicitantes = [usuario.get('nombre_completo', '')]

            for clave_sede, integrantes in INTEGRANTES_POR_SEDE.items():
                clave_normalizada = clave_sede.lower().strip()

                if clave_normalizada in raw_actual or raw_actual in clave_normalizada:
                    opciones_solicitantes = integrantes
                    break

            #st.write("DEBUG - sede:", raw_actual)
            #st.write("DEBUG - opciones:", opciones_solicitantes)

            #INTEGRANTES_POR_SEDE.get(sede_actual, [usuario['nombre_completo']])

            usr_especifico = st.selectbox(
                "👤 Solicitante Individual / Responsable:",
                options=opciones_solicitantes,
                help="Seleccioná al responsable precargado dentro de tu sede"
            )

            cantidad = st.number_input("📦 Cantidad de Cajas requeridas:", min_value=1, max_value=100, value=1, step=1)
            
            # 🛍️ INSUMOS ADICIONALES (Opciones siempre editables)
            st.write("🛍️ **Insumos Adicionales (Ingresá cantidad o dejá en 0):**")
            
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                cant_bolsas = st.number_input(
                    "🛍️ Cantidad de Bolsas de Seguridad:",
                    min_value=0,
                    max_value=100,
                    value=0,
                    step=1,
                    help="Dejá en 0 si no necesitás bolsas"
                )

            with col_b2:
                cant_tapas = st.number_input(
                    "📦 Cantidad de Tapas Adicionales:",
                    min_value=0,
                    max_value=100,
                    value=0,
                    step=1,
                    help="Dejá en 0 si no necesitás tapas"
                )

            motivo = st.text_area("📝 Motivo / Observaciones:", placeholder="Ej: Cierre de facturación mensual...")
            
            # Único botón de envío dentro del formulario
            submit_pedido = st.form_submit_button("🚀 Enviar Pedido de Cajas", type="primary", width="stretch")

        # Procesamiento del formulario al presionar el botón
        if submit_pedido:
            if not usr_especifico.strip():
                st.error("Por favor ingresá el nombre del solicitante.")
            else:
                # Filtrar solo si la cantidad es mayor a 0
                insumos = []
                if cant_bolsas > 0:
                    insumos.append(f"Bolsas (x{cant_bolsas})")
                if cant_tapas > 0:
                    insumos.append(f"Tapas (x{cant_tapas})")
                
                detalle_insumos = ", ".join(insumos) if insumos else "Sin adicionales"
                
                motivo_limpio = motivo.strip()
                motivo_final = f"{motivo_limpio} | Insumos: {detalle_insumos}" if motivo_limpio else f"Insumos: {detalle_insumos}"

                crear_pedido_cajas(
                    usuario=usr_especifico.strip(),
                    sede=usuario['sede_asignada'],
                    cantidad=int(cantidad),
                    motivo=motivo_final,
                    entorno=st.session_state['entorno']
                )
                
                st.toast(f"✅ Pedido registrado correctamente.", icon="📦")
                st.rerun()

    with col2:
        st.subheader("📋 Pedidos Realizados")
        pedidos = obtener_pedidos_cajas(sede=usuario['sede_asignada'], entorno=st.session_state['entorno'])
        if pedidos:
            df_p = pd.DataFrame(pedidos)
            st.dataframe(
                df_p[['id', 'usuario_solicitante', 'cantidad', 'motivo', 'estado', 'fecha_pedido']],
                width="stretch"
            )
        else:
            st.info("No hay pedidos registrados para tu sede.")

def vista_admin_pedidos_cajas():
    mostrar_banner_entorno()
    st.title("🚚 Pedidos de Cajas y Despacho con Etiquetas (Casa Central)")
    st.markdown("---")

    pedidos = obtener_pedidos_cajas(entorno=st.session_state['entorno'])
    
    if not pedidos:
        st.success("🎉 No hay solicitudes de envío de cajas actualmente.")
        return

    df_p = pd.DataFrame(pedidos)
    st.dataframe(df_p[['id', 'sede_dpto', 'usuario_solicitante', 'cantidad', 'motivo', 'estado', 'fecha_pedido']], use_container_width=True)

    pendientes = [p for p in pedidos if p['estado'] == 'pendiente']
    if pendientes:
        st.subheader("📦 Seleccionar Kits de Stock (Etiqueta + Precintos) y Despachar")
        
        mapeo_p = {f"Pedido #{p['id']} - {p['sede_dpto']} ({p['cantidad']} cajas para {p['usuario_solicitante']})": p for p in pendientes}
        sel_ped = st.selectbox("Seleccionar Pedido a Despachar:", list(mapeo_p.keys()))
        target = mapeo_p[sel_ped]

        etiquetas_libres = obtener_etiquetas_disponibles(entorno=st.session_state['entorno'])

        if not etiquetas_libres:
            st.warning("⚠️ No hay kits de insumos (etiquetas + precintos) disponibles en stock para asignar. Por favor carga insumos en el módulo '🏷️ Stock de Insumos' antes de despachar.")
            return

        mapeo_etiquetas = {
            f"Etiqueta: {e['nro_caja_proveedor']} | {e['codigo_barra']} (Precintos: {e.get('precinto_1','S/P')} / {e.get('precinto_2','S/P')})": e['id'] 
            for e in etiquetas_libres
        }

        with st.form("form_despacho_kit"):
            st.info(f"📍 **Sede Destino:** {target['sede_dpto']} | 👤 **Solicitante:** {target['usuario_solicitante']} | 📦 **Requeridas:** {target['cantidad']} cajas")
            
            etiquetas_seleccionadas = st.multiselect(
                f"🏷️ Selecciona exactamente {target['cantidad']} kit(s) de insumos del stock para meter en el sobre enviado:",
                options=list(mapeo_etiquetas.keys())
            )
            
            c1, c2 = st.columns(2)
            with c1:
                if st.form_submit_button("🚚 Aprobar y Despachar Cajas Asignadas", type="primary", use_container_width=True):
                    if len(etiquetas_seleccionadas) == 0:
                        st.error("Debes seleccionar al menos un kit de insumos para despachar.")
                    else:
                        ids_etiquetas = [mapeo_etiquetas[e] for e in etiquetas_seleccionadas]
                        despachar_pedido_con_etiquetas(
                            pedido_id=target['id'],
                            etiquetas_ids=ids_etiquetas,
                            admin_usr=st.session_state['usuario']['username'],
                            entorno=st.session_state['entorno']
                        )
                        st.toast(f"✅ Pedido #{target['id']} despachado con {len(ids_etiquetas)} kits asociados.", icon="🚚")
                        st.rerun()
            with c2:
                if st.form_submit_button("❌ Rechazar Pedido", use_container_width=True):
                    actualizar_estado_pedido(target['id'], 'rechazado', st.session_state['usuario']['username'], entorno=st.session_state['entorno'])
                    st.toast(f"Pedido #{target['id']} RECHAZADO.", icon="❌")
                    st.rerun()

def vista_admin_verificacion():
    mostrar_banner_entorno()
    st.title("✅ Verificación, Precintos y Etiquetas")
    st.markdown("---")
    
    cajas = obtener_cajas(entorno=st.session_state['entorno'])
    pendientes = [c for c in cajas if c.get('estado') != 'completada']
    
    if not pendientes:
        st.success("🎉 ¡Todas las cajas registradas se encuentran verificadas y completadas!")
        return

    st.subheader(f"📋 Cajas Pendientes de Verificación ({len(pendientes)})")
    mapeo = {f"Caja N° {c['nro_caja']} - {c['sede_dpto']} ({c['contenido'][:30]}...)": c for c in pendientes}
    sel_key = st.selectbox("Seleccioná la caja a auditar/verificar:", list(mapeo.keys()))
    caja_target = mapeo[sel_key]

    st.info(f"👤 **Cargado por:** {caja_target.get('cargado_por', 'S/D')} | 📍 **Sede:** {caja_target['sede_dpto']} | 👤 **Solicitante:** {caja_target['solicitante']}")
    
    with st.form("form_verificar_admin"):
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("Contenido cargado:", value=caja_target['contenido'], disabled=True)
            obs = st.text_area("Observaciones:", value=caja_target.get('observaciones', ''))
        with c2:
            cod_barra = st.text_input("🏷️ Asignar Código de Barra / Etiqueta Proveedor:", value=caja_target.get('codigo_barra', ''))
            p_ini = st.text_input("🔢 Precinto 1:", value=caja_target.get('precinto_inicio', ''))
            p_fin = st.text_input("🔢 Precinto 2:", value=caja_target.get('precinto_fin', ''))
            nuevo_estado = st.selectbox("Estado de la caja:", ESTADOS_OK, index=1 if caja_target.get('estado') != 'completada' else 0)

        if st.form_submit_button("💾 Guardar Verificación y Precintos", type="primary", use_container_width=True):
            actualizar_caja(caja_target['nro_caja'], {
                'sede_dpto': caja_target['sede_dpto'],
                'solicitante': caja_target['solicitante'],
                'contenido': caja_target['contenido'],
                'codigo_barra': cod_barra.strip(),
                'precinto_inicio': p_ini.strip(),
                'precinto_fin': p_fin.strip(),
                'estado': nuevo_estado,
                'observaciones': obs.strip(),
                'modificado_por': st.session_state['usuario']['username']
            }, entorno=st.session_state['entorno'])
            
            st.toast(f"✅ Caja {caja_target['nro_caja']} actualizada y verificada.", icon="✅")
            st.rerun()

def vista_admin_codigos_proveedor():
    mostrar_banner_entorno()
    st.title("🏷️ Stock de Insumos (Etiquetas Archibaires y Precintos)")
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["➕ Ingresar Insumos a Stock", "📦 Stock Disponible", "🔍 Consultar / Escanear"])

    with tab1:
        st.subheader("📥 Cargar Etiquetas y Precintos (Sin asignar a caja)")
        st.caption("Pasa la pistola escáner para cargar la etiqueta e ingresa los dos precintos de seguridad que irán en el sobre enviado.")
        
        with st.form("form_alta_stock_etiquetas", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nro_prov = st.text_input("📦 N° de Caja Archibaires (ej: 2904):")
                p1 = st.text_input("🔢 Precinto 1 (ej: 100501):")
            with col2:
                cod_barra = st.text_input("🏷️ Código de Barra (Lectura con Pistola - ej: 856141):")
                p2 = st.text_input("🔢 Precinto 2 (ej: 100502):")
            
            if st.form_submit_button("💾 Guardar Kit de Insumos en Stock", type="primary", use_container_width=True):
                if cod_barra.strip():
                    ok = registrar_etiqueta_proveedor(
                        nro_prov=nro_prov.strip(), 
                        cod_barra=cod_barra.strip(), 
                        precinto_1=p1.strip(),
                        precinto_2=p2.strip(),
                        usuario=st.session_state['usuario']['username'], 
                        entorno=st.session_state['entorno']
                    )
                    if ok:
                        st.toast(f"✅ Kit Etiqueta {nro_prov} | {cod_barra} guardado con precintos.", icon="🏷️")
                        st.rerun()
                    else:
                        st.error("⚠️ Ese código de barras ya se encuentra registrado en el sistema.")
                else:
                    st.error("Escanea o ingresa al menos el código de barras.")

    with tab2:
        st.subheader("📋 Kits de Insumos Listos para Enviar a Sedes")
        etiquetas = obtener_etiquetas_disponibles(entorno=st.session_state['entorno'])
        if etiquetas:
            df_e = pd.DataFrame(etiquetas)
            st.dataframe(df_e[['id', 'nro_caja_proveedor', 'codigo_barra', 'precinto_1', 'precinto_2', 'estado', 'fecha_carga']], use_container_width=True)
        else:
            st.info("No hay insumos en stock. Escanea nuevas etiquetas y precintos en la pestaña 'Ingresar Insumos a Stock'.")

    with tab3:
        cod_busc = st.text_input("🔍 Escaneá un código con la pistola para verificar su estado:")
        if cod_busc.strip():
            res = obtener_caja_por_identificador(cod_busc.strip(), entorno=st.session_state['entorno'])
            if res:
                st.success(f"✅ Caja Asignada N°: {res['nro_caja']} | Proveedor Archibaires: {res.get('codigo_barra','S/N')}")
                st.write(f"**Sede:** {res['sede_dpto']} | **Solicitante:** {res['solicitante']} | **Estado:** {res['estado']}")
                st.write(f"**Precinto 1:** {res.get('precinto_inicio','S/P')} | **Precinto 2:** {res.get('precinto_fin','S/P')}")
                st.text_area("Contenido:", value=res['contenido'], disabled=True)
            else:
                st.info("Esa etiqueta no está asignada a ninguna caja con contenido aún (se encuentra libre en stock).")

def vista_operador_mis_cajas(usuario):
    mostrar_banner_entorno()
    st.subheader("📋 Mis Cajas Registradas")
    
    sede_actual = usuario.get('sede_asignada', 'Casa Central')
    
    # Obtener cajas de la sede (asegurando traer 'pendiente de entrega')
    cajas = obtener_cajas_por_sede(sede_actual, entorno=st.session_state['entorno'])
    
    if not cajas:
        st.info("ℹ️ No hay cajas registradas para esta sede.")
        return

    # Convertir a DataFrame para procesar con st.data_editor
    df = pd.DataFrame(cajas)
    
    # Filtrar únicamente las cajas disponibles para solicitar retiro
    if 'estado' in df.columns:
        cajas_disponibles = df[df['estado'] == 'pendiente de entrega'].copy()
    else:
        cajas_disponibles = pd.DataFrame()
    
    if cajas_disponibles.empty:
        st.warning("⚠️ No tenés cajas pendientes de entrega para solicitar retiro.")
        st.dataframe(df, width="stretch")  # Muestra el historial general de la sede
        return

    # Insertar la columna booleana para las casillas de selección
    cajas_disponibles.insert(0, "Seleccionar", False)

    st.write("📌 **Tildá las cajas que querés incluir en la orden de retiro:**")

    # Tabla interactiva con checkboxes
    df_editado = st.data_editor(
        cajas_disponibles,
        column_config={
            "Seleccionar": st.column_config.CheckboxColumn(
                "Pedir Retiro",
                help="Marcar para incluir en la orden de retiro",
                default=False,
            ),
            "nro_caja": "N° Caja",
            "codigo_barra": "Código Etiquetas",
            "contenido": "Detalle Contenido",
            "estado": "Estado Actual"
        },
        disabled=[col for col in cajas_disponibles.columns if col != "Seleccionar"],
        hide_index=True,
        width="stretch"
    )

    # Filtrar únicamente las filas tildadas por el usuario
    cajas_seleccionadas = df_editado[df_editado["Seleccionar"] == True]

    st.markdown("---")

    # Si hay al menos una caja seleccionada, habilitar acciones
    if not cajas_seleccionadas.empty:
        cant = len(cajas_seleccionadas)
        st.success(f"📦 Has seleccionado **{cant}** caja(s) para retirar.")

        # Generar el binario del remito PDF
        pdf_bytes = generar_pdf_remito(sede_actual, usuario['username'], cajas_seleccionadas)

        col_acc1, col_acc2 = st.columns(2)

        with col_acc1:
            st.download_button(
                label="📄 Descargar Remito PDF",
                data=pdf_bytes,
                file_name=f"Remito_Retiro_{sede_actual.replace(' ', '_')}.pdf",
                mime="application/pdf",
                width="stretch"
            )

        with col_acc2:
            if st.button(f"🚚 Confirmar y Enviar Pedido ({cant} Cajas)", type="primary", key="btn_pedido_masivo", width="stretch"):
                lista_nros = cajas_seleccionadas['nro_caja'].tolist()
                
                # 1. Actualizar estados en la Base de Datos
                exito = solicitar_retiro_masivo_cajas(lista_nros, usuario['username'], entorno=st.session_state['entorno'])
                
                if exito:
                    resumen_cajas = ", ".join([str(n) for n in lista_nros])
                    
                    # Extracción de etiquetas para el correo
                    if 'codigo_barra' in cajas_seleccionadas.columns:
                        etiquetas_list = cajas_seleccionadas['codigo_barra'].dropna().astype(str).tolist()
                        detalle_etiquetas = ", ".join(etiquetas_list)
                    else:
                        detalle_etiquetas = "MÚLTIPLE"

                    # 2. Enviar correo de notificación
                    mail_enviado = enviar_notificacion_email(
                        nro_caja=f"SOLICITUD MASIVA ({cant} Cajas)",
                        sede=sede_actual,
                        solicitante=usuario['username'],
                        periodo="N/A",
                        contenido=f"Solicitud de retiro para las cajas N°: {resumen_cajas}",
                        codigo_barra=detalle_etiquetas
                    )
                    
                    # 3. Guardar trazabilidad en el Log de Envíos
                    estado_log = "Enviado con éxito" if mail_enviado else "Error en servidor de correo"
                    registrar_log_envio(
                        usuario=usuario['username'],
                        sede=sede_actual,
                        lista_cajas=lista_nros,
                        estado_email=estado_log,
                        entorno=st.session_state['entorno']
                    )
                    
                    st.toast(f"✅ Pedido de retiro generado y mail enviado ({cant} cajas).", icon="🚚")
                    st.rerun()
                else:
                    st.error("❌ Ocurrió un error al actualizar el estado en la base de datos.")

def vista_admin_dashboard():
    mostrar_banner_entorno()
    st.title("📊 Dashboard General")
    stats = obtener_estadisticas(entorno=st.session_state['entorno'])
    mostrar_kpis(stats)
    if stats['por_sede']:
        st.plotly_chart(px.bar(pd.DataFrame(stats['por_sede']), x='sede_dpto', y='cnt', color='sede_dpto', title="Cajas por Sede", color_discrete_sequence=['#1E3E6B', '#71BAB4', '#d99a38', '#5c4e8c']), use_container_width=True)

def vista_admin_auditoria():
    mostrar_banner_entorno()
    st.title("🔍 Auditoría Master")
    df = obtener_cajas_como_dataframe(entorno=st.session_state['entorno'])
    if not df.empty:
        res = auditar_con_datos_reales(df)
        st.metric("Alertas Detectadas", res['total_alertas'])
        if res['total_alertas'] > 0:
            st.dataframe(res['df_alertas'], use_container_width=True)
        else:
            st.success("✅ Todos los registros son válidos.")

def vista_admin_gestion():
    mostrar_banner_entorno()
    st.title("📋 Gestión de Cajas")
    cajas = obtener_cajas(entorno=st.session_state['entorno'])
    if cajas:
        df = pd.DataFrame(cajas)
        st.dataframe(df[['nro_caja', 'codigo_barra', 'sede_dpto', 'solicitante', 'contenido', 'estado']], use_container_width=True)

def vista_admin_log():
    mostrar_banner_entorno()
    st.title("📜 Log de Actividad")
    logs = obtener_log(entorno=st.session_state['entorno'])
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)

# ==============================================================================
# ENRUTAMIENTO PRINCIPAL
# ==============================================================================
if 'logged_in' not in st.session_state or not st.session_state.get('logged_in'):
    mostrar_login()
else:
    usuario = st.session_state['usuario']
    modulo = mostrar_sidebar(usuario)
    if usuario['rol'] in ['admin', 'admin_sede_central']:
        if modulo == "📊 Dashboard General": vista_admin_dashboard()
        elif modulo == "✅ Verificación y Precintos": vista_admin_verificacion()
        elif modulo == "🚚 Pedidos de Cajas a Sedes": vista_admin_pedidos_cajas()
        elif modulo == "🏷️ Stock de Insumos (Etiquetas y Precintos)": vista_admin_codigos_proveedor()
        elif modulo == "📋 Gestión de Cajas": vista_admin_gestion()
        elif modulo == "➕ Cargar Caja": formulario_carga(usuario)
        elif modulo == "🔍 Auditoría Master": vista_admin_auditoria()
        elif modulo == "📜 Log de Actividad": vista_admin_log()
    else:
        if modulo == "📋 Mis Cajas": vista_operador_mis_cajas(usuario)
        elif modulo == "➕ Cargar Contenido a Caja Enviada": formulario_carga(usuario, sede_fija=usuario['sede_asignada'])
        elif modulo == "📦 Solicitar Cajas a Sede": vista_operador_solicitar_cajas(usuario)