import streamlit as st
import urllib.parse
import pandas as pd
from datetime import datetime
import uuid
import os
import datetime

# --- CONFIGURACIÓN DE IDENTIDAD ---
NUMERO_NEGOCIO = "50558222234" 
COLOR_ACENTO = "#d32f2f"

st.set_page_config(page_title="Asados García Jiménez - Ometepe", page_icon="🔥", layout="centered")

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

# --- LÓGICA DE DÍA PARA SOPAS ---
dia_semana = datetime.datetime.now().weekday() 
es_dia_de_sopa = dia_semana in [0, 6] # 0=Lunes, 6=Domingo

# --- CABECERA ---
col_l1, col_l2, col_l3 = st.columns([1, 3, 1])
with col_l2:
    if os.path.exists("asado.jpeg"):
        st.image("asado.jpeg", use_container_width=True)
    st.markdown("""
    <div style='text-align: center; background-color: #f0f2f6; padding: 10px; border-radius: 10px; border: 1px solid #d32f2f;'>
        <h4 style='margin: 0; color: #d32f2f;'>⏰ Horario de Atención</h4>
        <p style='margin: 0; color: #31333F;'><b>Lunes a Domingo:</b> 3:00 PM - 8:00 PM</p>
        <p style='font-size: 0.8rem; margin: 0; color: #555;'>📍 Isla de Ometepe</p>
    </div>
    <br>
""", unsafe_allow_html=True)
    ahora = datetime.datetime.now() - datetime.timedelta(hours=6)
    hora_actual = ahora.time()

    inicio_servicio = datetime.time(15, 0)  # 3:00 PM
    fin_servicio = datetime.time(20, 0)     # 8:00 PM

    if inicio_servicio <= hora_actual <= fin_servicio:
        estado_tienda = "🟢 ¡ESTAMOS ABIERTOS!"
        color_banner = "#28a745" # Verde éxito
    else:
        estado_tienda = "🔴 CERRADO POR EL MOMENTO"
        color_banner = "#d32f2f" # Rojo atención

    # --- BANNER INFORMATIVO (HORARIO + TIPO DE SERVICIO) ---
    st.markdown(f"""
        <div style='border: 2px solid {color_banner}; padding: 15px; border-radius: 12px; background-color: #fffaf0; text-align: center;'>
            <h3 style='margin: 0; color: {color_banner};'>{estado_tienda}</h3>
            <p style='margin: 5px 0; font-size: 1.1rem; color: #333;'><b>Horario:</b> 3:00 PM a 8:00 PM</p>
            <hr style='margin: 10px 0; border: 0; border-top: 1px solid #ccc;'>
            <p style='margin: 0; font-weight: bold; color: #d32f2f;'>🛵 SERVICIO EXCLUSIVO A DOMICILIO</p>
            <p style='margin: 5px 0 0 0; font-size: 0.9rem; color: #666;'><i>No contamos con atención en local físico. <br> Pedidos únicamente vía WebApp y WhatsApp.</i></p>
        </div>
        <br>
    """, unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: {COLOR_ACENTO}; margin-top:-20px;'>Asados García Jiménez</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>🔥 El auténtico sabor de la Isla de Ometepe</p>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>Contactanos 88325774-81269278</p>", unsafe_allow_html=True)

# --- VARIABLES DE CONTROL ---
carrito = []
subtotal = 0

# --- SECCIÓN DE SOPAS (SOLO DOMINGO Y LUNES) ---
if es_dia_de_sopa:
    st.markdown("<div class='category-header'>🍲 SOPAS ESPECIALES (Hoy disponible)</div>", unsafe_allow_html=True)
    col_img, col_info = st.columns([1, 2])
    with col_img:
        # Si tienes foto de sopa, cámbiala por sopa.jpeg
        st.image("sopa.jpeg", use_container_width=True) 
    with col_info:
        st.markdown("**Sopa de Res / Pollo**")
        st.markdown("<span class='price-tag'>C$ 180</span>", unsafe_allow_html=True)
        cant_s = st.number_input("Cantidad Sopa:", min_value=0, step=1, key="sopa_input")
        if cant_s > 0:
            carrito.append(f"{cant_s}x Sopa de Res/Pollo")
            subtotal += (180 * cant_s)
    st.divider()

# --- SECCIÓN DE ASADOS (CON PRECIOS VARIABLES) ---
st.markdown("<div class='category-header'>🥩 ASADOS (Elegir tamaño)</div>", unsafe_allow_html=True)

asados = [
    {"n": "Servicio de Res", "img": "res.jpeg"},
    {"n": "Servicio de Pollo", "img": "pollo.jpeg"},
    {"n": "Servicio de Cerdo", "img": "cerdo.jpeg"},
    {"n": "Servicio Mixto,Gallopinto", "img": "mixto.jpeg"}
]

for a in asados:
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if os.path.exists(a["img"]):
            st.image(a["img"], use_container_width=True)
    with col_info:
        st.markdown(f"**{a['n']}**")
        precio_elegido = st.radio(f"Tamaño para {a['n']}:", [80, 100, 120], horizontal=True, key=f"p_{a['n']}")
        cant = st.number_input("Cantidad:", min_value=0, step=1, key=f"c_{a['n']}")
        
        if cant > 0:
            item_total = precio_elegido * cant
            carrito.append(f"{cant}x {a['n']} (C$ {precio_elegido} c/u)")
            subtotal += item_total
    st.divider()

# --- SECCIÓN DE OTROS Y FRESCOS ---
st.markdown("<div class='category-header'>🌮 ANTOJITOS Y FRESCOS</div>", unsafe_allow_html=True)
otros = [
    {"n": "Tacos Crujientes", "p": 80, "img": "taco.jpeg"},
    {"n": "Arroz Negro", "p": 80, "img": "arros.jpeg"},
    {"n": "Arroz Especial", "p": 120, "img": "arroz.jpeg"},
    {"n": "combo papas y alitas", "p": 120, "img": "alitas.jpeg"},
    {"n": "Melon", "p": 35, "img": "melon.jpeg"},
    {"n": "Fresco del Dia", "p": 30, "img": "especial.jpeg"}
]

for o in otros:
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if os.path.exists(o["img"]):
            st.image(o["img"], use_container_width=True)
    with col_info:
        st.markdown(f"**{o['n']}**")
        st.markdown(f"<span class='price-tag'>C$ {o['p']}</span>", unsafe_allow_html=True)
        cant_o = st.number_input("Cantidad:", min_value=0, step=1, key=f"co_{o['n']}")
        if cant_o > 0:
            carrito.append(f"{cant_o}x {o['n']}")
            subtotal += (o['p'] * cant_o)
    st.divider()

# --- GESTIÓN DE DELIVERY ---
costo_delivery = 0
if subtotal > 0:
    st.markdown("<div class='category-header'>🛵 ENTREGA A DOMICILIO</div>", unsafe_allow_html=True)
    zona = st.selectbox("Seleccione su ubicación:", 
                        ["Santa Cruz (Gratis)", "Madroñal (Gratis)", "Balgüe (Gratis)", "Otras zonas de Ometepe (No disponible Aun)"])
    
    if "Otras zonas" in zona:
        costo_delivery = 50
    
    total_final = subtotal + costo_delivery

   # --- SUSTITUIR DESDE AQUÍ (Línea 154) ---
    st.markdown(f"""
            <div style='background-color: #fff; padding: 15px; border-radius: 10px; border: 1px solid #ddd;'>
                <h4 style='margin-top: 0;'>Resumen de Cuenta:</h4>
                <div style='background-color: #f9f9f9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <p style='margin: 0; font-weight: bold; color: #555;'>Productos seleccionados:</p>
                    <ul style='margin: 5px 0; padding-left: 20px;'>
                        {"".join([f"<li>{item}</li>" for item in carrito])}
                    </ul>
                </div>
                <p style='margin: 5px 0;'>Subtotal: C$ {subtotal}</p>
                <p style='margin: 5px 0;'>Delivery: C$ {costo_delivery}</p>
                <h3 style='color: {COLOR_ACENTO}; margin: 10px 0 0 0;'>TOTAL: C$ {total_final}</h3>
            </div>
        """, unsafe_allow_html=True)
        # --- HASTA AQUÍ (Línea 161) ---

    with st.form("comanda_final"):
        nombre = st.text_input("Nombre Completo")
        celular = st.text_input("Número Celular")
        direccion = st.text_area("Dirección / Referencia exacta")
        notas = st.text_area("Notas (Ej: Chile aparte, sin ensalada)")
        enviar = st.form_submit_button("🚀 ENVIAR PEDIDO POR WHATSAPP")

    if enviar:
        if nombre and celular and direccion:
            order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"
            msg = (
                f"🔥 *PEDIDO OMETEPE: {order_id}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Cliente:* {nombre}\n"
                f"📞 *Tel:* {celular}\n"
                f"📍 *Zona:* {zona}\n\n"
                f"🍱 *DETALLE:*\n{chr(10).join(carrito)}\n\n"
                f"💬 *NOTAS:* {notas if notas else 'Ninguna'}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 *SUBTOTAL:* C$ {subtotal}\n"
                f"🛵 *DELIVERY:* C$ {costo_delivery}\n"
                f"💵 *TOTAL:* C$ {total_final}"
            )
            
            st.balloons()
            st.success(f"¡Pedido {order_id} listo!")
            link = f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(msg)}"
            st.link_button("📲 Abrir WhatsApp y Confirmar", link)
