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
CLAVE_SECRETA = 210825 # Clave para Firma Digital
CLAVE_ADMIN = "Nestor2026" # <--- CONTRASEÑA PARA TU PANEL INVISIBLE

st.set_page_config(page_title="Asados García Jiménez - Ometepe", page_icon="🔥", layout="centered")

# --- CONEXIÓN A BASE DE DATOS (AsCloS) ---
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
    st.title("🔐 Panel de Control AsCloS")
    
    password_input = st.text_input("Ingrese la clave de administrador:", type="password")
    
    if password_input == CLAVE_ADMIN:
        st.success("Acceso concedido, Nestor.")
        tab1, tab2 = st.tabs(["📋 Historial de Pedidos", "💰 Gestión de Precios"])
        
        with tab1:
            st.subheader("Registros en Base de Datos")
            try:
                conn = conectar_db()
                query = "SELECT fecha, order_id, cliente, celular, total_pagar, zona, detalle_items FROM pedidos ORDER BY fecha DESC"
                df = pd.read_sql(query, conn)
                conn.close()
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"Error al cargar base de datos: {e}")

        with tab2:
            st.subheader("Control de Precios")
            st.info("Aquí podrás editar el catálogo cuando terminemos de migrar los productos a la tabla SQL.")
            if st.button("🔄 Refrescar Sistema"):
                st.rerun()
    elif password_input != "":
        st.error("Contraseña incorrecta.")

else:
    # =========================================================
    # VISTA CLIENTE (TU CÓDIGO ORIGINAL)
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
    es_dia_de_sopa = False # dia_semana in [0, 6]

    # --- CABECERA ---
    col_l1, col_l2, col_l3 = st.columns([1, 3, 1])
    with col_l2:
        if os.path.exists("asado.jpeg"):
            st.image("asado.jpeg", use_container_width=True)
        st.markdown(f"<h2 style='text-align: center; color: {COLOR_ACENTO};'>Asados García Jiménez</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-style: italic;'>🔥 El auténtico sabor de la Isla de Ometepe</p>", unsafe_allow_html=True)

    # --- VARIABLES DE CONTROL ---
    carrito = []
    subtotal = 0

    # --- SECCIÓN DE SOPAS ---
    if es_dia_de_sopa:
        st.markdown("<div class='category-header'>🍲 SOPAS ESPECIALES</div>", unsafe_allow_html=True)
        # (Tu lógica de sopas se mantiene igual aquí)

    # --- SECCIÓN DE ASADOS ---
    st.markdown("<div class='category-header'>🥩 ASADOS (Elegir tamaño)</div>", unsafe_allow_html=True)
    asados = [
        {"n": "Servicio de Pollo", "img": "pollo.jpeg"},
        {"n": "Servicio de Cerdo", "img": "cerdo.jpeg"},
    ]

    for a in asados:
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if os.path.exists(a["img"]): st.image(a["img"], use_container_width=True)
        with col_info:
            st.markdown(f"**{a['n']}**")
            precio_elegido = st.radio(f"Tamaño:", [80, 100], horizontal=True, key=f"p_{a['n']}")
            cant = st.number_input("Cantidad:", min_value=0, step=1, key=f"c_{a['n']}")
            if cant > 0:
                item_total = precio_elegido * cant
                carrito.append(f"{cant}x {a['n']} (C$ {precio_elegido} c/u)")
                subtotal += item_total
        st.divider()

    # --- SECCIÓN DE ANTOJITOS ---
    st.markdown("<div class='category-header'> Taco🌮 ANTOJITOS </div>", unsafe_allow_html=True)
    otros = [
        {"n": "Tacos Crujientes", "p": 70, "img": "taco.jpeg"},
        {"n": "Arroz Negro", "p": 80, "img": "arros.jpeg"},
        {"n": "Arroz Negro Papa/pollo", "p": 130, "img": "arroz.jpeg"},
        {"n": "combo papas y alitas", "p": 90, "img": "alitas.jpeg"},
        {"n": "Extra Gallopinto", "p": 30, "img": "gallo.jpeg"},
        {"n": "Extra De Papa", "p": 30, "img": "pap.jpeg"},
    ]

    for o in otros:
        col_img, col_info = st.columns([1, 2])
        with col_img:
            if os.path.exists(o["img"]): st.image(o["img"], use_container_width=True)
        with col_info:
            st.markdown(f"**{o['n']}**")
            st.markdown(f"<span class='price-tag'>C$ {o['p']}</span>", unsafe_allow_html=True)
            cant_o = st.number_input("Cantidad:", min_value=0, step=1, key=f"co_{o['n']}")
            if cant_o > 0:
                item_total_otro = o['p'] * cant_o
                carrito.append(f"{cant_o}x {o['n']} (C$ {o['p']} c/u = C$ {item_total_otro})")
                subtotal += item_total_otro
        st.divider()

    # --- GESTIÓN DE DELIVERY Y ENVÍO ---
    if subtotal > 0:
        st.markdown("<div class='category-header'>🛵 ENTREGA A DOMICILIO</div>", unsafe_allow_html=True)
        zona = st.selectbox("Seleccione su ubicación:", ["Santa Cruz (Gratis)", "Madroñal (Gratis)", "Balgüe (Gratis)", "Otras zonas (C$ 50)"])
        costo_delivery = 50 if "Otras zonas" in zona else 0
        total_final = subtotal + costo_delivery

        with st.form("comanda_final"):
            nombre = st.text_input("Nombre Completo")
            celular = st.text_input("Número Celular")
            direccion = st.text_area("Dirección / Referencia")
            notas = st.text_area("Notas adicionales")
            enviar = st.form_submit_button("🚀 GENERAR RESUMEN")

        if enviar and nombre and celular and direccion:
            # LÓGICA DE REGISTRO EN BASE DE DATOS
            order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"
            hash_verificacion = (total_final + CLAVE_SECRETA) * 2
            
            try:
                conn = conectar_db()
                cursor = conn.cursor()
                sql = "INSERT INTO pedidos (order_id, cliente, celular, zona, direccion_referencia, detalle_items, subtotal, costo_delivery, total_pagar, notas_cliente) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (order_id, nombre, celular, zona, direccion, ", ".join(carrito), subtotal, costo_delivery, total_final, notas))
                conn.commit()
                conn.close()
                st.session_state.pedido_listo = True
                st.session_state.msg_whatsapp = (
                    f"🔥 *PEDIDO OMETEPE: {order_id}*\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"🍱 *DETALLE:* {', '.join(carrito)}\n"
                    f"💵 *TOTAL:* C$ {total_final}\n"
                    f"🔐 *FNUM COMANDA:* {hash_verificacion}"
                )
            except Exception as e:
                st.error(f"Error al guardar: {e}")

        if "pedido_listo" in st.session_state:
            st.success("✅ Pedido registrado y resumen listo.")
            link = f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(st.session_state.msg_whatsapp)}"
            st.link_button("📲 ENVIAR POR WHATSAPP", link, use_container_width=True, type="primary")
            if st.button("🔄 Nuevo Pedido"):
                st.session_state.clear()
                st.rerun()
