import streamlit as st
import urllib.parse
import pandas as pd
from datetime import datetime
import uuid
import os

# --- CONFIGURACIÓN DE IDENTIDAD ---
NUMERO_NEGOCIO = "50581269278" 
COLOR_ACENTO = "#d32f2f"
CLAVE_SECRETA = 210825

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
dia_semana = datetime.now().weekday() 
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
        <p style='font-size: 0.8rem; margin: 0; color: #555;'>📍 Isla de Ometepe,El Madroñal</p>
    </div>
    <br>
""", unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align: center; color: {COLOR_ACENTO}; margin-top:-20px;'>Asados García Jiménez</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-style: italic;'>🔥 El auténtico sabor de la Isla de Ometepe</p>", unsafe_allow_html=True)

# --- VARIABLES DE CONTROL ---
carrito = []
subtotal = 0

# --- SECCIÓN DE SOPAS (SOLO DOMINGO Y LUNES) ---
if es_dia_de_sopa:
    st.markdown("<div class='category-header'>🍲 SOPAS ESPECIALES (Hoy disponible)</div>", unsafe_allow_html=True)
    col_img, col_info = st.columns([1, 2])
    
    with col_img:
        if os.path.exists("sopa.jpeg"):
            st.image("sopa.jpeg", use_container_width=True) 
            
    with col_info:
        st.markdown("**Disponible desde 10:00 am**")
        st.markdown("**Sopa de Res**")
        st.markdown("<span class='price-tag'>C$ 110</span>", unsafe_allow_html=True)
        
        # Usamos un nombre de variable único para la cantidad
        cant_sopa = st.number_input("Cantidad Sopa:", min_value=0, step=1, key="input_sopa_hoy")
        
        # IMPORTANTE: Solo sumar si la cantidad es mayor a cero
        if cant_sopa > 0:
            precio_sopa = 110
            total_sopa = precio_sopa * cant_sopa
            carrito.append(f"{cant_sopa}x Sopa de Res (C$ {precio_sopa} c/u)")
            subtotal += total_sopa # Aquí ya no te sumará nada si cant_sopa es 0
    st.divider()

# --- SECCIÓN DE ASADOS (CON PRECIOS VARIABLES) ---
st.markdown("<div class='category-header'>🥩 ASADOS (Elegir tamaño)</div>", unsafe_allow_html=True)

asados = [
    {"n": "Servicio de Res", "img": "res.jpeg"},
    {"n": "Servicio de Pollo", "img": "pollo.jpeg"},
    {"n": "Servicio de Cerdo", "img": "cerdo.jpeg"},
    {"n": "Servicio Mixto", "img": "mixto.jpeg"}
]

for a in asados:
    col_img, col_info = st.columns([1, 2])
    with col_img:
        if os.path.exists(a["img"]):
            st.image(a["img"], use_container_width=True)
    with col_info:
        st.markdown(f"**{a['n']}**")
        precio_elegido = st.radio(f"Tamaño para {a['n']}:", [80, 100,], horizontal=True, key=f"p_{a['n']}")
        cant = st.number_input("Cantidad:", min_value=0, step=1, key=f"c_{a['n']}")
        
        if cant > 0:
            item_total = precio_elegido * cant
            carrito.append(f"{cant}x {a['n']} (C$ {precio_elegido} c/u)")
            subtotal += item_total
    st.divider()

# --- SECCIÓN DE OTROS Y FRESCOS ---
st.markdown("<div class='category-header'>🌮 ANTOJITOS </div>", unsafe_allow_html=True)
otros = [
    {"n": "Tacos Crujientes", "p": 70, "img": "taco.jpeg"},
    {"n": "Arroz Especial", "p": 130, "img": "arroz.jpeg"},
    {"n": "combo papas y alitas", "p": 80, "img": "alitas.jpeg"},
    #{"n": "Melon", "p": 35, "img": "melon.jpeg"},
    #{"n": "Especial", "p": 30, "img": "especial.jpeg"}
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
            # --- CAMBIO AQUÍ: Detallamos el precio en el carrito ---
            item_total_otro = o['p'] * cant_o
            carrito.append(f"{cant_o}x {o['n']} (C$ {o['p']} c/u = C$ {item_total_otro})")
            subtotal += item_total_otro
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

    st.markdown(f"""
        <div style='background-color: #fff; padding: 15px; border-radius: 10px; border: 1px solid #ddd;'>
            <h4>Resumen de Cuenta:</h4>
            <p>Subtotal: C$ {subtotal}</p>
            <p>Delivery: C$ {costo_delivery}</p>
            <h3 style='color: {COLOR_ACENTO};'>TOTAL: C$ {total_final}</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form("comanda_final"):
        nombre = st.text_input("Nombre Completo")
        celular = st.text_input("Número Celular")
        direccion = st.text_area("Dirección / Referencia exacta")
        notas = st.text_area("Notas (Ej: Chile aparte, sin ensalada)")
        enviar = st.form_submit_button("🚀 GENERAR RESUMEN")

    if enviar:
        if nombre and celular and direccion:
            # 1. Calculamos la Firma Digital antes de armar el mensaje
            # Sumamos tu clave (la fecha de Cloe Sofia) y multiplicamos por 2
            hash_verificacion = (total_final + CLAVE_SECRETA) * 2
            
            # 2. Generamos el ID único del pedido
            order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"

            # 3. Guardamos todo en la sesión
            st.session_state.pedido_listo = True
            st.session_state.msg_whatsapp = (
                f"🔥 *PEDIDO OMETEPE: {order_id}*\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"👤 *Cliente:* {nombre}\n"
                f"📞 *Tel:* {celular}\n"
                f"📍 *Zona:* {zona}\n"
                f"🏠 *Dirección:* {direccion}\n\n"
                f"🍱 *DETALLE:*\n{chr(10).join(carrito)}\n\n"
                f"💬 *NOTAS:* {notas if notas else 'Ninguna'}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"💰 *SUBTOTAL:* C$ {subtotal}\n"
                f"🛵 *DELIVERY:* C$ {costo_delivery}\n"
                f"💵 *TOTAL:* C$ {total_final}\n"
                f"🔐 *FNUM COMANDA:* {hash_verificacion}" # <--- ¡AQUÍ QUEDA PROTEGIDO!
            )
        else:
            st.error("⚠️ Por favor, completa Nombre, Celular y Dirección.")

    # Mostramos el botón de WhatsApp FUERA del bloque 'if enviar' si ya está listo
    if "pedido_listo" in st.session_state:
        st.balloons()
        st.success("✅ ¡Resumen generado! CONTINUA CON EL BOTON DE ABAJO.")
        
        link = f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(st.session_state.msg_whatsapp)}"
        st.link_button("📲 CONFIRMAR Y ENVIAR POR WHATSAPP", link, use_container_width=True, type="primary")
        
        if st.button("🔄 Nuevo Pedido (Limpiar todo)"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()