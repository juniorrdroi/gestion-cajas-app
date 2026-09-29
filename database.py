# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any

DB_PRODUCCION = "archivo_produccion.db"
DB_PRUEBAS = "archivo_pruebas.db"

def get_db_path(entorno: str = "produccion") -> str:
    return DB_PRUEBAS if entorno == "pruebas" else DB_PRODUCCION

def get_connection(entorno: str = "produccion"):
    db_file = get_db_path(entorno)
    conn = sqlite3.connect(db_file, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_pass(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def init_db(entorno: str = "produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
        username TEXT PRIMARY KEY,
        password_hash TEXT NOT NULL,
        rol TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        sede_asignada TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS cajas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nro_caja TEXT UNIQUE NOT NULL,
        codigo_barra TEXT,
        sede_dpto TEXT NOT NULL,
        solicitante TEXT NOT NULL,
        contenido TEXT NOT NULL,
        precinto_inicio TEXT,
        precinto_fin TEXT,
        estado TEXT NOT NULL DEFAULT 'pendiente de entrega',
        observaciones TEXT,
        cargado_por TEXT,
        fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    try:
        cur.execute("ALTER TABLE cajas ADD COLUMN fecha_desde TEXT")
    except Exception as e:
        pass

    try:
        cur.execute("ALTER TABLE cajas ADD COLUMN fecha_hasta TEXT")
    except Exception as e:
        pass  

    cur.execute('''
    CREATE TABLE IF NOT EXISTS pedidos_cajas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_solicitante TEXT NOT NULL,
        sede_dpto TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        motivo TEXT,
        estado TEXT DEFAULT 'pendiente',
        fecha_pedido DATETIME DEFAULT CURRENT_TIMESTAMP,
        fecha_atendido DATETIME
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS etiquetas_disponibles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nro_caja_proveedor TEXT,
        codigo_barra TEXT UNIQUE NOT NULL,
        precinto_1 TEXT,
        precinto_2 TEXT,
        estado TEXT DEFAULT 'disponible',
        fecha_carga DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Migración por si la tabla de etiquetas ya existía sin precintos
    try:
        cur.execute("ALTER TABLE etiquetas_disponibles ADD COLUMN precinto_1 TEXT")
        cur.execute("ALTER TABLE etiquetas_disponibles ADD COLUMN precinto_2 TEXT")
    except sqlite3.OperationalError:
        pass

    cur.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
        usuario TEXT NOT NULL,
        accion TEXT NOT NULL,
        detalle TEXT
    )
    ''')
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM usuarios")
    if cur.fetchone()[0] == 0:
        usuarios_default = [
            # Admins
            ("admin", hash_pass("admin2026"), "admin", "Administrador Master", "Casa Central"),
            ("admin_central", hash_pass("central2026"), "admin_sede_central", "Administrador Sede Central", "Casa Central"),
            
            # Operadores de todas las Sedes
            ("azcuenaga", hash_pass("sede2026"), "operador", "Operador Azcuénaga", "Azcuénaga"),
            ("facturacion", hash_pass("sede2026"), "operador", "Operador Facturación", "Facturación"),
            ("rrhh", hash_pass("sede2026"), "operador", "Operador RRHH", "RRHH"),
            ("ineba_end", hash_pass("sede2026"), "operador", "Operador Ineba Endoscopia", "Ineba Endoscopia"),
            ("finochietto", hash_pass("sede2026"), "operador", "Operador Finochietto", "Finochietto"),
            ("compras", hash_pass("sede2026"), "operador", "Operador Compras", "Compras"),
            ("tesoreria", hash_pass("sede2026"), "operador", "Operador Tesorería", "Tesorería"),
            ("santafe", hash_pass("sede2026"), "operador", "Operador Santa Fe", "Santa Fe"),
            ("vof", hash_pass("sede2026"), "operador", "Operador Vof", "Vof"),
            ("fleming", hash_pass("sede2026"), "operador", "Operador Fleming", "Fleming"),
            ("juncal_pb", hash_pass("sede2026"), "operador", "Operador Juncal PB", "Juncal PB"),
            ("itac", hash_pass("sede2026"), "operador", "Operador Itac", "Itac"),
            ("ineba_3p", hash_pass("sede2026"), "operador", "Operador Ineba 3P", "Ineba 3P")
        ]
        cur.executemany("INSERT INTO usuarios VALUES (?, ?, ?, ?, ?)", usuarios_default)
        conn.commit()

    asegurar_usuarios_todas_las_sedes(entorno)
        
    if entorno == "pruebas":
        sembrar_datos_de_prueba_si_vacio()

def asegurar_usuarios_todas_las_sedes(entorno='pruebas'):
    conn = get_connection(entorno)
    cur = conn.cursor()
    
    usuarios_necesarios = [
        ("azcuenaga", hash_pass("sede2026"), "operador", "Operador Azcuénaga", "Azcuénaga"),
        ("facturacion", hash_pass("sede2026"), "operador", "Operador Facturación", "Facturación"),
        ("rrhh", hash_pass("sede2026"), "operador", "Operador RRHH", "RRHH"),
        ("ineba_end", hash_pass("sede2026"), "operador", "Operador Ineba Endoscopia", "Ineba Endoscopia"),
        ("finochietto", hash_pass("sede2026"), "operador", "Operador Finochietto", "Finochietto"),
        ("compras", hash_pass("sede2026"), "operador", "Operador Compras", "Compras"),
        ("tesoreria", hash_pass("sede2026"), "operador", "Operador Tesorería", "Tesorería"),
        ("santafe", hash_pass("sede2026"), "operador", "Operador Santa Fe", "Santa Fe"),
        ("vof", hash_pass("sede2026"), "operador", "Operador Vof", "Vof"),
        ("fleming", hash_pass("sede2026"), "operador", "Operador Fleming", "Fleming"),
        ("juncal_pb", hash_pass("sede2026"), "operador", "Operador Juncal PB", "Juncal PB"),
        ("itac", hash_pass("sede2026"), "operador", "Operador Itac", "Itac"),
        ("ineba_3p", hash_pass("sede2026"), "operador", "Operador Ineba 3P", "Ineba 3P")
    ]
    
    for username, pass_hash, rol, nombre, sede in usuarios_necesarios:
        cur.execute("SELECT COUNT(*) FROM usuarios WHERE username = ?", (username,))
        if cur.fetchone()[0] == 0:
            cur.execute(
                "INSERT INTO usuarios (username, password_hash, rol, nombre_completo, sede_asignada) VALUES (?, ?, ?, ?, ?)",
                (username, pass_hash, rol, nombre, sede)
            )
            
    conn.commit()
    conn.close()

def migrar_desde_excel(ruta_excel, entorno="produccion"):
    import os
    import pandas as pd

    if not os.path.exists(ruta_excel):
        print(f"No se encontró el archivo Excel en la ruta: {ruta_excel}")
        return
    
    conn = get_connection(entorno)
    cur = conn.cursor()

    try:
        df = pd.read_excel(ruta_excel)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Actualizamos el mapeo para incluir las fechas y observaciones
        mapeo = {
            'NRO_CAJA': 'nro_caja', 'CAJA': 'nro_caja',
            'CODIGO_BARRA': 'codigo_barra', 'CODIGO': 'codigo_barra',
            'SEDE_DPTO': 'sede_dpto', 'SEDE': 'sede_dpto',
            'SOLICITANTE': 'solicitante', 
            'CONTENIDO': 'contenido',
            'CONTENIDODESDE': 'fecha_desde', 'FECHA DESDE': 'fecha_desde',
            'CONTENIDOHASTA': 'fecha_hasta', 'FECHA HASTA': 'fecha_hasta',
            'PRECINTO_INICIO': 'precinto_inicio', 'PRECINTO INICIAL': 'precinto_inicio',
            'PRECINTO_FIN': 'precinto_fin', 'PRECINTO FINAL': 'precinto_fin',
            'ESTADO': 'estado', 
            'OBSERVACIONES': 'observaciones',
            'FECHA ENTREGA EN AGÜERO': 'fecha_entrega_aguero' # Lo capturamos para sumarlo a observaciones
        }

        cajas_insertadas = 0
        for _, row in df.iterrows():
            datos = {v: str(row.get(k, '')).strip() for k, v in mapeo.items() if k in df.columns}
            
            for key in datos:
                if datos[key].lower() == 'nan':
                    datos[key] = ''

            # Si hay una fecha de entrega en Agüero, la sumamos a las observaciones
            obs = datos.get('observaciones', '')
            fecha_aguero = datos.get('fecha_entrega_aguero', '')
            if fecha_aguero:
                obs = f"Fecha entrega en Agüero: {fecha_aguero}. {obs}".strip()

            nro = datos.get('nro_caja', '')
            if nro:
                # Agregamos fecha_desde y fecha_hasta a la base de datos
                cur.execute('''
                    INSERT OR IGNORE INTO cajas (
                        nro_caja, codigo_barra, sede_dpto, solicitante, contenido, 
                        fecha_desde, fecha_hasta, precinto_inicio, precinto_fin, 
                        estado, observaciones, cargado_por
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'migracion_excel_real')
                ''', (
                    nro,
                    datos.get('codigo_barra', ''),
                    datos.get('sede_dpto', 'Casa Central'),
                    datos.get('solicitante', 'General'),
                    datos.get('contenido', 'Sin contenido especificado'),
                    datos.get('fecha_desde', ''),
                    datos.get('fecha_hasta', ''),
                    datos.get('precinto_inicio', ''),
                    datos.get('precinto_fin', ''),
                    datos.get('estado', 'pendiente de entrega'),
                    obs,
                ))
                cajas_insertadas += 1

        conn.commit()
        if 'registrar_actividad' in globals():
            registrar_actividad("sistema", "MIGRACION_REAL", f"Se migraron {cajas_insertadas} cajas reales desde Excel.", entorno=entorno)
        
        print(f"✅ Migración exitosa: Se insertaron {cajas_insertadas} cajas con sus fechas.")
        
    except Exception as e:
        print(f"❌ Error al migrar Excel real: {e}")
    finally:
        conn.close()

def sembrar_datos_de_prueba_si_vacio():
    conn = get_connection("pruebas")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM cajas")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    datos_prueba = [
        ("1001", "PROV-AZC-901", "Azcuénaga", "Dra. Gómez", "Historias Clínicas 2022 - Tomo 1", "100501", "100505", "completada", "Caja lista para auditoría", "azcuenaga"),
        ("1002", "PROV-AZC-902", "Azcuénaga", "Lic. Martínez", "Recetas Archivadas 2023", "100506", "100510", "pendiente de entrega", "Falta firma de recepción", "azcuenaga"),
        ("1003", "", "Azcuénaga", "Recepción Azcuénaga", "Fichas de Guardia Enero 2024", "100511", "100515", "pendiente de entrega", "Sin código de proveedor asignado aún", "azcuenaga")
    ]

    cur.executemany('''
        INSERT INTO cajas (nro_caja, codigo_barra, sede_dpto, solicitante, contenido, precinto_inicio, precinto_fin, estado, observaciones, cargado_por)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', datos_prueba)
    
    conn.commit()
    conn.close()

def reiniciar_base_de_pruebas():
    conn = get_connection("pruebas")
    cur = conn.cursor()
    cur.execute("DELETE FROM cajas")
    cur.execute("DELETE FROM pedidos_cajas")
    cur.execute("DELETE FROM etiquetas_disponibles")
    cur.execute("DELETE FROM logs")
    conn.commit()
    conn.close()
    sembrar_datos_de_prueba_si_vacio()

def autenticar_usuario(username, password, entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute(
        "SELECT username, rol, nombre_completo, sede_asignada FROM usuarios WHERE username = ? AND password_hash = ?",
        (username.strip().lower(), hash_pass(password.strip()))
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'username': row['username'],
            'rol': row['rol'],
            'nombre_completo': row['nombre_completo'],
            'sede_asignada': row['sede_asignada']
        }
    return None

# ➕ AGREGÁ ESTA NUEVA FUNCIÓN DEBAJO:
def obtener_usuarios_por_sede(sede, entorno='pruebas'):
    conn = get_connection(entorno)
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT nombre_completo FROM usuarios WHERE LOWER(TRIM(sede_asignada)) = LOWER(TRIM(?))", 
            (sede,)
        )
        rows = cur.fetchall()
        return [r['nombre_completo'] for r in rows] if rows else []
    except Exception as e:
        print(f"Error al obtener usuarios: {e}")
        return []
    finally:
        conn.close()

def obtener_cajas(sede=None, estado=None, busqueda=None, entorno="produccion"):
    conn = get_connection(entorno)
    query = "SELECT * FROM cajas WHERE 1=1"
    params = []

    if sede:
        query += " AND UPPER(sede_dpto) = UPPER(?)"
        params.append(sede)
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if busqueda:
        query += " AND (nro_caja LIKE ? OR codigo_barra LIKE ? OR contenido LIKE ? OR solicitante LIKE ? OR observaciones LIKE ?)"
        patron = f"%{busqueda}%"
        params.extend([patron, patron, patron, patron, patron])

    query += " ORDER BY fecha_carga DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df.to_dict(orient='records')

def obtener_cajas_pendientes_de_llenar(sede, entorno="produccion"):
    conn = get_connection(entorno)
    query = "SELECT * FROM cajas WHERE UPPER(sede_dpto) = UPPER(?) AND (contenido = '' OR contenido = 'Pendiente de carga de contenido') ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=[sede])
    conn.close()
    return df.to_dict(orient='records')

def obtener_cajas_como_dataframe(entorno="produccion"):
    conn = get_connection(entorno)
    df = pd.read_sql_query("SELECT * FROM cajas ORDER BY fecha_carga DESC", conn)
    conn.close()
    return df

def obtener_caja_por_identificador(identificador: str, entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM cajas WHERE UPPER(TRIM(nro_caja)) = UPPER(TRIM(?)) OR UPPER(TRIM(codigo_barra)) LIKE UPPER(TRIM(?))",
        (identificador, f"%{identificador}%")
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def insertar_caja(datos: dict, entorno="produccion") -> bool:
    conn = get_connection(entorno)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO cajas (nro_caja, codigo_barra, sede_dpto, solicitante, contenido, precinto_inicio, precinto_fin, estado, observaciones, cargado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos['nro_caja'],
            datos.get('codigo_barra', '').strip(),
            datos['sede_dpto'],
            datos['solicitante'],
            datos['contenido'],
            datos.get('precinto_inicio', ''),
            datos.get('precinto_fin', ''),
            datos.get('estado', 'pendiente de entrega'),
            datos.get('observaciones', ''),
            datos.get('cargado_por', 'sistema')
        ))
        conn.commit()
        registrar_actividad(datos.get('cargado_por', 'sistema'), 'CREAR_CAJA', f"Caja {datos['nro_caja']} creada ({entorno})", entorno=entorno)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def vincular_codigo_barra(nro_caja: str, codigo_barra: str, nro_caja_proveedor: str = "", usuario: str = "admin", entorno="produccion") -> bool:
    conn = get_connection(entorno)
    cur = conn.cursor()
    valor_final = f"{nro_caja_proveedor.strip()} | {codigo_barra.strip()}" if nro_caja_proveedor.strip() else codigo_barra.strip()
    cur.execute("UPDATE cajas SET codigo_barra = ? WHERE nro_caja = ?", (valor_final, nro_caja.strip()))
    filas = cur.rowcount
    conn.commit()
    conn.close()
    if filas > 0:
        registrar_actividad(usuario, 'VINCULAR_CODIGO', f"Caja N° {nro_caja} vinculada a etiqueta proveedor: {valor_final}", entorno=entorno)
        return True
    return False

def actualizar_caja(nro_caja: str, datos: dict, entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute('''
        UPDATE cajas
        SET codigo_barra = ?, sede_dpto = ?, solicitante = ?, contenido = ?, estado = ?, precinto_inicio = ?, precinto_fin = ?, observaciones = ?
        WHERE nro_caja = ?
    ''', (
        datos.get('codigo_barra', '').strip(),
        datos['sede_dpto'],
        datos['solicitante'],
        datos['contenido'],
        datos['estado'],
        datos.get('precinto_inicio', ''),
        datos.get('precinto_fin', ''),
        datos.get('observaciones', ''),
        nro_caja
    ))
    conn.commit()
    conn.close()
    registrar_actividad(datos.get('modificado_por', 'admin'), 'EDITAR_CAJA', f"Caja N° {nro_caja} actualizada", entorno=entorno)

def eliminar_caja(nro_caja: str, usuario: str = "admin", entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute("DELETE FROM cajas WHERE nro_caja = ?", (nro_caja,))
    conn.commit()
    conn.close()
    registrar_actividad(usuario, 'ELIMINAR_CAJA', f"Caja N° {nro_caja} eliminada", entorno=entorno)

def siguiente_nro_caja(entorno="produccion") -> str:
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute("SELECT nro_caja FROM cajas")
    rows = cur.fetchall()
    conn.close()
    max_num = 1000
    for r in rows:
        val = str(r[0]).strip()
        if val.isdigit():
            num = int(val)
            if num > max_num:
                max_num = num
    return str(max_num + 1)

def obtener_estadisticas(sede=None, entorno="produccion"):
    conn = get_connection(entorno)
    where = "WHERE UPPER(sede_dpto) = UPPER(?)" if sede else ""
    params = [sede] if sede else []

    total = conn.execute(f"SELECT COUNT(*) FROM cajas {where}", params).fetchone()[0]
    where_comp = f"{where} AND " if where else "WHERE "
    comp = conn.execute(f"SELECT COUNT(*) FROM cajas {where_comp} LOWER(estado) = 'completada'", params).fetchone()[0]
    pend = conn.execute(f"SELECT COUNT(*) FROM cajas {where_comp} LOWER(estado) LIKE '%pendiente%'", params).fetchone()[0]
    no_asig = conn.execute(f"SELECT COUNT(*) FROM cajas {where_comp} LOWER(estado) LIKE '%no asignada%'", params).fetchone()[0]

    cur = conn.cursor()
    cur.execute(f"SELECT sede_dpto, COUNT(*) as cnt FROM cajas {where} GROUP BY sede_dpto ORDER BY cnt DESC", params)
    por_sede = [{'sede_dpto': r[0], 'cnt': r[1]} for r in cur.fetchall()]

    cur.execute(f"SELECT solicitante, COUNT(*) as cnt FROM cajas {where} GROUP BY solicitante ORDER BY cnt DESC", params)
    por_solic = [{'solicitante': r[0], 'cnt': r[1]} for r in cur.fetchall()]

    conn.close()
    return {
        'total': total,
        'completadas': comp,
        'pendientes': pend,
        'no_asignadas': no_asig,
        'por_sede': por_sede,
        'por_solicitante': por_solic
    }

def crear_pedido_cajas(usuario: str, sede: str, cantidad: int, motivo: str = "", entorno: str = "produccion") -> bool:
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO pedidos_cajas (usuario_solicitante, sede_dpto, cantidad, motivo)
        VALUES (?, ?, ?, ?)
    ''', (usuario, sede, cantidad, motivo))
    conn.commit()
    conn.close()
    registrar_actividad(usuario, 'PEDIDO_CAJAS', f"Solicitó {cantidad} cajas para {sede}", entorno=entorno)
    return True

def obtener_pedidos_cajas(sede=None, entorno="produccion"):
    conn = get_connection(entorno)
    query = "SELECT * FROM pedidos_cajas WHERE 1=1"
    params = []
    if sede:
        query += " AND UPPER(sede_dpto) = UPPER(?)"
        params.append(sede)
    query += " ORDER BY fecha_pedido DESC"
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df.to_dict(orient='records')

def despachar_pedido_con_etiquetas(pedido_id: int, etiquetas_ids: list, admin_usr: str, entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM pedidos_cajas WHERE id = ?", (pedido_id,))
    pedido = cur.fetchone()
    if not pedido:
        conn.close()
        return False

    sede = pedido['sede_dpto']
    solicitante = pedido['usuario_solicitante']

    cur.execute("SELECT nro_caja FROM cajas")
    rows = cur.fetchall()
    max_num = 1000
    for r in rows:
        val = str(r[0]).strip()
        if val.isdigit():
            num = int(val)
            if num > max_num:
                max_num = num

    for et_id in etiquetas_ids:
        max_num += 1
        nro_interno = str(max_num)

        cur.execute("SELECT * FROM etiquetas_disponibles WHERE id = ?", (et_id,))
        etiqueta = cur.fetchone()
        if etiqueta:
            cod_final = f"{etiqueta['nro_caja_proveedor']} | {etiqueta['codigo_barra']}" if etiqueta['nro_caja_proveedor'] else etiqueta['codigo_barra']
            p1 = etiqueta['precinto_1'] if etiqueta['precinto_1'] else ''
            p2 = etiqueta['precinto_2'] if etiqueta['precinto_2'] else ''

            cur.execute('''
                INSERT INTO cajas (nro_caja, codigo_barra, sede_dpto, solicitante, contenido, precinto_inicio, precinto_fin, estado, cargado_por)
                VALUES (?, ?, ?, ?, 'Pendiente de carga de contenido', ?, ?, 'enviada a sede', ?)
            ''', (nro_interno, cod_final, sede, solicitante, p1, p2, admin_usr))

            cur.execute("UPDATE etiquetas_disponibles SET estado = 'asignada' WHERE id = ?", (et_id,))

    cur.execute("UPDATE pedidos_cajas SET estado = 'enviado', fecha_atendido = CURRENT_TIMESTAMP WHERE id = ?", (pedido_id,))
    conn.commit()
    conn.close()

    registrar_actividad(admin_usr, 'DESPACHO_PEDIDO', f"Despachó Pedido #{pedido_id} a {sede} con {len(etiquetas_ids)} kits (etiqueta+precintos) asociados", entorno=entorno)
    return True

def actualizar_estado_pedido(pedido_id: int, nuevo_estado: str, admin_usr: str, entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute('''
        UPDATE pedidos_cajas 
        SET estado = ?, fecha_atendido = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (nuevo_estado, pedido_id))
    conn.commit()
    conn.close()
    registrar_actividad(admin_usr, 'ATENDER_PEDIDO', f"Pedido #{pedido_id} marcado como {nuevo_estado}", entorno=entorno)

def registrar_etiqueta_proveedor(nro_prov: str, cod_barra: str, precinto_1: str = "", precinto_2: str = "", usuario: str = "admin", entorno="produccion") -> bool:
    conn = get_connection(entorno)
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO etiquetas_disponibles (nro_caja_proveedor, codigo_barra, precinto_1, precinto_2)
            VALUES (?, ?, ?, ?)
        ''', (nro_prov.strip(), cod_barra.strip(), precinto_1.strip(), precinto_2.strip()))
        conn.commit()
        registrar_actividad(usuario, 'ALTA_ETIQUETA', f"Kit Insumos {nro_prov} | {cod_barra} (Precintos: {precinto_1}/{precinto_2}) agregado al stock", entorno=entorno)
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def obtener_etiquetas_disponibles(entorno="produccion"):
    conn = get_connection(entorno)
    df = pd.read_sql_query("SELECT * FROM etiquetas_disponibles WHERE estado = 'disponible' ORDER BY id DESC", conn)
    conn.close()
    return df.to_dict(orient='records')

def registrar_actividad(usuario: str, accion: str, detalle: str = "", entorno="produccion"):
    conn = get_connection(entorno)
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (usuario, accion, detalle) VALUES (?, ?, ?)", (usuario, accion, detalle))
    conn.commit()
    conn.close()

def obtener_log(limit: int = 100, entorno="produccion"):
    conn = get_connection(entorno)
    df = pd.read_sql_query(f"SELECT fecha, usuario, accion, detalle FROM logs ORDER BY fecha DESC LIMIT {limit}", conn)
    conn.close()
    return df.to_dict(orient='records')

def migrar_y_crear_tablas_log(entorno='pruebas'):
    """Asegura la existencia de la columna modificado_por y la tabla de logs."""
    conn = get_connection(entorno)
    cursor = conn.cursor()
    
    # 1. Agregar columna modificado_por si no existe
    try:
        cursor.execute("ALTER TABLE cajas ADD COLUMN modificado_por TEXT")
        conn.commit()
    except Exception:
        pass  # La columna ya existe

    # 2. Crear tabla para el historial de envíos/logs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_envios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usuario TEXT,
            sede TEXT,
            cajas_solicitadas TEXT,
            cant_cajas INTEGER,
            estado_email TEXT
        )
    """)
    conn.commit()
    conn.close()

def registrar_log_envio(usuario, sede, lista_cajas, estado_email, entorno='pruebas'):
    """Inserta un registro en el historial de envíos/logs."""
    conn = get_connection(entorno)
    cursor = conn.cursor()
    try:
        cajas_str = ", ".join([str(n) for n in lista_cajas])
        cursor.execute("""
            INSERT INTO log_envios (usuario, sede, cajas_solicitadas, cant_cajas, estado_email)
            VALUES (?, ?, ?, ?, ?)
        """, (usuario, sede, cajas_str, len(lista_cajas), estado_email))
        conn.commit()
    except Exception as e:
        print(f"Error al guardar log de envío: {e}")
    finally:
        conn.close()

def solicitar_retiro_masivo_cajas(lista_nro_cajas, usuario_solicitante, entorno='pruebas'):
    """Actualiza el estado y el usuario modificador de una lista de cajas."""
    migrar_y_crear_tablas_log(entorno)  # Garantiza que las columnas/tablas existan
    
    conn = get_connection(entorno)
    cursor = conn.cursor()
    try:
        cant_cajas = len(lista_nro_cajas)
        placeholders = ','.join(['?'] * cant_cajas)
        
        sql_query = f"""
            UPDATE cajas 
            SET estado = 'solicitada para retiro',
                modificado_por = ?
            WHERE nro_caja IN ({placeholders})
        """
        
        parametros = [usuario_solicitante] + list(lista_nro_cajas)
        cursor.execute(sql_query, parametros)
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al solicitar retiro masivo: {e}")
        return False
    finally:
        conn.close()

def obtener_cajas_por_sede(sede, entorno="produccion"):
    """Retorna todas las cajas asociadas a una sede específica."""
    conn = get_connection(entorno)
    query = "SELECT * FROM cajas WHERE UPPER(sede_dpto) = UPPER(?) ORDER BY id DESC"
    df = pd.read_sql_query(query, conn, params=[sede])
    conn.close()
    return df.to_dict(orient='records')

def agregar_columna_modificado_por(entorno='pruebas'):
    """Agrega la columna modificado_por a la tabla cajas si no existe."""
    conn = get_connection(entorno)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE cajas ADD COLUMN modificado_por TEXT")
        conn.commit()
        print("✅ Columna 'modificado_por' agregada exitosamente.")
    except Exception as e:
        print(f"ℹ️ La columna ya existe o no se pudo agregar: {e}")
    finally:
        conn.close()

# Ejecutar la migración al importar el módulo
agregar_columna_modificado_por('pruebas')
agregar_columna_modificado_por('produccion')