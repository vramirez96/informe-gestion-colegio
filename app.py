import streamlit as st
import pandas as pd
import plotly.express as px
import db_utils
import os

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Dashboard Financiero - Colegio Gimnasio Palma Real",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Carga de Datos ---
# --- Carga de Datos ---
@st.cache_data
def get_data_v3():
    try:
        df_pagos = db_utils.load_data_pagos()
        df_alumnos = db_utils.load_data_alumnos()
        df_deudores = db_utils.load_data_deudores()
        return df_pagos, df_alumnos, df_deudores
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_pagos, df_alumnos, df_deudores = get_data_v3()

# --- Preprocesamiento Adicional ---
if not df_pagos.empty:
    df_pagos['Año'] = df_pagos['Fecha'].dt.year
    df_pagos['Mes'] = df_pagos['Fecha'].dt.strftime('%Y-%m')

# Merge pagos con información del alumno para tener Grado/Curso en pagos
if not df_pagos.empty and not df_alumnos.empty:
    df_pagos = df_pagos.merge(df_alumnos[['Cod_alumno', 'Nom_curso', 'Nom_grado']], on='Cod_alumno', how='left')

# --- Barra Lateral ---
st.sidebar.title("Filtros")

# Filtro de Año
selected_year = None
if not df_pagos.empty:
    unique_years = sorted(df_pagos['Año'].dropna().unique(), reverse=True)
    default_index = unique_years.index(2025) if 2025 in unique_years else 0
    selected_year = st.sidebar.selectbox("Seleccionar Año Lectivo", unique_years, index=default_index)

# Filtro de Grado
selected_grades = []
if not df_alumnos.empty:
    unique_grades = sorted(df_alumnos['Nom_grado'].dropna().unique())
    selected_grades = st.sidebar.multiselect("Seleccionar Grado", unique_grades, default=unique_grades)

# Aplicar Filtros
df_pagos_filtered = df_pagos.copy()
df_deudores_filtered = df_deudores.copy()

if selected_year:
    df_pagos_filtered = df_pagos_filtered[df_pagos_filtered['Año'] == selected_year]
    # Nota: TBL_Alumnos_deudores no parece tener campo de fecha/año explícito fácil, asumimossnapshot actual o filtramos si es posible.
    # Por ahora no filtramos deudores por año histórico ya que suele ser foto actual.

if selected_grades:
    df_pagos_filtered = df_pagos_filtered[df_pagos_filtered['Nom_grado'].isin(selected_grades)]
    # Deudores tiene Nom_curso, necesitamos mapear Curso -> Grado si queremos filtrar por Grado exacto
    # Hacemos un merge rápido para filtrar deudores
    if not df_deudores_filtered.empty and not df_alumnos.empty:
         # Asumimos que la tabla deudores tiene los alumnos actuales
         # Creamos map curso -> grado
         curso_grado_map = df_alumnos[['Nom_curso', 'Nom_grado']].drop_duplicates().set_index('Nom_curso')['Nom_grado'].to_dict()
         df_deudores_filtered['Grado'] = df_deudores_filtered['Nom_curso'].map(curso_grado_map)
         df_deudores_filtered = df_deudores_filtered[df_deudores_filtered['Grado'].isin(selected_grades)]


# --- Dashboard Principal ---

st.markdown("<h1 style='text-align: center;'>Informe de Gestión - Diciembre de 2025</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>📊 Dashboard Financiero - Colegio Gimnasio Palma Real</h3>", unsafe_allow_html=True)


# --- KPIs ---
if not df_pagos_filtered.empty and not df_deudores_filtered.empty:
    total_recaudado = df_pagos_filtered['Valor'].sum()
    total_cartera = df_deudores_filtered['Total_Deuda'].sum()
    pct_recuperacion = 0
    if (total_recaudado + total_cartera) > 0:
        pct_recuperacion = (total_recaudado / (total_recaudado + total_cartera)) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Recaudado", f"${total_recaudado:,.0f}")
    col2.metric("📉 Total Cartera (Deuda)", f"${total_cartera:,.0f}")
    col3.metric("📈 % Recuperación", f"{pct_recuperacion:.1f}%")
