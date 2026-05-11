import streamlit as st
import urllib.parse
import pandas as pd
from datetime import datetime, time, timedelta
import uuid
import os
import mysql.connector

# --- CONFIGURACIÓN DE IDENTIDAD ---
NUMERO_NEGOCIO = "50588325774" 
COLOR_ACENTO = "#d32f2f"
CLAVE_SECRETA = 210825 # Para Firma Digital
CLAVE_ADMIN = "210825" # Contraseña para tu panel invisible

st.set_page_config(page_title="Asados García Jiménez - Ometepe", page_icon="🔥", layout="centered")

# --- CONEXIÓN A BASE DE DATOS ---
def conectar_db():
    return mysql.connector.connect(
        host="gateway01.us-east-1.prod.aws.tidbcloud.com",
        user="4Lu2TDuy2Wz3k9j.root",
        password="rDz6pwkzY2ZRyFv1",
        database="asclos_db",
        port=4000,
        ssl_ca="isrgrootx1.pem" 
    )

# --- FUNCIONES DE DATOS ---
def obtener_menu():
    try:
        conn = conectar_db()
        df = pd.read_sql("SELECT * FROM productos WHERE disponible = 1", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# --- DETECTAR MODO (INVISIBLE) ---
query_params = st.query_params

if query_params.get("admin") == "true":
    # =========================================================
    # VISTA OPERATIVA (SOLO NESTOR)
    # =========================================================
    st.title("🔐 Panel de Control AsCloS")
    password_input = st.text_input("Ingrese la clave de administrador:", type="password")
    
    if password_input == CLAVE_ADMIN:
        st.success("Acceso concedido.")
        tab1, tab2 = st.tabs(["📋 Historial de Pedidos", "💰 Gestionar Precios"])
        
        with tab1:
            try:
                conn = conectar_db()
                df_pedidos = pd.read_sql("SELECT fecha, order_id, cliente, total_pagar, detalle_items FROM pedidos ORDER BY fecha DESC", conn)
                conn.close()
                st.dataframe(df_pedidos, use_container_width=True)
            except Exception as e:
                st.error(f"Error al cargar pedidos: {e}")

        with tab2:
            st.subheader("🛠️ Editor Maestro de Menú")
            st.caption("Escribe el nombre del producto, el precio y el nombre exacto de la foto (ej: baho.jpeg).")
            
            try:
                conn = conectar_db()
                # Traemos la tabla actual de la base de datos
                df_prods = pd.read_sql("SELECT * FROM productos", conn)
                
                # CONFIGURACIÓN DEL EDITOR CORREGIDA (Sin el error de placeholder)
                editado = st.data_editor(
                    df_prods,
                    column_order=("nombre", "precio_base", "disponible", "imagen_url"),
                    num_rows="dynamic", # Permite usar el '+' para agregar filas
                    column_config={
                        "nombre": st.column_config.TextColumn("Nombre del Producto", required=True),
                        "precio_base": st.column_config.NumberColumn("Precio C$", min_value=0, format="C$ %d"),
                        "disponible": st.column_config.CheckboxColumn("¿Vender Hoy?", default=True),
                        "imagen_url": st.column_config.TextColumn(
                            "Foto (Archivo)", 
                            help="Escribe el nombre del archivo como está en GitHub, ej: baho.jpeg"
                        )
                    },
                    use_container_width=True,
                    key="editor_maestro_v3"
                )
                
                if st.button("💾 Guardar Cambios en el Menú"):
                    cursor = conn.cursor()
                    # 1. Limpiamos para evitar duplicados
                    cursor.execute("DELETE FROM productos")
                    
                    # 2. Insertamos lo que tienes en pantalla
                    for _, row in editado.iterrows():
                        if row['nombre']: # Solo si tiene nombre
                            # Si la celda de foto está vacía, ponemos asado.jpeg por defecto
                            foto = row['imagen_url'] if row['imagen_url'] else "asado.jpeg"
                            
                            sql = """INSERT INTO productos 
                                     (nombre, precio_base, disponible, imagen_url, categoria) 
                                     VALUES (%s, %s, %s, %s, %s)"""
                            cursor.execute(sql, (
                                row['nombre'], 
                                row['precio_base'], 
                                row['disponible'], 
                                foto,
                                "General"
                            ))
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ ¡Menú actualizado! Ya puedes ver los cambios.")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error de conexión: {e}")
    elif password_input != "":
        st.error("Clave incorrecta.")

