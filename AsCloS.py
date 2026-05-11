import streamlit as st
import urllib.parse
import pandas as pd
from datetime import datetime, time, timedelta
import uuid
import os
import mysql.connector

# --- CONFIGURACIÓN DE IDENTIDAD ---
NUMERO_NEGOCIO = "50558222234" 
COLOR_ACENTO = "#d32f2f"

st.set_page_config(page_title="AsCloS - Sistema de Pedidos", page_icon="🔥", layout="centered")

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

# --- DETECTAR MODO (INVISIBLE) ---
query_params = st.query_params

if query_params.get("admin") == "true":
    # =========================================================
    # VISTA OPERATIVA (SOLO NESTOR)
    # =========================================================
    st.title("🛠️ Panel de Control AsCloS")
    
    tab1, tab2 = st.tabs(["📋 Historial de Pedidos", "📊 Gestión de Precios"])
    
    with tab1:
        st.subheader("Registros en Base de Datos")
        try:
            conn = conectar_db()
            query = "SELECT fecha, order_id, cliente, total_pagar, zona, estado_pedido FROM pedidos ORDER BY fecha DESC"
            df = pd.read_sql(query, conn)
            conn.close()
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Error al cargar pedidos: {e}")

    with tab2:
        st.subheader("Configuración de Productos")
        st.info("Aquí podrás añadir la tabla de 'productos' para cambiar precios dinámicamente.")
        if st.button("🔄 Actualizar App"):
            st.rerun()

else:
    # =========================================================
    # VISTA CLIENTE (LO QUE YA ESTÁ EN OPERACIÓN)
    # =========================================================
    
    # --- ESTILO CSS ---
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #f8f9fa; }}
        .category-header {{
            background-color: {COLOR_ACENTO}; color: white; padding: 10px;
            border-radius: 12px; margin: 20px 0; text-align: center; font-weight: bold;
        }}
        .price-tag {{ color: {COLOR_ACENTO}; font-weight: bold; font-size: 20px; }}
        </style>
        """, unsafe_allow_html=True)

    # --- LÓGICA DE TIEMPO ---
    ahora_nica = datetime.now() - timedelta(hours=6)
    dia_semana = ahora_nica.weekday() 
    es_dia_de_sopa = dia_semana in [0, 6] 

    # --- CABECERA ---
    col_l1, col_l2, col_l3 = st.columns([1, 3, 1])
    with col_l2:
        if os.path.exists("asado.jpeg"): st.image("asado.jpeg", use_container_width=True)
        
        hora_actual = ahora_nica.time()
        if time(15, 0) <= hora_actual <= time(20, 0):
            estado, color = "🟢 ¡ESTAMOS ABIERTOS!", "#28a745"
        else:
            estado, color = "🔴 CERRADO POR EL MOMENTO", "#d32f2f"

        st.markdown(f"""
            <div style='border: 2px solid {color}; padding: 15px; border-radius: 12px; background-color: #fffaf0; text-align: center;'>
                <h3 style='margin: 0; color: {color};'>{estado}</h3>
                <p style='margin: 5px 0;'><b>Horario:</b> 3:00 PM a 8:00 PM</p>
                <p style='margin: 0; font-weight: bold; color: #d32f2f;'>🛵 SOLO DOMICILIO</p>
            </div><br>
        """, unsafe_allow_html=True)

    # --- LÓGICA DE CARRITO (Simplificada para el ejemplo) ---
    carrito = []
    subtotal = 0

    st.markdown("<div class='category-header'>🥩 NUESTROS ASADOS</div>", unsafe_allow_html=True)
    
    # Ejemplo de un producto (puedes repetir este bloque para los demás)
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if os.path.exists("res.jpeg"): st.image("res.jpeg")
    with col_info:
        st.markdown("**Servicio de Res**")
        p_res = st.radio("Tamaño:", [80, 100, 120], horizontal=True, key="p_res")
        c_res = st.number_input("Cantidad:", min_value=0, step=1, key="c_res")
        if c_res > 0:
            carrito.append(f"{c_res}x Res (C$ {p_res} c/u)")
            subtotal += (p_res * c_res)

    # --- SECCIÓN FINAL Y ENVÍO ---
    if subtotal > 0:
        st.divider()
        zona = st.selectbox("Ubicación:", ["Santa Cruz", "Madroñal", "Balgüe"])
        costo_delivery = 0 # Lógica de costo según zona
        total_final = subtotal + costo_delivery

        with st.form("comanda"):
            nombre = st.text_input("Nombre")
            celular = st.text_input("Celular")
            direccion = st.text_area("Dirección")
            enviar = st.form_submit_button("🚀 ENVIAR PEDIDO")

        if enviar and nombre and celular and direccion:
            order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"
            try:
                conn = conectar_db()
                cursor = conn.cursor()
                sql = "INSERT INTO pedidos (order_id, cliente, celular, zona, direccion_referencia, detalle_items, subtotal, costo_delivery, total_pagar) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (order_id, nombre, celular, zona, direccion, ", ".join(carrito), subtotal, costo_delivery, total_final))
                conn.commit()
                conn.close()
                
                st.success(f"✅ Pedido {order_id} registrado")
                st.balloons()
                
                # Link de WhatsApp
                msg = f"🔥 *PEDIDO {order_id}*\nCliente: {nombre}\nDetalle: {', '.join(carrito)}\nTotal: C$ {total_final}"
                st.link_button("📲 Confirmar en WhatsApp", f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(msg)}")
                
                if st.button("🔄 Nuevo Pedido"):
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