else:
    st.warning("No hay datos suficientes para mostrar KPIs.")


# --- Análisis Temporal ---
st.markdown("---")
st.subheader("📅 Tendencia de Recaudo Mensual")
if not df_pagos_filtered.empty:
    # Agrupar por mes
    recaudo_mensual = df_pagos_filtered.groupby('Mes')['Valor'].sum().reset_index()
    fig_temporal = px.area(recaudo_mensual, x='Mes', y='Valor', 
                           title=f"Recaudo Mensual - Año {selected_year}",
                           labels={'Valor': 'Ingresos ($)', 'Mes': 'Mes'},
                           markers=True)
    fig_temporal.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_temporal, width='stretch')
else:
    st.info("No hay datos de recaudos para mostrar.")

# --- Análisis por Nivel ---
st.markdown("---")
st.subheader("🎓 Ingresos por Grado")
if not df_pagos_filtered.empty:
    ingreso_grado = df_pagos_filtered.groupby('Nom_grado')['Valor'].sum().reset_index().sort_values('Valor', ascending=False)
    fig_grado = px.bar(ingreso_grado, x='Nom_grado', y='Valor',
                       color='Valor',
                       title="Ranking de Ingresos por Grado",
                       labels={'Valor': 'Total ($)', 'Nom_grado': 'Grado'})
    fig_grado.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_grado, width='stretch')

st.markdown("---")
st.subheader("🏫 Ingresos por Curso")
if not df_pagos_filtered.empty:
    ingreso_curso = df_pagos_filtered.groupby('Nom_curso')['Valor'].sum().reset_index().sort_values('Valor', ascending=False).head(10) # Top 10
    fig_curso = px.bar(ingreso_curso, x='Nom_curso', y='Valor',
                       title="Top 10 Cursos con Mayores Ingresos",
                       labels={'Valor': 'Total ($)', 'Nom_curso': 'Curso'})
    fig_curso.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_curso, width='stretch')

st.markdown("---")
st.subheader("🪙 Ingresos por Concepto (Rubro)")
if not df_pagos_filtered.empty and 'Nom_rubro' in df_pagos_filtered.columns:
    # Agrupar rubros similares (ej. "Pensión 1", "Pensión 2" -> "Pensión")
    def agrupar_rubro(nombre):
        nombre = str(nombre).lower()
        if 'pensión' in nombre or 'pension' in nombre:
            return 'Pensión'
        elif 'transporte' in nombre:
            return 'Transporte'
        elif 'matrícula' in nombre or 'matricula' in nombre:
            return 'Matrícula'
        elif 'seguro' in nombre:
            return 'Seguro'
        elif 'sistemas' in nombre:
            return 'Sistemas'
        else:
            return nombre.title()

    df_pagos_filtered['Categoria_Rubro'] = df_pagos_filtered['Nom_rubro'].apply(agrupar_rubro)
    ingreso_rubro = df_pagos_filtered.groupby('Categoria_Rubro')['Valor'].sum().reset_index()
    
    fig_rubro = px.pie(ingreso_rubro, values='Valor', names='Categoria_Rubro', 
                       title=f"Distribución de Ingresos por Concepto - Año {selected_year}",
                       hole=0.4)
    fig_rubro.update_traces(textposition='inside', textinfo='percent+label')
    fig_rubro.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_rubro, width='stretch')
else:
    st.info("No hay información de rubros disponible.")

# --- Análisis de Costos y Rentabilidad ---
st.markdown("---")
st.subheader("💰 Análisis de Costos y Rentabilidad (Estimado)")

