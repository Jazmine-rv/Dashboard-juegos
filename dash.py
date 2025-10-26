
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import requests
from bs4 import BeautifulSoup
import time

# Configuración de la página
st.set_page_config(page_title="Genshin Impact Dashboard", layout="wide")

# -------------------- FUNCIÓN DE WEB SCRAPING --------------------
@st.cache_data(ttl=86400)  # Cache por 24 horas (puedes ajustar)
def scrape_genshin_characters():
    """
    Scrapea datos de personajes de Genshin Impact de la wiki
    Basado en el código original proporcionado
    """
    try:
        url = "https://genshin-impact.fandom.com/wiki/Characters/List"
        
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        
        # Buscamos la tabla principal
        tabla = soup.find("table", {"class": "article-table"})
        
        if not tabla:
            st.error("No se pudo encontrar la tabla de personajes")
            return pd.DataFrame()
            
        filas = tabla.find_all("tr")[1:]  # saltamos encabezado
        
        # Listas para guardar datos
        nombres, elementos, regiones, armas = [], [], [], []
        
        for fila in filas:
            celdas = fila.find_all("td")
            if len(celdas) >= 6:
                # Nombre
                nombre_tag = celdas[1].find("a")
                nombre = nombre_tag.text.strip() if nombre_tag else celdas[1].text.strip()
                
                # Elemento
                elemento_img = celdas[3].find("img")
                elemento = ""
                if elemento_img:
                    elemento = elemento_img.get("alt", "").replace("Icon", "").replace("Element ", "").strip()
                if not elemento:
                    elemento = celdas[3].text.strip()
                
                # Arma
                arma_img = celdas[4].find("img")
                arma = ""
                if arma_img:
                    arma = arma_img.get("alt", "").replace("Icon", "").replace("Weapon ", "").strip()
                if not arma:
                    arma = celdas[4].text.strip()
                
                # Región
                region_img = celdas[5].find("img")
                region = ""
                if region_img:
                    region = region_img.get("alt", "").replace("Icon", "").strip()
                if not region:
                    region = celdas[5].text.strip()
                
                nombres.append(nombre)
                elementos.append(elemento)
                armas.append(arma)
                regiones.append(region)
        
        # Creamos DataFrame limpio
        df = pd.DataFrame({
            "Nombre": nombres,
            "Elemento": elementos,
            "Arma": armas,
            "Región": regiones
        })
        
        return df
        
    except Exception as e:
        st.error(f"Error en el scraping: {e}")
        return pd.DataFrame()

# -------------------- CARGAR DATOS --------------------
@st.cache_data(ttl=86400)
def load_data():
    """
    Carga los datos via web scraping
    """
    with st.spinner("🔄 Cargando datos actualizados de Genshin Impact..."):
        df = scrape_genshin_characters()
        
        if df.empty:
            st.error("No se pudieron cargar los datos. Intenta recargar la página.")
            return pd.DataFrame()
        
        # Limpieza de datos (igual que tu código original)
        df['Nombre'] = df['Nombre'].astype(str)
        df['Elemento'] = df['Elemento'].astype(str)
        df['Arma'] = df['Arma'].astype(str)
        df['Región'] = df['Región'].astype(str).replace("None", "Desconocida")
        
        # Limpiar valores vacíos o inconsistentes
        df['Elemento'] = df['Elemento'].replace('', 'Desconocido')
        df['Arma'] = df['Arma'].replace('', 'Desconocido')
        df['Región'] = df['Región'].replace('', 'Desconocida')
        
        return df

# Cargar datos al inicio
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

# -------------------- Sidebar estilo OneLake --------------------
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
    # Limpiar cache para forzar nuevo scraping
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 12px;">
    <p>Genshin Impact Analytics v2.0</p>
    <p> Datos en tiempo real</p>
   
</div>
""", unsafe_allow_html=True)

# ================== TAB 0 → INICIO ==================
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
                    #imagen
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
        
        # Solo una imagen representativa para personajes
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
        - **Datos actualizados** - Información en tiempo real directamente de la wiki oficial
        
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
    
    **✨ Característica nueva:** Todos los datos se obtienen en tiempo real de la wiki oficial.
    """)

# ================== TAB 1 → Resumen Mejorado ==================
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

    # ... (el resto de tu código original para las otras pestañas continúa IGUAL)
    # Solo asegúrate de que todas las referencias a 'df' funcionen correctamente

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

# ================== TAB 2 → Elementos ==================
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

# ================== TAB 3 → Regiones ==================
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

# ================== TAB 4 → Combinaciones ==================
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

# ================== TAB 5 → Mapa ==================
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

    # Mostrar el mapa embedido (Streamlit no permite iframes directamente, pero podemos usar un link grande)
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

# ================== TAB 6 → Buscador ==================
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

# ================== FOOTER ==================
st.markdown("---")
st.markdown(
    "Datos de Genshin Impact | "
    "Fuente: [Genshin Impact Wiki](https://genshin-impact.fandom.com/wiki/Characters/List) | "
    "✅ Datos en tiempo real | "
    "¡Diviértete explorando Teyvat! 🎮"
)