else:
    # =========================================================
    # VISTA CLIENTE (DINÁMICA)
    # =========================================================
    st.markdown(f"<style>.category-header {{background-color: {COLOR_ACENTO}; color: white; padding: 10px; border-radius: 12px; text-align: center; font-weight: bold; margin: 20px 0;}} .price-tag {{color: {COLOR_ACENTO}; font-weight: bold; font-size: 20px;}}</style>", unsafe_allow_html=True)

    # Cabecera y Horario
    col_l1, col_l2, col_l3 = st.columns([1, 3, 1])
    with col_l2:
        if os.path.exists("asado.jpeg"): st.image("asado.jpeg", use_container_width=True)
        st.markdown(f"<h2 style='text-align: center; color: {COLOR_ACENTO};'>Asados García Jiménez</h2>", unsafe_allow_html=True)

    # Carga de Menú desde DB
    df_menu = obtener_menu()
    carrito = []
    subtotal = 0

    if not df_menu.empty:
        st.markdown("<div class='category-header'>🥩 NUESTRO MENÚ</div>", unsafe_allow_html=True)
        
        # Agrupamos los productos que tienen el mismo nombre
        nombres_unicos = df_menu['nombre'].unique()

        for nombre in nombres_unicos:
            # Filtramos todas las variantes de este producto (ej: el de 80 y el de 100)
            variantes = df_menu[df_menu['nombre'] == nombre]
            primera_variante = variantes.iloc[0] # Para sacar la foto y el ID base
            
            col_img, col_info = st.columns([1, 2])
            
            with col_img:
                if os.path.exists(primera_variante['imagen_url']):
                    st.image(primera_variante['imagen_url'], use_container_width=True)
            
            with col_info:
                st.markdown(f"**{nombre}**")
                
                # SI TIENE MÁS DE UN PRECIO (Doble selección)
                if len(variantes) > 1:
                    lista_precios = variantes['precio_base'].tolist()
                    precio_elegido = st.radio(
                        f"Tamaño para {nombre}:", 
                        options=lista_precios,
                        horizontal=True,
                        key=f"radio_{nombre}"
                    )
                else:
                    # SI TIENE UN SOLO PRECIO (Normal)
                    precio_elegido = primera_variante['precio_base']
                    st.markdown(f"<span class='price-tag'>C$ {precio_elegido}</span>", unsafe_allow_html=True)
                
                cant = st.number_input("Cantidad:", min_value=0, step=1, key=f"cant_{nombre}")
                
                if cant > 0:
                    item_total = precio_elegido * cant
                    carrito.append(f"{cant}x {nombre} (C$ {precio_elegido} c/u)")
                    subtotal += item_total
            st.divider()
    # Formulario de Envío
    if subtotal > 0:
        st.markdown("<div class='category-header'>🛵 ENTREGA A DOMICILIO</div>", unsafe_allow_html=True)
        zona = st.selectbox("Ubicación:", ["Santa Cruz (Gratis)", "Madroñal (Gratis)", "Balgüe (Gratis)", "Otras zonas (C$ 50)"])
        costo_delivery = 50 if "Otras zonas" in zona else 0
        total_final = subtotal + costo_delivery

        with st.form("comanda"):
            nombre = st.text_input("Nombre Completo")
            celular = st.text_input("Número Celular")
            direccion = st.text_area("Dirección / Referencia")
            enviar = st.form_submit_button("🚀 GENERAR RESUMEN")

        if enviar and nombre and celular and direccion:
            order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"
            hash_verificacion = (total_final + CLAVE_SECRETA) * 2
            try:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pedidos (order_id, cliente, celular, zona, direccion_referencia, detalle_items, subtotal, costo_delivery, total_pagar) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                             (order_id, nombre, celular, zona, direccion, ", ".join(carrito), subtotal, costo_delivery, total_final))
                conn.commit()
                conn.close()
                
                st.session_state.msg_whatsapp = f"🔥 *PEDIDO {order_id}*\n👤 *Cliente:* {nombre}\n🍱 *DETALLE:* {', '.join(carrito)}\n💵 *TOTAL:* C$ {total_final}\n🔐 *FNUM:* {hash_verificacion}"
                st.session_state.pedido_listo = True
            except Exception as e: st.error(f"Error: {e}")

        if "pedido_listo" in st.session_state:
            st.success("✅ Pedido registrado.")
            link = f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(st.session_state.msg_whatsapp)}"
            st.link_button("📲 ENVIAR POR WHATSAPP", link, use_container_width=True, type="primary")
            if st.button("🔄 Nuevo Pedido"):
                st.session_state.clear()
                st.rerun()