# Inputs en Sidebar para Costos
st.sidebar.markdown("---")
st.sidebar.subheader("Parámetros de Costos")
num_docentes = st.sidebar.number_input("Número de Docentes", min_value=1, value=25, step=1)
salario_promedio = st.sidebar.number_input("Salario Promedio Base", min_value=0, value=1950000, step=50000)
factor_prestacional = st.sidebar.slider("Factor Prestacional (Carga)", 1.0, 2.0, 1.5, 0.1)

if not df_pagos_filtered.empty and not df_alumnos.empty:
    # 1. Cálculo de Costos Globales
    costo_nomina_mensual = num_docentes * salario_promedio * factor_prestacional
    # Asumimos costo anual = mensual * 12 (o 10 meses lectivos? Usualmente se paga todo el año o 12 meses legalmente)
    # Para simplificar y comparar con "Ingresos a la Fecha" (que suelen ser acumulados del año),
    # deberíamos proyectar el costo al mismo periodo o usar un costo Anual Total estimado.
    # El usuario pidió "Costo x Curso", asumiremos costo anual para comparar con ingresos anuales.
    costo_nomina_anual = costo_nomina_mensual * 12 
    
    # 2. Contar Alumnos Activos Totales y por Curso
    # Filtrar solo activos para el prorrateo de costos (quienes pagan)
    # Nota: Si df_alumnos tiene históricos, filtrar por el año seleccionado si hubiera columna año en alumnos.
    # Asumimos df_alumnos es la foto actual.
    
    # Convertir Activo a numérico si es necesario o filtrar strings 'True'/1
    # Check data type of Activo first
    total_alumnos_activos = df_alumnos[df_alumnos['Activo'] == 1].shape[0]
    
    if total_alumnos_activos > 0:
        costo_por_estudiante = costo_nomina_anual / total_alumnos_activos
    else:
        costo_por_estudiante = 0

    # 3. Preparar Dataframe por Curso para el Análisis
    # Ingresos por curso
    ingresos_curso_df = df_pagos_filtered.groupby('Nom_curso')['Valor'].sum().reset_index()
    ingresos_curso_df.rename(columns={'Valor': 'Ingresos'}, inplace=True)
    
    # Alumnos por curso (Activos)
    alumnos_curso_df = df_alumnos[df_alumnos['Activo'] == 1].groupby('Nom_curso')['Cod_alumno'].count().reset_index()
    alumnos_curso_df.rename(columns={'Cod_alumno': 'Num_Alumnos'}, inplace=True)
    
    # Merge
    analisis_curso = pd.merge(ingresos_curso_df, alumnos_curso_df, on='Nom_curso', how='inner')
    
    # Cálculos Financieros por Curso
    analisis_curso['Costo_Estimado'] = analisis_curso['Num_Alumnos'] * costo_por_estudiante
    analisis_curso['Utilidad'] = analisis_curso['Ingresos'] - analisis_curso['Costo_Estimado']
    analisis_curso['Margen'] = (analisis_curso['Utilidad'] / analisis_curso['Ingresos']) * 100
    
    # Ordenar por Utilidad
    analisis_curso = analisis_curso.sort_values('Utilidad', ascending=False)

    # --- Visualizaciones Costos ---
    
    # 1. KPIs Generales Costos
    kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
    kpi_c1.metric("Costo Nómina Anual (Est.)", f"${costo_nomina_anual:,.0f}")
    kpi_c2.metric("Costo Anual por Alumno", f"${costo_por_estudiante:,.0f}")
    if num_docentes > 0:
        alumnos_x_profe = total_alumnos_activos / num_docentes
        kpi_c3.metric("Alumnos por Docente", f"{alumnos_x_profe:.1f}")

    st.markdown("##### Rentabilidad por Curso (Ingresos vs Costos)")
    
    # 2. Gráfico Barras Agrupadas: Ingresos vs Costos
    # Necesitamos "melt" para plotly grouped bar
    analisis_melted = analisis_curso.melt(id_vars='Nom_curso', value_vars=['Ingresos', 'Costo_Estimado'], var_name='Tipo', value_name='Monto')
    
    fig_rent = px.bar(analisis_melted, x='Nom_curso', y='Monto', color='Tipo', barmode='group',
                      title="Comparativa: Ingresos Reales vs Costos Operativos Estimados",
                      labels={'Monto': 'Valor ($)', 'Nom_curso': 'Curso'},
                      color_discrete_map={'Ingresos': '#00CC96', 'Costo_Estimado': '#EF553B'})
    fig_rent.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_rent, width='stretch')
    
    # 3. Scatter Plot: Utilidad vs Volumen
    st.markdown("##### Matriz de Eficiencia: Volumen de Alumnos vs Utilidad")
    fig_scatter = px.scatter(analisis_curso, x='Num_Alumnos', y='Utilidad', 
                             size='Ingresos', color='Utilidad',
                             hover_name='Nom_curso',
                             title="Eficiencia por Curso (Tamaño burbuja = Ingresos)",
                             color_continuous_scale='RdYlGn',
                             labels={'Num_Alumnos': 'Número de Estudiantes', 'Utilidad': 'Utilidad Neta Estimada ($)'})
    # Add predicted break-even line if possible or just axis lines
    fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray", annotation_text="Punto de Equilibrio")
    fig_scatter.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
    st.plotly_chart(fig_scatter, width='stretch')

