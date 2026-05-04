import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(page_title="Dashboard Directivo - Análisis de Repuestos", layout="wide")

# Estilo personalizado para KPIs
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
    .main { background-color: #F8FAFC; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    # Cargar el CSV
    df = pd.read_csv('reporte_repuestos_mostrador.xlsx - MOSTRADOR.csv')
    df['fecha'] = pd.to_datetime(df['fecha'])
    # Asegurar orden cronológico para los gráficos de tendencia
    df = df.sort_values('fecha')
    return df

try:
    df = load_data()

    # --- SIDEBAR: FILTROS ---
    st.sidebar.header("Panel de Filtros")
    
    # Filtro de Año
    años = sorted(df['Año'].unique(), reverse=True)
    año_sel = st.sidebar.multiselect("Año", años, default=años[0])
    
    # Filtro de Sucursal
    sucursales = sorted(df['Sucursal'].unique())
    sucursal_sel = st.sidebar.multiselect("Sucursal", sucursales, default=sucursales)
    
    # Filtro de Corredor (Vendedor)
    vendedores = sorted(df['Corredor'].unique())
    vendedor_sel = st.sidebar.multiselect("Corredor / Vendedor", vendedores, default=vendedores)

    # Aplicar filtros al dataframe
    mask = df['Año'].isin(año_sel) & df['Sucursal'].isin(sucursal_sel) & df['Corredor'].isin(vendedor_sel)
    df_filtered = df[mask]

    # --- TÍTULO PRINCIPAL ---
    st.title("📊 Reporte Ejecutivo de Ventas y Rentabilidad")
    st.markdown(f"**Análisis de Repuestos Mostrador** | Periodo: {', '.join(map(str, año_sel))}")
    st.divider()

    # --- SECCIÓN 1: KPIs GLOBALES ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_ventas = df_filtered['Venta Total'].sum()
    total_costo = df_filtered['Costo Total'].sum()
    total_utilidad = df_filtered['Utilidad'].sum()
    margen_promedio = (total_utilidad / total_ventas * 100) if total_ventas > 0 else 0
    ticket_promedio = df_filtered['Venta Total'].mean()

    with col1:
        st.metric("Ventas Totales", f"$ {total_ventas:,.0f}")
    with col2:
        st.metric("Utilidad Total", f"$ {total_utilidad:,.0f}")
    with col3:
        st.metric("Margen sobre Venta", f"{margen_promedio:.2f}%")
    with col4:
        st.metric("Ticket Promedio", f"$ {ticket_promedio:,.0f}")

    st.divider()

    # --- SECCIÓN 2: TENDENCIAS Y GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Tendencia Mensual de Ventas y Utilidad")
        # Agrupar por mes y año para el gráfico
        df_trend = df_filtered.groupby(['Año', 'Mes', df_filtered['fecha'].dt.strftime('%Y-%m')]).agg({
            'Venta Total': 'sum',
            'Utilidad': 'sum'
        }).reset_index().sort_values('fecha')
        
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(x=df_trend['fecha'], y=df_trend['Venta Total'], name='Venta Total', line=dict(color='#1E3A8A', width=3)))
        fig_trend.add_trace(go.Bar(x=df_trend['fecha'], y=df_trend['Utilidad'], name='Utilidad', marker_color='#10B981', opacity=0.6))
        fig_trend.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_trend, use_container_width=True)

    with c2:
        st.subheader("Participación por Sucursal (Ventas)")
        fig_pie = px.pie(df_filtered, values='Venta Total', names='Sucursal', hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- SECCIÓN 3: ANÁLISIS POR CORREDOR ---
    st.divider()
    st.subheader("Ranking de Vendedores (Top Corredores)")
    
    col_rank1, col_rank2 = st.columns([2, 1])

    with col_rank1:
        df_vendedores = df_filtered.groupby('Corredor').agg({
            'Venta Total': 'sum',
            'Utilidad': 'sum',
            'comprobante': 'count'
        }).rename(columns={'comprobante': 'Operaciones'}).reset_index()
        
        df_vendedores['Utilidad por Operación'] = df_vendedores['Utilidad'] / df_vendedores['Operaciones']
        df_vendedores = df_vendedores.sort_values('Venta Total', ascending=False)

        fig_vendedores = px.bar(df_vendedores.head(10), x='Corredor', y='Venta Total', 
                                 text_auto='.2s', title="Top 10 Vendedores por Volumen",
                                 color='Utilidad', color_continuous_scale='Blues')
        st.plotly_chart(fig_vendedores, use_container_width=True)

    with col_rank2:
        st.markdown("**Eficiencia por Vendedor**")
        st.dataframe(df_vendedores[['Corredor', 'Venta Total', 'Utilidad por Operación']]
                     .style.format({'Venta Total': '${:,.0f}', 'Utilidad por Operación': '${:,.0f}'}),
                     hide_index=True, use_container_width=True)

    # --- SECCIÓN 4: TABLA DE DATOS DETALLADA ---
    with st.expander("Ver Detalles de Operaciones (Tabla Completa)"):
        st.dataframe(df_filtered[['fecha', 'comprobante', 'cliente', 'Corredor', 'Sucursal', 'Venta Total', 'Utilidad', '(%) Utilidad']])

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.info("Asegúrate de que el archivo CSV esté en la misma carpeta que este script.")