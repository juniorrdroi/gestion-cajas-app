# -*- coding: utf-8 -*-
import io
import pandas as pd

SEDES_DPTOS_OK = [
    "Azcuénaga", "Facturación", "RRHH", "Ineba Endoscopia", "Finochietto",
    "Santa Fe", "Compras", "Tesorería", "Vof", "Fleming", "Juncal PB", "Itac", "Ineba 3P"
]

SEDES_SOLICITANTES = {
    "Azcuénaga": ["Soledad Massat", "Tania Lopez"],
    "Facturación": ["Verónica Scapin", "Pamela Cortez"],
    "RRHH": ["Candela García", "Miranda Caruso"],
    "Ineba Endoscopia": ["Celeste Rodriguez"],
    "Finochietto": ["Carla Maciel"],
    "Compras": ["Valeria Moreno"],
    "Tesorería": ["Mariana Pagos", "Diego Cobranzas"],
    "Santa Fe": ["Verónica Martinez", "Kalil Marpez"],
    "Vof": ["Cynthia Rosales", "Matías Conte"],
    "Fleming": ["Mariela Mashchio"],
    "Juncal PB": ["Vilma Rodriguez"],
    "Itac": ["Celeste Llanos"],
    "Ineba 3P": ["Florencia Meza"]
}

SOLICITANTES_OK = [sol for sub in SEDES_SOLICITANTES.values() for sol in sub]
ESTADOS_OK = ["pendiente de entrega", "completada", "caja no asignada"]

def auditar_con_datos_reales(origen):
    if isinstance(origen, pd.DataFrame):
        df = origen.copy()
    else:
        df = pd.read_excel(origen)

    df.columns = [str(c).strip().upper() for c in df.columns]

    mapeo = {
        'NRO_CAJA': 'NRO_CAJA', 'NUMERO DE CAJA': 'NRO_CAJA', 'CAJA': 'NRO_CAJA',
        'SEDE_DPTO': 'SEDE O DPTO', 'SEDE': 'SEDE O DPTO',
        'SOLICITANTE': 'SOLICITANTE', 'CONTENIDO': 'CONTENIDO',
        'PRECINTO_INICIO': 'PRECINTO INICIAL', 'PRECINTO_FIN': 'PRECINTO FINAL',
        'ESTADO': 'ESTADO', 'CODIGO_BARRA': 'CODIGO PROVEEDOR'
    }
    df = df.rename(columns={k: v for k, v in mapeo.items() if k in df.columns})

    total_registros = len(df)
    alertas = []
    err_solicitantes, err_sedes, err_estados, err_rangos, precintos_duplicados = [], [], [], [], []

    sedes_validas = [s.upper() for s in SEDES_DPTOS_OK]
    solics_validos = [s.upper() for s in SOLICITANTES_OK]
    estados_validos = [e.upper() for e in ESTADOS_OK]
    precintos_vistos = set()

    for idx, row in df.iterrows():
        caja = str(row.get('NRO_CAJA', idx + 1))
        sede = str(row.get('SEDE O DPTO', '')).strip()
        solic = str(row.get('SOLICITANTE', '')).strip()
        estado = str(row.get('ESTADO', '')).strip()
        p_ini = str(row.get('PRECINTO INICIAL', '')).strip()
        p_fin = str(row.get('PRECINTO FINAL', '')).strip()

        if sede.upper() not in sedes_validas:
            err_sedes.append(caja)
            alertas.append({'Caja': caja, 'Tipo': 'Sede No Válida', 'Detalle': f"'{sede}' no reconocida"})

        if solic.upper() not in solics_validos:
            err_solicitantes.append(caja)
            alertas.append({'Caja': caja, 'Tipo': 'Solicitante No Válido', 'Detalle': f"'{solic}' no registrado"})

        if estado.upper() not in estados_validos:
            err_estados.append(caja)
            alertas.append({'Caja': caja, 'Tipo': 'Estado No Válido', 'Detalle': f"'{estado}' no estándar"})

        if p_ini.isdigit() and p_fin.isdigit():
            if int(p_ini) > int(p_fin):
                err_rangos.append(caja)
                alertas.append({'Caja': caja, 'Tipo': 'Rango Precinto Inválido', 'Detalle': f"{p_ini} > {p_fin}"})
            if p_ini in precintos_vistos:
                precintos_duplicados.append(p_ini)
                alertas.append({'Caja': caja, 'Tipo': 'Precinto Duplicado', 'Detalle': f"Precinto {p_ini} repetido"})
            precintos_vistos.add(p_ini)

    df_alertas = pd.DataFrame(alertas) if alertas else pd.DataFrame(columns=['Caja', 'Tipo', 'Detalle'])
    cajas_acopio = len(df[df['ESTADO'].astype(str).str.lower() == 'completada'])
    reporte_sedes = df[df['ESTADO'].astype(str).str.lower() == 'completada'].groupby('SEDE O DPTO').size().reset_index(name='Cajas Listas para Acopio') if 'SEDE O DPTO' in df.columns else pd.DataFrame()

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cajas_General', index=False)
        df_alertas.to_excel(writer, sheet_name='Alertas', index=False)

    return {
        'total_registros': total_registros,
        'cajas_acopio': cajas_acopio,
        'total_alertas': len(alertas),
        'err_solicitantes': err_solicitantes,
        'err_sedes': err_sedes,
        'err_estados': err_estados,
        'err_rangos': err_rangos,
        'precintos_duplicados': precintos_duplicados,
        'df_alertas': df_alertas,
        'reporte_sedes': reporte_sedes,
        'df_base': df,
        'excel_buffer': excel_buffer
    }