else:
    st.info("Necesitamos datos de Pagos y Alumnos (con campo Activo) para calcular costos.")


# --- Semáforo de Cartera ---
st.markdown("---")
st.subheader("🚨 Semáforo de Cartera (Deudas)")

if not df_deudores_filtered.empty:
    st.subheader("Riesgo por Grado (Cartera Total)")
    if 'Grado' in df_deudores_filtered.columns:
        deuda_grado = df_deudores_filtered.groupby('Grado')['Total_Deuda'].sum().reset_index().sort_values('Total_Deuda', ascending=False)
        fig_deuda = px.bar(deuda_grado, x='Grado', y='Total_Deuda',
                           color='Total_Deuda',
                           color_continuous_scale='Reds',
                           title="Grados con Mayor Deuda Acumulada")
        fig_deuda.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
        st.plotly_chart(fig_deuda, width='stretch')
    else:
         st.warning("No se pudo mapear grados para la cartera.")

    # --- Analsis de Deuda detallado (Nuevo) ---
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("**Composición de la Deuda por Concepto**")
        # Sumar columnas de conceptos
        conceptos = ['Matricula', 'Pension', 'Transporte', 'Sistemas', 'Asociacion', 'Otros', 'Ludicas', 'Mpruebas']
        # Check existence of columns
        valid_conceptos = [c for c in conceptos if c in df_deudores_filtered.columns]
        
        if valid_conceptos:
            deuda_concepto = df_deudores_filtered[valid_conceptos].sum().reset_index()
            deuda_concepto.columns = ['Concepto', 'Monto']
            
            # Filtrar montos en cero
            deuda_concepto = deuda_concepto[deuda_concepto['Monto'] > 0]
            
            deuda_concepto = deuda_concepto.sort_values('Monto', ascending=False)
            
            fig_conc = px.bar(deuda_concepto, x='Concepto', y='Monto',
                              color='Monto', color_continuous_scale='OrRd',
                              title="¿Qué se debe más?",
                              labels={'Monto': 'Deuda Total ($)'})
            fig_conc.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
            st.plotly_chart(fig_conc, width='stretch')
            
    with col_det2:
        st.markdown("**Antigüedad de Mora (Por Mes)**")
        # Agrupar por Mes
        if 'Mes' in df_deudores_filtered.columns:
            # Ordenar Meses si son numeros
            deuda_tiempo = df_deudores_filtered.groupby('Mes')['Total_Deuda'].sum().reset_index().sort_values('Mes')
            
            # Mapear mes numérico a nombre si es posible, o dejar como está
            # Asumiendo Mes es int 1-12
            import calendar
            try:
                # Si Mes es numérico 1-12
                # deuda_tiempo['Nombre_Mes'] = deuda_tiempo['Mes'].apply(lambda x: calendar.month_name[int(x)] if 1<=x<=12 else str(x))
                # Pero la user locale puede ser ES. Dejemoslo simple por ahora
                pass
            except:
                pass

            fig_antig = px.bar(deuda_tiempo, x='Mes', y='Total_Deuda',
                               title="Evolución de la Deuda por Mes",
                               labels={'Total_Deuda': 'Monto ($)', 'Mes': 'Mes de Deuda'})
            fig_antig.update_layout(font=dict(size=14), hoverlabel=dict(font_size=18))
            st.plotly_chart(fig_antig, width='stretch')


