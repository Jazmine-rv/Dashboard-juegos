import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import requests
import time
import re
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== 2. CONFIGURACIÓN DE LA PÁGINA ====================
st.set_page_config(page_title="Genshin Impact Dashboard", layout="wide")

# ==================== 3. FUNCIÓN DE WEB SCRAPING CON UNDETECTED-CHROMEDRIVER ====================

@st.cache_data(ttl=86400)
def scrape_genshin_characters():
    """
    Scrapea datos de personajes de Genshin Impact desde la wiki usando undetected-chromedriver
    """
    driver = None
    try:
        # Configurar opciones de Chrome
        options = uc.ChromeOptions()
        
        # === COMENTA ESTA LÍNEA PARA VER EL NAVEGADOR ===
        # options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-infobars")
        
        # User agent realista
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Crear el driver con undetected-chromedriver
        driver = uc.Chrome(options=options)
        
        # URL de la página
        url = "https://genshin-impact.fandom.com/es/wiki/Personajes"
        
        #st.info("🌐 Abriendo navegador con undetected-chromedriver...")
        driver.get(url)
        
        # Esperar a que la página cargue completamente
        #st.info("⏳ Esperando a que la página cargue... (10 segundos)")
        time.sleep(10)
        
        # ====== CERRAR POPUPS ======
        #st.info("🔍 Cerrando popups...")
        try:
            driver.execute_script("""
                // Cerrar popups de cookies
                document.querySelectorAll('.cookie-policy, .cookie-warning, .consent, .fc-close, [class*="cookie"], [class*="Cookie"]').forEach(function(el) {
                    el.click();
                });
                
                // Cerrar cualquier otro popup
                document.querySelectorAll('[class*="close"], [class*="Close"], [aria-label="Close"]').forEach(el => el.click());
                document.querySelectorAll('button:contains("Aceptar"), button:contains("Accept")').forEach(el => el.click());
            """)
        except:
            pass
        
        time.sleep(2)
        
        # ====== DESPLAZARSE A LA TABLA ======
        #st.info("📜 Buscando la tabla...")
        
        # Desplazarse gradualmente
        driver.execute_script("window.scrollTo(0, 300);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 600);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 900);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 1200);")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0, 1500);")
        time.sleep(1)
        
        # Buscar la tabla específicamente
        try:
            wait = WebDriverWait(driver, 15)
            tabla_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.wikitable")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tabla_element)
            #st.info("✅ Tabla encontrada")
            time.sleep(2)
        except Exception as e:
            st.warning(f"⚠️ No se encontró table.wikitable: {e}")
            # Buscar cualquier tabla
            tablas = driver.find_elements(By.TAG_NAME, "table")
            #st.info(f"🔍 Encontradas {len(tablas)} tablas")
            if tablas:
                # Usar la tabla más grande
                tabla_element = max(tablas, key=lambda t: len(t.find_elements(By.TAG_NAME, "tr")))
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tabla_element)
                st.info("✅ Usando la tabla más grande encontrada")
        
        # ====== OBTENER EL HTML ======
        #st.info("📄 Extrayendo datos...")
        html_completo = driver.page_source
        
        # Cerrar el navegador
        driver.quit()
        driver = None
        
        # ====== PARSEAR CON BEAUTIFULSOUP ======
        soup = BeautifulSoup(html_completo, 'html.parser')
        
        # Buscar TODAS las tablas
        tablas = soup.find_all("table")
        #st.info(f"🔍 Encontradas {len(tablas)} tablas en el HTML parseado")
        
        # Buscar la tabla correcta
        tabla_correcta = None
        for i, tabla in enumerate(tablas):
            primera_fila = tabla.find("tr")
            if not primera_fila:
                continue
            encabezados = primera_fila.find_all(["th", "td"])
            texto_encabezados = " ".join([th.text.strip().lower() for th in encabezados])
            if "personaje" in texto_encabezados and "rareza" in texto_encabezados:
                tabla_correcta = tabla
                #st.info(f"📋 Tabla {i+1} encontrada con encabezados correctos")
                break
        
        if not tabla_correcta:
            st.error("❌ No se encontró la tabla de personajes")
            return pd.DataFrame()
        
                # ====== EXTRAER DATOS - VERSIÓN MUY SIMPLE ======
        filas = tabla_correcta.find_all("tr")
        #st.info(f"📋 Total de filas: {len(filas)}")
        
        # Obtener los encabezados
        encabezados = filas[0].find_all(["th", "td"])
        texto_encabezados = [th.text.strip().lower() for th in encabezados]
        #st.info(f"📋 Encabezados: {texto_encabezados}")
        
        # Mapear índices de columnas
        col_idx = {}
        for i, h in enumerate(texto_encabezados):
            if "personaje" in h or "nombre" in h:
                col_idx['nombre'] = i
            elif "rareza" in h:
                col_idx['rareza'] = i
            elif "elemento" in h:
                col_idx['elemento'] = i
            elif "arma" in h:
                col_idx['arma'] = i
            elif "sexo" in h:
                col_idx['sexo'] = i
            elif "región de procedencia" in h:
                col_idx['region'] = i
        
        # Valores por defecto
        if 'nombre' not in col_idx:
            col_idx['nombre'] = 0
        if 'rareza' not in col_idx:
            col_idx['rareza'] = 1
        if 'elemento' not in col_idx:
            col_idx['elemento'] = 2
        if 'arma' not in col_idx:
            col_idx['arma'] = 3
        if 'sexo' not in col_idx:
            col_idx['sexo'] = 4
        if 'region' not in col_idx:
            col_idx['region'] = 5
        
        #st.info(f"📋 Índices de columnas: {col_idx}")
        
        # ====== EXTRACCIÓN PASO A PASO ======
        nombres, rarezas, elementos, armas, sexos, regiones = [], [], [], [], [], []
        
        # Verificar cuántas filas hay
        #st.info(f"📋 Filas a procesar: {len(filas) - 1} (excluyendo encabezado)")
        
        # Procesar CADA fila
        for idx_fila in range(1, len(filas)):  # Empezar desde 1 para saltar el encabezado
            fila = filas[idx_fila]
            celdas = fila.find_all(["td", "th"])
            
            # Si tiene menos de 4 celdas, no es una fila de datos
            if len(celdas) < 4:
                continue
            
            # ---- EXTRAER CADA CAMPO POR ÍNDICE ----
            # Nombre
            nombre = ""
            if col_idx['nombre'] < len(celdas):
                celda = celdas[col_idx['nombre']]
                # Intentar obtener enlace
                enlace = celda.find("a")
                if enlace:
                    nombre = enlace.get_text(strip=True)
                if not nombre:
                    nombre = celda.get_text(strip=True)
            
            # Si no hay nombre, saltar
            if not nombre:
                continue
            
            # Si el nombre es un encabezado, saltar
            if nombre.lower() in ["personaje", "rareza", "elemento", "arma", "sexo", "región", "región de procedencia"]:
                continue
            
            # Rareza
            rareza = "Desconocida"
            if col_idx['rareza'] < len(celdas):
                celda = celdas[col_idx['rareza']]
                # Buscar imágenes de estrellas
                estrellas = celda.find_all("img")
                if estrellas:
                    rareza = f"{len(estrellas)}★"
                else:
                    rareza = celda.get_text(strip=True)
            
            # Elemento
            elemento = "Desconocido"
            if col_idx['elemento'] < len(celdas):
                celda = celdas[col_idx['elemento']]
                # Buscar imagen
                img = celda.find("img")
                if img:
                    elemento = img.get("alt", "").strip()
                if not elemento or elemento == "Icon":
                    elemento = celda.get_text(strip=True)
                # Limpiar
                elemento = elemento.replace("Icon", "").replace("Element", "").strip()
            
            # Arma
            arma = "Desconocido"
            if col_idx['arma'] < len(celdas):
                celda = celdas[col_idx['arma']]
                img = celda.find("img")
                if img:
                    arma = img.get("alt", "").strip()
                if not arma or arma == "Icon":
                    arma = celda.get_text(strip=True)
                arma = arma.replace("Icon", "").replace("Weapon", "").strip()
            
            # Sexo
            sexo = "Desconocido"
            if col_idx['sexo'] < len(celdas):
                sexo = celdas[col_idx['sexo']].get_text(strip=True)
            
            # Región
            region = "Desconocida"
            if col_idx['region'] < len(celdas):
                region = celdas[col_idx['region']].get_text(strip=True)
                if region in ["—", "-", "Ninguna", ""]:
                    region = "Desconocida"
            
            # Agregar a las listas
            nombres.append(nombre)
            rarezas.append(rareza if rareza else "Desconocida")
            elementos.append(elemento if elemento else "Desconocido")
            armas.append(arma if arma else "Desconocido")
            sexos.append(sexo if sexo else "Desconocido")
            regiones.append(region if region else "Desconocida")
        
        # ====== DEPURACIÓN ======
        #st.info(f"🔍 Total nombres extraídos: {len(nombres)}")
        #if nombres:
            #st.info(f"🔍 Primeros 5 nombres: {nombres[:5]}")
            #st.info(f"🔍 Primeros 5 elementos: {elementos[:5]}")
            #st.info(f"🔍 Primeras 5 armas: {armas[:5]}")
        
        # ====== CREAR DATAFRAME ======
        if len(nombres) == 0:
            st.error("❌ No se extrajeron datos")
            return pd.DataFrame()
        
        df = pd.DataFrame({
            "Nombre": nombres,
            "Rareza": rarezas,
            "Elemento": elementos,
            "Arma": armas,
            "Sexo": sexos,
            "Región": regiones
        })
        
        #st.success(f"✅ Datos extraídos: {len(df)} personajes")
        
        
        # Limpiar datos
        df['Elemento'] = df['Elemento'].replace('', 'Desconocido')
        df['Arma'] = df['Arma'].replace('', 'Desconocido')
        df['Región'] = df['Región'].replace('', 'Desconocida')
        df['Sexo'] = df['Sexo'].replace('', 'Desconocido')
        df['Rareza'] = df['Rareza'].replace('', 'Desconocida')
        
        # Normalizar nombres de armas
        df['Arma'] = df['Arma'].replace({
            'Espada ligera': 'Espada',
            'Espada Claymore': 'Mandoble',
            'Mandoble': 'Mandoble',
            'Lanza': 'Lanza',
            'Arco': 'Arco',
            'Catalizador': 'Catalizador',
            'Claymore': 'Mandoble',
            'Sword': 'Espada',
            'Bow': 'Arco',
            'Catalyst': 'Catalizador',
            'Polearm': 'Lanza'
        })
        
        df = df.drop_duplicates(subset=['Nombre'])
        
        #st.success(f"✅ Datos obtenidos: {len(df)} personajes")
        return df
        
    except Exception as e:
        st.error(f"❌ Error en el scraping con undetected-chromedriver: {e}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

# ==================== 4. FUNCIÓN LOAD_DATA ====================

@st.cache_data(ttl=86400)
def load_data():
    """
    Carga los datos via web scraping con undetected-chromedriver
    """
    with st.spinner("🔄 Cargando datos actualizados de Genshin Impact..."):
        df = scrape_genshin_characters()
        
        if df.empty:
            st.error("No se pudieron cargar los datos. Intenta recargar la página.")
            return pd.DataFrame()
        
        # Limpieza de datos
        df['Nombre'] = df['Nombre'].astype(str)
        df['Elemento'] = df['Elemento'].astype(str)
        df['Arma'] = df['Arma'].astype(str)
        df['Región'] = df['Región'].astype(str)
        df['Sexo'] = df['Sexo'].astype(str)
        df['Rareza'] = df['Rareza'].astype(str)
        
        # Limpiar valores vacíos
        df['Elemento'] = df['Elemento'].replace('', 'Desconocido')
        df['Arma'] = df['Arma'].replace('', 'Desconocido')
        df['Región'] = df['Región'].replace('', 'Desconocida')
        df['Sexo'] = df['Sexo'].replace('', 'Desconocido')
        df['Rareza'] = df['Rareza'].replace('', 'Desconocida')
        
        return df

# ==================== 5. CARGAR DATOS ====================
df = load_data()

# Si no hay datos, mostrar error y detener
if df.empty:
    st.error("""
    ❌ No se pudieron cargar los datos. Esto puede deberse a:
    - Problemas de conexión a internet
    - Cambios en la estructura de la página web
    - Bloqueo temporal del sitio
    
    ⚠️ Por favor, recarga la página o intenta más tarde.
    """)
    st.stop()

# ==================== 6. SIDEBAR ESTILO ONELAKE ====================
st.sidebar.markdown("""
<div style="padding: 10px; background: #f8f9fa; border-radius: 8px; margin-bottom: 20px;">
    <h3 style="margin: 0; color: #1f2937; font-size: 18px;">🌍 Genshin Impact</h3>
    <p style="margin: 5px 0 0 0; color: #6b7280; font-size: 12px;">Tu centro de datos de Teyvat</p>
</div>
""", unsafe_allow_html=True)

# Sección de Navegación Principal
st.sidebar.markdown("### 📊 Navegación")

# Definir las pestañas principales
tabs = [
    {"icon": "🏠", "name": "Inicio", "description": "Página principal"},
    {"icon": "📈", "name": "Resumen", "description": "Estadísticas generales"},
    {"icon": "🔥", "name": "Elementos", "description": "Análisis por elemento"},
    {"icon": "🗺️", "name": "Regiones", "description": "Datos por región"},
    {"icon": "⚔️", "name": "Combinaciones", "description": "Elemento + Arma"},
    {"icon": "🌍", "name": "Mapa", "description": "Mapa interactivo"},
    {"icon": "🔍", "name": "Buscador", "description": "Búsqueda avanzada"}
]

# Inicializar el estado de la pestaña seleccionada
if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = "Inicio"

# Crear botones de navegación estilo OneLake
for tab in tabs:
    if st.sidebar.button(
        f"{tab['icon']} {tab['name']}",
        key=f"nav_{tab['name']}",
        use_container_width=True,
        help=tab['description']
    ):
        st.session_state.selected_tab = tab['name']

# Usar la pestaña seleccionada del estado de sesión
selected_tab = st.session_state.selected_tab

# Información del dataset en tiempo real
st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Información del Dataset")

st.sidebar.metric("Personajes", len(df))
st.sidebar.metric("Elementos", df['Elemento'].nunique())
st.sidebar.metric("Regiones", df['Región'].nunique())
st.sidebar.metric("Armas", df['Arma'].nunique())

# Botón para forzar actualización
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualizar Datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 12px;">
    <p>Genshin Impact Analytics v2.0</p>
    <p> Datos en tiempo real con undetected-chromedriver</p>
</div>
""", unsafe_allow_html=True)

# ==================== 7. TAB 0 → INICIO ====================
if selected_tab == "Inicio":
    st.title("🎮 Genshin Impact: Descubre el Mundo de Teyvat")
    st.markdown("---")

    # Estado para controlar el carrusel
    if 'carrusel_index' not in st.session_state:
        st.session_state.carrusel_index = 0

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        ## 🌟 ¿Qué es Genshin Impact?
        
        **Imagina un mundo mágico** donde los elementos controlan el destino, los héroes poseen poderes increíbles 
        y cada rincón esconde secretos por descubrir. ¡Bienvenido a Teyvat!
        
        ### 🎯 ¿Por qué millones de jugadores aman este juego?
        
        - **🌍 Mundo abierto inmenso**: Explora paisajes espectaculares desde montañas nevadas hasta desiertos ardientes""")
                    
        st.image("https://pbs.twimg.com/media/G15OmALbAAA5jJk?format=jpg&name=medium", 
                    caption="Naciones en Teyvat", 
                    use_container_width=True)

        st.markdown("""
        - **⚡ Sistema de elementos único**: Combina fuego, agua, electricidad y más para crear reacciones devastadoras""")
        try:
            st.image("https://theartofgaming.es/wp-content/uploads/2020/10/genshin-impact-reacciones-elementales.jpg", 
                    caption="Sistema de combate elemental - Combina poderes para efectos únicos", 
                    use_container_width=True)
        except:
            st.info("✨ Sistema de combate elemental - Combina poderes para efectos únicos")

        st.markdown("""
        - **🎭 Personajes memorables**: Más de 70 héroes únicos, cada uno con su propia historia y personalidad
        """)
        
        try:
            st.image("https://preview.redd.it/if-a-picture-can-help-people-traverse-through-time-v0-0kpiw2vftmrf1.jpeg?width=1080&crop=smart&auto=webp&s=de2e0bb1671503eb326b22ff53445ac072194afe", 
                    caption="Algunos de los héroes que encontrarás en tu aventura", 
                    use_container_width=True)
        except:
            st.info("👥 Algunos de los héroes que encontrarás en tu aventura")

        st.markdown("""
        - **💰 Gratuito para jugar**: Una experiencia AAA completamente gratuita""")
        
        st.image("https://oyster.ignimgs.com/mediawiki/apis.ign.com/genshin-impact/9/97/6.0_Header.jpg", 
                    caption="Nueva version 6.0", 
                    use_container_width=True)            

        st.markdown(f"""
        ## 📊 ¿Qué descubrirás en este dashboard?
        
        - **{df['Elemento'].nunique()} elementos mágicos** - Algunos son más comunes que otros entre los héroes
        - **{df['Región'].nunique()} regiones únicas** - Cada una tiene su propio estilo de personajes y habilidades
        - **{df['Arma'].nunique()} tipos de armas** - Existen combinaciones secretas entre elementos y armas
        - **Datos actualizados** - Información en tiempo real directamente de la wiki oficial con undetected-chromedriver
        
        ### 🚀 Tu aventura comienza aquí
        
        **Prepárate para:**
        - **Revelar patrones ocultos** en el diseño de personajes
        - **Armar equipos invencibles** basados en datos reales
        - **Explorar la diversidad** de las naciones de Teyvat
        - **Descubrir combinaciones únicas** que te darán ventaja en batalla
        
        *"Datos actualizados al momento"*
        """)

    with col2:
        st.image("teyvat_map.png", 
                 caption="El mundo mágico de Teyvat - Un universo por explorar", use_container_width=True)
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
        <h3 style="color: white; margin-top: 0;">🎁 Datos en Tiempo Real</h3>
        <p><strong>{len(df)}</strong> personajes únicos</p>
        <p><strong>{df['Elemento'].nunique()}</strong> elementos mágicos</p>
        <p><strong>{df['Región'].nunique()}</strong> regiones por explorar</p>
        <p><strong>{df['Arma'].nunique()}</strong> tipos de armas diferentes</p>
        <p style="font-size: 10px; margin: 5px 0 0 0;"></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        **💡 Perfecto para ti si:**
        - Eres nuevo en Genshin Impact
        - Quieres entender mejor el juego
        - Te gustan los datos y estadísticas
        - Buscas ventajas estratégicas
        """)

    # Tarjetas de resumen rápido
    st.markdown("---")
    st.subheader("🚀 Empieza tu Exploración")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Personajes", len(df))
        st.caption("Héroes únicos por descubrir")
        
    with col2:
        st.metric("🌈 Elementos", df['Elemento'].nunique())
        st.caption("Poderes mágicos diferentes")
        
    with col3:
        st.metric("🗺️ Regiones", df['Región'].nunique())
        st.caption("Naciones por explorar")
        
    with col4:
        st.metric("⚔️ Armas", df['Arma'].nunique())
        st.caption("Estilos de combate únicos")

    # Llamada a la acción
    st.markdown("---")
    st.success("""
    **🎯 ¿Listo para comenzar?** 
    Usa el menú lateral para explorar cada sección. Te recomendamos empezar por **📊 Resumen** 
    para obtener una visión general del universo de Genshin Impact.
    
    **✨ Característica nueva:** Todos los datos se obtienen en tiempo real de la wiki oficial usando undetected-chromedriver.
    """)

# ==================== 8. TAB 1 → RESUMEN ====================
elif selected_tab == "Resumen":
    st.header("📊 Resumen General")

    # KPIs en columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de personajes", len(df))
    with col2:
        elementos_unicos = [elem for elem in df['Elemento'].unique() if elem != "Desconocido"]
        st.metric("Total de elementos", len(elementos_unicos))
    with col3:
        regiones_unicas = [region for region in df['Región'].unique() if region != "Desconocido"]
        st.metric("Total de regiones", len(regiones_unicas))
    with col4:
        st.metric("Total de tipos de arma", df['Arma'].nunique())

    # Estadísticas adicionales
    st.subheader("📈 Estadísticas Detalladas")

    col1, col2 = st.columns(2)

    with col1:
        # Elemento más común (excluyendo "Desconocido")
        elementos_filtrados = df[df['Elemento'] != "Desconocido"]
        if len(elementos_filtrados) > 0:
            elemento_comun = elementos_filtrados['Elemento'].mode()[0]
            count_elemento = len(df[df['Elemento'] == elemento_comun])
            st.metric("Elemento más común", f"{elemento_comun} ({count_elemento})")
        else:
            st.metric("Elemento más común", "No disponible")

        # Región con más personajes (excluyendo "Desconocido")
        regiones_filtradas = df[df['Región'] != "Desconocido"]
        if len(regiones_filtradas) > 0:
            region_top = regiones_filtradas['Región'].value_counts().index[0]
            count_region = len(df[df['Región'] == region_top])
            st.metric("Región con más personajes", f"{region_top} ({count_region})")
        else:
            st.metric("Región con más personajes", "No disponible")

    with col2:
        # Arma más común (excluyendo "Desconocido")
        armas_filtradas = df[df['Arma'] != "Desconocido"]
        if len(armas_filtradas) > 0:
            arma_comun = armas_filtradas['Arma'].mode()[0]
            count_arma = len(df[df['Arma'] == arma_comun])
            st.metric("Arma más común", f"{arma_comun} ({count_arma})")
        else:
            st.metric("Arma más común", "No disponible")

        # Combinación más frecuente (excluyendo "Desconocido")
        combinaciones_filtradas = df[(df['Elemento'] != "Desconocido") & (df['Arma'] != "Desconocido")]
        if len(combinaciones_filtradas) > 0:
            combo = combinaciones_filtradas.groupby(['Elemento', 'Arma']).size().idxmax()
            count_combo = len(df[(df['Elemento'] == combo[0]) & (df['Arma'] == combo[1])])
            st.metric("Combinación más frecuente", f"{combo[0]} + {combo[1]} ({count_combo})")
        else:
            st.metric("Combinación más frecuente", "No disponible")

    # Vista previa de datos
    st.subheader("👥 Primeros 10 personajes del dataset")
    st.dataframe(df.head(10), use_container_width=True)

# ==================== 9. TAB 2 → ELEMENTOS ====================
elif selected_tab == "Elementos":
    st.header("🔥 Personajes por Elemento")

    col1, col2 = st.columns([1, 2])

    with col1:
        opciones_elemento = ["Todos"] + sorted([elem for elem in df['Elemento'].unique() if elem != "Desconocido"]) + ["Desconocido"]
        elemento_seleccionado = st.selectbox(
            "Filtrar por elemento", 
            opciones_elemento,
            key="elem_filter"
        )

    if elemento_seleccionado != "Todos":
        df_elemento = df[df['Elemento'] == elemento_seleccionado]
    else:
        df_elemento = df.copy()

    st.subheader(f"Personajes filtrados ({len(df_elemento)})")
    st.dataframe(df_elemento, use_container_width=True)

    # Gráficos de elementos
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Cantidad de personajes por elemento")
        df_count = df['Elemento'].value_counts().reset_index()
        df_count.columns = ['Elemento', 'Cantidad']

        fig_elem = px.bar(
            df_count,
            x='Elemento',
            y='Cantidad',
            text='Cantidad',
            title="Cantidad de personajes por elemento",
            color='Elemento',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        fig_elem.update_traces(textposition='outside')
        st.plotly_chart(fig_elem, use_container_width=True)

    with col2:
        st.subheader("🎯 Distribución de Armas por Elemento")
        fig_armas_elemento = px.histogram(
            df, 
            x='Elemento', 
            color='Arma',
            barmode='stack',
            title="Armas utilizadas por cada Elemento",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_armas_elemento, use_container_width=True)

# ==================== 10. TAB 3 → REGIONES ====================
elif selected_tab == "Regiones":
    st.header("🗺️ Personajes por Región")

    col1, col2 = st.columns([1, 2])

    with col1:
        opciones_region = ["Todas"] + sorted([region for region in df['Región'].unique() if region != "Desconocido"]) + ["Desconocido"]
        region_seleccionada = st.selectbox(
            "Filtrar por región", 
            opciones_region,
            key="region_filter"
        )

    if region_seleccionada != "Todas":
        df_region = df[df['Región'] == region_seleccionada]
    else:
        df_region = df.copy()

    st.subheader(f"Personajes filtrados ({len(df_region)})")
    st.dataframe(df_region, use_container_width=True)

    # Gráficos de regiones
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏔️ Cantidad de personajes por región")
        df_count_region = df['Región'].value_counts().reset_index()
        df_count_region.columns = ['Región', 'Cantidad']

        fig_region = px.bar(
            df_count_region,
            x='Región',
            y='Cantidad',
            text='Cantidad',
            title="Cantidad de personajes por región",
            color='Región'
        )
        fig_region.update_traces(textposition='outside')
        fig_region.update_xaxes(tickangle=45)
        st.plotly_chart(fig_region, use_container_width=True)

    with col2:
        st.subheader(f"🔥 Elementos en {region_seleccionada}")
        df_count_elemento_region = df_region['Elemento'].value_counts().reset_index()
        df_count_elemento_region.columns = ['Elemento', 'Cantidad']

        fig_elemento_region = px.pie(
            df_count_elemento_region,
            values='Cantidad',
            names='Elemento',
            title=f"Distribución de elementos en {region_seleccionada}",
            color='Elemento',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_elemento_region, use_container_width=True)

# ==================== 11. TAB 4 → COMBINACIONES ====================
elif selected_tab == "Combinaciones":
    st.header("⚔️ Combinaciones Elemento-Arma")

    # Heatmap de combinaciones
    st.subheader("🎨 Mapa de Calor - Combinaciones Elemento-Arma")
    cross_tab = pd.crosstab(df['Elemento'], df['Arma'])

    fig_heatmap = px.imshow(
        cross_tab,
        title="Frecuencia de Combinaciones Elemento-Arma",
        color_continuous_scale="purp",
        aspect="auto"
    )
    fig_heatmap.update_xaxes(title="Arma")
    fig_heatmap.update_yaxes(title="Elemento")
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # Gráficos de distribución
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏹 Distribución de Armas")
        fig_armas = px.pie(
            df, 
            names='Arma', 
            title='Distribución de Tipos de Armas',
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_armas, use_container_width=True)

    with col2:
        st.subheader("🌈 Distribución de Elementos")
        fig_elementos = px.pie(
            df, 
            names='Elemento', 
            title='Distribución de Elementos',
            color_discrete_sequence=px.colors.qualitative.Bold
        )
        st.plotly_chart(fig_elementos, use_container_width=True)

    # Tabla de combinaciones más comunes
    st.subheader("📋 Top 10 Combinaciones Más Comunes")
    combinaciones = df.groupby(['Elemento', 'Arma']).size().reset_index(name='Cantidad')
    combinaciones = combinaciones.sort_values('Cantidad', ascending=False).head(10)
    st.dataframe(combinaciones, use_container_width=True)

# ==================== 12. TAB 5 → MAPA ====================
elif selected_tab == "Mapa":
    st.header("🌍 Mapa Interactivo Oficial de Teyvat")
    # Información sobre el mapa oficial
    st.info("""
    **🗺️ Mapa Oficial de Hoyolab** - Esta es la herramienta interactiva oficial de miHoYo/Hoyoverse 
    para explorar el mundo de Genshin Impact. Puedes usarla para:
    - Ver la ubicación exacta de cada región
    - Encontrar materiales de ascensión
    - Descubrir secretos y tesoros
    - Planificar tus rutas de farmeo
    """)

    # Embed del mapa oficial de Hoyolab
    st.subheader("📍 Mapa Interactivo Oficial")

    # URL del mapa oficial de Hoyolab
    mapa_hoyolab_url = "https://act.hoyolab.com/ys/app/interactive-map/index.html?lang=es-es#/map/2?shown_types=&center=1886.00,-2221.00&zoom=-3.00"

    # Mostrar el mapa embedido
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"""
        <div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 10px; background-color: #f0f8f0;">
            <h4 style="color: #2E7D32; text-align: center;">🎮 Mapa Oficial de Hoyolab</h4>
            <p style="text-align: center;">Haz clic en el enlace para abrir el mapa interactivo oficial:</p>
            <div style="text-align: center; margin: 20px 0;">
                <a href="{mapa_hoyolab_url}" target="_blank" style="
                    display: inline-block; 
                    padding: 15px 30px; 
                    background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
                    color: white; 
                    text-decoration: none; 
                    border-radius: 25px; 
                    font-weight: bold; 
                    font-size: 18px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                    transition: all 0.3s ease;">
                    🗺️ Abrir Mapa Oficial de Hoyolab
                </a>
            </div>
            <p style="text-align: center; font-size: 12px; color: #666;">
                Se abrirá en una nueva pestaña - Requiere conexión a internet
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.image("teyvat_map.png", 
                 caption="El mundo de Teyvat", use_container_width=True)

    # Información adicional sobre las regiones
    st.subheader("🏞️ Información de las Regiones")

    coordenadas_teyvat = {
        'Mondstadt': {'color': "#b45817"},
        'Liyue': {'color': "#ffbb4d"},
        'Inazuma': {'color': "#cc5de8"},
        'Sumeru': {'color': "#45e321"},
        'Fontaine': {'color': "#29baef"},
        'Natlan': {'color': "#fe6767"},
        'Snezhnaya': {'color': "#f03e8e"},
        'Nod-Krai': {'color': "#1a1fa7"},
        'Desconocida': {'color': '#868e96'}
    }

    region_info = {
        'Mondstadt': "Ciudad de la Libertad y el viento",
        'Liyue': "Puerto próspero gobernado por los Adeptus",
        'Inazuma': "Nación del trueno y la eternidad",
        'Sumeru': "Tierra de la sabiduría y los arcontes de la sabiduría",
        'Fontaine': "Nación de la justicia y el agua",
        'Natlan': "Tierra del fuego y la guerra (por venir)",
        'Snezhnaya': "Nación del frío y los Fatui",
        'Nod-Krai': "Región misteriosa por explorar",
        'Desconocida': "Orígenes aún por descubrir"
    }

    # Mostrar información en tarjetas
    cols = st.columns(3)
    for idx, (region, info) in enumerate(region_info.items()):
        with cols[idx % 3]:
            count = len(df[df['Región'] == region])
            st.markdown(f"""
            <div style="border-left: 4px solid {coordenadas_teyvat.get(region, {}).get('color', '#666')}; 
                        padding: 10px; margin: 5px 0; background: white; border-radius: 5px;">
                <h5 style="margin: 0; color: {coordenadas_teyvat.get(region, {}).get('color', '#666')};">{region}</h5>
                <p style="margin: 5px 0; font-size: 12px;">{info}</p>
                <p style="margin: 0; font-weight: bold;">{count} personajes</p>
            </div>
            """, unsafe_allow_html=True)

