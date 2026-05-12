import streamlit as st
import urllib.parse
import pandas as pd
from datetime import datetime, time, timedelta
import uuid
import os
import mysql.connector
import base64
import requests
import time
import io
output = io.BytesIO()

# --- CONFIGURACIÓN DE IDENTIDAD ---
NUMERO_NEGOCIO = "50558222234" 
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
    # VISTA OPERATIVA PROTEGIDA
    # =========================================================
    st.title("🔐 Panel de Control AsCloS")

    # 1. Inicializar el estado de autenticación si no existe
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    # 2. Lógica de Login
    if not st.session_state.autenticado:
        password_input = st.text_input("Ingrese la clave de administrador:", type="password")
        
        if password_input == CLAVE_ADMIN:
            st.session_state.autenticado = True
            st.success("Acceso concedido.")
            st.rerun() 
        elif password_input != "":
            st.error("Clave incorrecta.")
    
    # 3. Si YA está autenticado, mostramos las pestañas
    else:
        # Botón en la barra lateral para salir
        if st.sidebar.button("🔒 Cerrar Sesión Admin"):
            st.session_state.autenticado = False
            st.rerun()

        tab1, tab2, tab3 = st.tabs(["📋 Historial de Pedidos", "💰 Gestionar Precios", "📜 Historial"])
        
        with tab1:
            st.subheader("🛎️ Recepción de Pedidos Nuevos")
            
            try:
                # Abrimos una única conexión para todo el Tab
                conn = conectar_db()
                
                # --- PARTE 1: RECEPCIÓN ---
                query_pendientes = "SELECT * FROM pedidos WHERE estado = 'Pendiente' ORDER BY fecha DESC"
                df_pendientes = pd.read_sql(query_pendientes, conn)
                
                if not df_pendientes.empty:
                    for i, row in df_pendientes.iterrows():
                        with st.container(border=True):
                            col_info, col_acc = st.columns([3, 1])
                            with col_info:
                                st.write(f"**Pedido:** {row['order_id']} | **Cliente:** {row['cliente']}")
                                st.write(f"**Detalle:** {row['detalle_items']}")
                                st.write(f"**Total:** C$ {row['total_pagar']}")
                            
                            with col_acc:
                                if st.button("✅ Confirmar Venta", key=f"conf_{row['order_id']}"):
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE pedidos SET estado = 'Confirmado' WHERE order_id = %s", (row['order_id'],))
                                    conn.commit()
                                    st.success("Venta registrada")
                                    st.rerun()
                                
                                if st.button("❌ Cancelar / Duplicado", key=f"can_{row['order_id']}"):
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE pedidos SET estado = 'Cancelado' WHERE order_id = %s", (row['order_id'],))
                                    conn.commit()
                                    st.warning("Pedido descartado")
                                    st.rerun()
                else:
                    st.info("No hay pedidos nuevos por el momento.")

                st.divider()

                # --- PARTE 2: RESUMEN DEL DÍA (ESTILO TABLA) ---
                st.subheader("📊 Resumen de Ventas Actual")
                
                query_hoy = "SELECT detalle_items, total_pagar FROM pedidos WHERE estado = 'Confirmado' AND cierre_caja = 0"
                df_hoy = pd.read_sql(query_hoy, conn)

                if not df_hoy.empty:
                    conteo_productos = {}
                    for items in df_hoy['detalle_items']:
                        for parte in items.split(','):
                            parte = parte.strip()
                            if "x " in parte:
                                try:
                                    cantidad = int(parte.split('x ')[0])
                                    nombre_prod = parte.split('x ')[1].split(' (')[0].strip()
                                    conteo_productos[nombre_prod] = conteo_productos.get(nombre_prod, 0) + cantidad
                                except: continue
                    
                    # Convertimos el conteo a un DataFrame para mostrar la tabla
                    df_resumen = pd.DataFrame([
                        {"Producto": prod, "Cantidad": cant} 
                        for prod, cant in conteo_productos.items()
                    ])
                    
                    # Mostramos la tabla profesional
                    st.table(df_resumen)

                    

                    # Total y Botones
                    col_total, col_descarga, col_cierre = st.columns([1.5, 1, 1])
                    
                    total_dinero = df_hoy['total_pagar'].sum()
                    col_total.metric("VENTA TOTAL", f"C$ {total_dinero}")

                    # --- GENERAR EXCEL CON XLSXWRITER ---
                    import io
                    output = io.BytesIO()
                    
                    # Ahora sí funcionará porque ya lo instalamos en el Paso 1
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_resumen.to_excel(writer, index=False, sheet_name='Corte_Caja')
                        
                        # Formatos opcionales
                        workbook  = writer.book
                        worksheet = writer.sheets['Corte_Caja']
                        format_total = workbook.add_format({'bold': True, 'font_color': 'red'})
                        
                        # Escribir el total al final
                        fila_total = len(df_resumen) + 2
                        worksheet.write(fila_total, 0, "TOTAL VENTA", format_total)
                        worksheet.write(fila_total, 1, total_dinero, format_total)

                    col_descarga.download_button(
                        label="📥 Descargar Excel Real",
                        data=output.getvalue(),
                        file_name=f"Corte_Asados_{time.strftime('%d_%m_%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                    if col_cierre.button("🏁 CIERRE DE DÍA", type="primary", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE pedidos SET cierre_caja = 1 WHERE cierre_caja = 0")
                        conn.commit()
                        st.success("✅ Cierre realizado correctamente.")
                        time.sleep(2)
                        st.rerun()
                else:
                    st.info("💡 Las ventas confirmadas aparecerán aquí en formato de tabla.")
            except Exception as e:
                st.error(f"Error en el resumen: {e}")        

        with tab2:
            if "upload_key" not in st.session_state:
                st.session_state.upload_key = 0

            st.subheader("🛠️ Editor Maestro de Menú")
            st.markdown("### 📸 Subir Foto Real del Producto")
            
            with st.expander("Abrir cargador de imágenes"):
                # 2. Widgets con key dinámica (16 espacios de sangría)
                foto_subida = st.file_uploader(
                    "Selecciona la foto desde tu celular", 
                    type=['jpg', 'jpeg', 'png'],
                    key=f"foto_{st.session_state.upload_key}"
                )
                nombre_archivo_github = st.text_input(
                    "Dale un nombre a la foto (ej: asado_nuevo.jpg)",
                    key=f"nombre_{st.session_state.upload_key}"
                )
                
                if st.button("🚀 Publicar Foto en la App"):
                    if foto_subida and nombre_archivo_github:
                        with st.spinner("Subiendo foto a la nube..."):
                            try:
                                token = st.secrets["GITHUB_TOKEN"]
                                repo = st.secrets["REPO_NAME"]
                                url = f"https://api.github.com/repos/{repo}/contents/{nombre_archivo_github}"
                                
                                contenido = base64.b64encode(foto_subida.read()).decode()
                                
                                datos = {
                                    "message": f"Nueva foto subida: {nombre_archivo_github}",
                                    "content": contenido,
                                    "branch": "main" 
                                }
                                
                                headers = {"Authorization": f"token {token}"}
                                response = requests.put(url, json=datos, headers=headers)
                                
                                if response.status_code in [200, 201]:
                                    st.success(f"✅ ¡Foto subida con éxito! Nombre: {nombre_archivo_github}")
                                    
                                    # 3. Incrementar key para limpiar widgets
                                    st.session_state.upload_key += 1
                                    
                                    import time
                                    time.sleep(2) 
                                    st.rerun()    
                                else:
                                    st.error(f"Error al subir: {response.json().get('message')}")
                            except Exception as e:
                                st.error(f"Error de conexión con GitHub: {e}")
                    else:
                        st.warning("Debes seleccionar una foto y ponerle un nombre.")

            st.divider()
            st.caption("Escribe el nombre del producto, el precio y el nombre exacto de la foto (ej: baho.jpeg).")
            
            try:
                conn = conectar_db()
                df_prods = pd.read_sql("SELECT * FROM productos", conn)
                
                editado = st.data_editor(
                    df_prods,
                    column_order=("nombre", "precio_base", "disponible", "imagen_url"),
                    num_rows="dynamic",
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
                    cursor.execute("DELETE FROM productos")
                    
                    for _, row in editado.iterrows():
                        if row['nombre']:
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
                    st.success("✅ ¡Menú actualizado!")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error de conexión: {e}")
        with tab3:
                st.subheader("📜 Historial de Ventas y Cierres")
                
                try:
                    conn = conectar_db()
                    
                    # Buscamos pedidos confirmados y cerrados
                    query_historial = """
                        SELECT fecha, cliente, detalle_items, total_pagar 
                        FROM pedidos 
                        WHERE estado = 'Confirmado' AND cierre_caja = 1 
                        ORDER BY fecha DESC
                    """
                    df_historial = pd.read_sql(query_historial, conn)
                    
                    if not df_historial.empty:
                        # (Aquí va tu código de filtros y st.dataframe que ya tienes)
                        filtro_fecha = st.date_input("📅 Selecciona una fecha para revisar", value=None)
                        
                        if filtro_fecha:
                            df_historial['fecha_solo'] = pd.to_datetime(df_historial['fecha']).dt.date
                            df_filtrado = df_historial[df_historial['fecha_solo'] == filtro_fecha]
                        else:
                            df_filtrado = df_historial
    
                        st.dataframe(df_filtrado[['fecha', 'cliente', 'detalle_items', 'total_pagar']], use_container_width=True)
                    
                    else:
                        # --- ESTE ES EL MENSAJE QUE BUSCAS ---
                        st.info("👋 ¡Hola! El historial está vacío por ahora.")
                        st.warning("⚠️ **Nota:** Los pedidos de hoy aparecerán aquí **solamente después** de que realices el 'Cierre de Día' en la pestaña de Recepción.")
                        
                        # Opcional: Un botón que lo mande de vuelta a la recepción
                        if st.button("Ir a Recepción para cerrar"):
                            st.switch_page("AsCloS.py") # O el nombre exacto de tu archivo principal
    
                    conn.close()

    except Exception as e:
                st.error(f"Error al cargar historial: {e}")
 




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
    # --- RESUMEN VISUAL DEL CARRITO (Antes de enviar) ---
    if subtotal > 0:
        st.markdown("<div class='category-header'>🛒 TU CARRITO ACTUAL</div>", unsafe_allow_html=True)
        
        # Contenedor con estilo de recibo
        st.markdown(f"""
            <div style="background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #eee; box-shadow: 0px 2px 5px rgba(0,0,0,0.05);">
                <p style="margin: 0; color: #888; font-size: 0.9rem;">Productos seleccionados:</p>
                <hr style="margin: 10px 0; border: 0; border-top: 1px dashed #ccc;">
                {"".join([f"<div style='display: flex; justify-content: space-between; margin-bottom: 5px;'><span>{item}</span></div>" for item in carrito])}
                <hr style="margin: 10px 0; border: 0; border-top: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 1.2rem; color: {COLOR_ACENTO};">
                    <span>SUBTOTAL:</span>
                    <span>C$ {subtotal}</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.write("") # Espacio visual

        # --- SECCIÓN DE ENVÍO Y FORMULARIO ---
        st.markdown("<div class='category-header'>🛵 DATOS DE ENTREGA</div>", unsafe_allow_html=True)
        
        zona = st.selectbox("¿Dónde te entregamos?", 
                           ["Santa Cruz (Gratis)", "Madroñal (Gratis)", "Balgüe (Gratis)", "Otras zonas (C$ 50)"])
        
        costo_delivery = 50 if "Otras zonas" in zona else 0
        total_final = subtotal + costo_delivery

        with st.form("comanda_final"):
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("👤 Nombre Completo")
            with col2:
                celular = st.text_input("📞 Número de Celular")
            
            direccion = st.text_area("🏠 Dirección Exacta / Puntos de Referencia")
            notas = st.text_input("📝 ¿Alguna nota especial? (Opcional)")
            
            st.markdown(f"### Total a pagar: C$ {total_final}")
            enviar = st.form_submit_button("🚀 GENERAR PEDIDO FINAL", use_container_width=True)

        if enviar:
            if nombre and celular and direccion:
                order_id = f"AGJ-{str(uuid.uuid4())[:4].upper()}"
                hash_v = (total_final + CLAVE_SECRETA) * 2
                
                # --- FORMATO ESTILO TICKET PROFESIONAL ---
                linea = "__________________________"
                detalle_texto = ""
                for item in carrito:
                    detalle_texto += f"🍱 {item}\n"

                msg_final = (
                    f"🔥 *PEDIDO OMETEPE: {order_id}*\n"
                    f"{linea}\n\n"
                    f"👤 *Cliente:* {nombre}\n"
                    f"📞 *Tel:* {celular}\n"
                    f"📍 *Zona:* {zona}\n"
                    f"🏠 *Dirección:* {direccion}\n\n"
                    f"🍱 *DETALLE:*\n{detalle_texto}\n"
                    f"💬 *NOTAS:* {notas if notas else 'Sin notas'}\n"
                    f"{linea}\n\n"
                    f"💰 *SUBTOTAL:* C$ {subtotal}\n"
                    f"🛵 *DELIVERY:* C$ {costo_delivery}\n"
                    f"💵 *TOTAL:* C$ {total_final}\n\n"
                    f"🔐 *FNUM COMANDA:* {hash_v}"
                )
                
                # --- GUARDAR EN BASE DE DATOS (INSERT REAL) ---
                try:
                    conn = conectar_db()
                    cursor = conn.cursor()
                    sql_insert = """INSERT INTO pedidos 
                                   (order_id, cliente, celular, zona, direccion_referencia, detalle_items, total_pagar) 
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)"""
                    # Convertimos el carrito a un solo texto para la DB
                    items_db = ", ".join(carrito)
                    cursor.execute(sql_insert, (order_id, nombre, celular, zona, direccion, items_db, total_final))
                    
                    conn.commit()
                    conn.close()
                    
                    # Guardamos en sesión para el botón de WhatsApp
                    st.session_state.msg_whatsapp = msg_final
                    st.session_state.pedido_listo = True
                    st.success(f"✅ Pedido {order_id} generado con éxito.")
                except Exception as e:
                    st.error(f"Error al guardar en base de datos: {e}")
            else:
                st.warning("⚠️ Por favor completa los datos de envío.")

        # --- BOTÓN DE WHATSAPP Y REINICIO ---
        if "pedido_listo" in st.session_state:
            st.markdown("---")
            st.info("¡Casi listo! Ahora envía el detalle a nuestro WhatsApp para confirmar.")
            
            link = f"https://api.whatsapp.com/send?phone={NUMERO_NEGOCIO}&text={urllib.parse.quote(st.session_state.msg_whatsapp)}"
            st.link_button("📲 ENVIAR PEDIDO POR WHATSAPP", link, use_container_width=True, type="primary")
            
            st.write("") 
            
            col_reset, _ = st.columns([1, 1])
            with col_reset:
                if st.button("🔄 HACER NUEVO PEDIDO", use_container_width=True):
                    st.toast("¡Gracias por tu pedido! En breve se te confirmará. 🍗🔥")
                    import time
                    time.sleep(2) 
                    st.session_state.clear()
                    st.rerun()
            
            st.caption("Nota: Al presionar 'Hacer nuevo pedido', se limpiará tu carrito actual.")