else:
    st.info("No hay datos de cartera para mostrar.")

# --- Galería de Actividades (Facebook / Web) ---
st.markdown("---")

@st.dialog("📸 Visor de Imagen", width="large")
def view_image(image_path, caption):
    st.image(image_path, caption=caption, use_container_width=True)

with st.expander("📸 Galería de Actividades y Eventos", expanded=True):
    image_folder = 'imagenes'
    if not os.path.exists(image_folder):
        os.makedirs(image_folder)
        
    # Buscar imágenes locales
    local_images = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    if local_images:
        # Mostrar imágenes locales dinámicamente
        num_cols = 3
        cols = st.columns(num_cols)
        for i, img_path in enumerate(local_images):
            with cols[i % num_cols]:
                st.image(img_path, use_container_width=True)
                if st.button("🔍 Ampliar", key=f"img_btn_{i}"):
                    view_image(img_path, "Imagen de la Galería")
                    
        st.success(f"Mostrando {len(local_images)} imágenes de la carpeta '{image_folder}'.")
    else:
        # Fallback: URLs de ejemplo
        img_urls = [
            "https://img.freepik.com/foto-gratis/estudiantes-corriendo-pasillo-universidad_23-2147763809.jpg", 
            "https://img.freepik.com/foto-gratis/grupo-estudiantes-adolescentes-escuela_23-2148141443.jpg", 
            "https://img.freepik.com/foto-gratis/alumnos-felices-profesor-clase_1098-2598.jpg"
        ]
        
        # Mostrar en columnas
        col_gal1, col_gal2, col_gal3 = st.columns(3)
        with col_gal1:
            st.image(img_urls[0], caption="Actividades Deportivas", use_container_width=True)
            if st.button("🔍 Ampliar", key="btn_gal1"):
                view_image(img_urls[0], "Actividades Deportivas")
        with col_gal2:
            st.image(img_urls[1], caption="Convivencia Escolar", use_container_width=True)
            if st.button("🔍 Ampliar", key="btn_gal2"):
                view_image(img_urls[1], "Convivencia Escolar")
        with col_gal3:
            st.image(img_urls[2], caption="Excelencia Académica", use_container_width=True)
            if st.button("🔍 Ampliar", key="btn_gal3"):
                view_image(img_urls[2], "Excelencia Académica")
                
        st.info(f"💡 La carpeta '{image_folder}' está vacía. Agrega tus fotos ahí para que aparezcan aquí automáticamente.")

    st.markdown("---")
    st.markdown("##### 🌐 Conecta con nosotros")
    col_social1, col_social2 = st.columns(2)
    with col_social1:
        st.link_button("📘 Visitar Facebook Oficial", "https://www.facebook.com/gim.palmareal", use_container_width=True)
    with col_social2:
        st.link_button("📺 Ver Video Institucional (YouTube)", "https://www.youtube.com/watch?v=Ivhoj5tRttY", use_container_width=True)