# ==================== 13. TAB 6 → BUSCADOR ====================
elif selected_tab == "Buscador":
    st.header("🔍 Buscador de Personajes")
    st.write("Utiliza los filtros para encontrar personajes específicos:")

    col1, col2, col3 = st.columns(3)

    with col1:
        elemento_buscar = st.multiselect(
            "Elemento(s)", 
            options=sorted(df['Elemento'].unique()),
            default=None,
            key="search_elem"
        )

    with col2:
        arma_buscar = st.multiselect(
            "Tipo de Arma", 
            options=sorted(df['Arma'].unique()),
            default=None,
            key="search_arma"
        )

    with col3:
        region_buscar = st.multiselect(
            "Región(es)", 
            options=sorted(df['Región'].unique()),
            default=None,
            key="search_region"
        )

    # Aplicar filtros
    df_filtrado = df.copy()

    if elemento_buscar:
        df_filtrado = df_filtrado[df_filtrado['Elemento'].isin(elemento_buscar)]

    if arma_buscar:
        df_filtrado = df_filtrado[df_filtrado['Arma'].isin(arma_buscar)]

    if region_buscar:
        df_filtrado = df_filtrado[df_filtrado['Región'].isin(region_buscar)]

    # Mostrar resultados
    st.subheader(f"🎯 Resultados de la búsqueda: {len(df_filtrado)} personajes encontrados")

    if len(df_filtrado) > 0:
        # Estadísticas de los resultados
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Elementos en resultados", df_filtrado['Elemento'].nunique())
        with col2:
            st.metric("Armas en resultados", df_filtrado['Arma'].nunique())
        with col3:
            st.metric("Regiones en resultados", df_filtrado['Región'].nunique())

        # Mostrar datos
        st.dataframe(df_filtrado, use_container_width=True)

        # Mostrar distribución de los resultados
        col1, col2 = st.columns(2)
        with col1:
            if len(df_filtrado) > 1:
                fig_dist_elem = px.pie(
                    df_filtrado, 
                    names='Elemento', 
                    title='Distribución de Elementos en Resultados'
                )
                st.plotly_chart(fig_dist_elem, use_container_width=True)

        with col2:
            if len(df_filtrado) > 1:
                fig_dist_arma = px.pie(
                    df_filtrado, 
                    names='Arma', 
                    title='Distribución de Armas en Resultados'
                )
                st.plotly_chart(fig_dist_arma, use_container_width=True)
    else:
        st.warning("⚠️ No se encontraron personajes con los filtros seleccionados. Intenta con otros criterios.")

# ==================== 14. FOOTER ====================
st.markdown("---")
st.markdown(
    "Datos de Genshin Impact | "
    "Fuente: [Genshin Impact Wiki](https://genshin-impact.fandom.com/es/wiki/Personajes) | "
    "✅ Datos en tiempo real con undetected-chromedriver | "
    "¡Diviértete explorando Teyvat! 🎮"
)
