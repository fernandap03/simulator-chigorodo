"""Simulador exploratorio de capacidad hospitalaria: Chigorodó.

Ejecutar:
    pip install streamlit pandas plotly
    streamlit run simulador_capacidad_chigorodo.py

Las cifras son capacidad teórica y NO estimaciones de demanda.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Capacidad hospitalaria | Chigorodó", page_icon="🏥", layout="wide")

st.title("🏥 Simulador de capacidad hospitalaria | Chigorodó")
st.caption("Escenarios de oferta teórica para la articulación de la red de Urabá. No equivale a demanda esperada ni a pacientes únicos.")

with st.sidebar:
    st.header("Supuestos del escenario")
    ocupacion = st.slider("Ocupación promedio (%)", min_value=60, max_value=95, value=80, step=5)
    estancia_uci = st.slider("Estancia media en UCI (días)", min_value=3, max_value=20, value=8)
    estancia_intermedios = st.slider("Estancia media en intermedios (días)", min_value=2, max_value=15, value=5)
    estancia_hosp = st.slider("Estancia media en hospitalización (días)", min_value=2, max_value=20, value=6)
    st.divider()
    uci = st.number_input("Camas UCI de adultos propuestas", min_value=0, max_value=200, value=10, step=1)
    intermedios = st.number_input("Camas intermedias propuestas", min_value=0, max_value=200, value=10, step=1)
    objetivo_hosp = st.number_input("Meta de 80 camas de hospitalización", min_value=0, max_value=1000, value=80, step=1)
    incluyen_criticas = st.radio(
        "¿La meta de hospitalización incluye las camas de UCI e intermedios?",
        ["No: 80 generales + 20 críticas", "Sí: 80 camas en total"],
        index=0,
    )
    st.divider()
    st.caption("Se supone que toda cama es operativa durante 365 días. La ocupación es un supuesto uniforme para los tres tipos de cama.")

camas_hosp = max(0, objetivo_hosp - uci - intermedios) if incluyen_criticas.startswith("Sí") else objetivo_hosp
if incluyen_criticas.startswith("Sí") and uci + intermedios > objetivo_hosp:
    st.error("La suma de camas críticas supera la meta total. Ajusta los valores de la barra lateral.")
    st.stop()

def calcular_egresos_equivalentes(camas: int, estancia: int) -> float:
    return camas * 365 * (ocupacion / 100) / estancia

resultados = pd.DataFrame([
    {"Servicio": "UCI adultos", "Camas": uci, "Estancia media (días)": estancia_uci},
    {"Servicio": "Cuidados intermedios", "Camas": intermedios, "Estancia media (días)": estancia_intermedios},
    {"Servicio": "Hospitalización general", "Camas": camas_hosp, "Estancia media (días)": estancia_hosp},
])
resultados["Días-cama disponibles/año"] = resultados["Camas"] * 365
resultados["Días-cama ocupados/año"] = resultados["Días-cama disponibles/año"] * ocupacion / 100
resultados["Egresos equivalentes/año"] = resultados["Días-cama ocupados/año"] / resultados["Estancia media (días)"]

c1, c2, c3 = st.columns(3)
for col, servicio in zip((c1, c2, c3), resultados.itertuples(index=False)):
    with col:
        st.metric(servicio[0], f"{servicio[5]:,.0f}".replace(",", "."), help="Egresos equivalentes al año, calculados con los supuestos actuales.")
        st.caption(f"{servicio[1]} camas · estancia media: {servicio[2]} días")

st.info(
    f"Configuración: **{int(resultados['Camas'].sum())} camas totales** "
    f"({uci} UCI, {intermedios} intermedias y {camas_hosp} de hospitalización general). "
    "La suma de egresos equivalentes entre servicios NO representa pacientes únicos: una persona puede transitar entre varios servicios."
)

fig = px.bar(
    resultados,
    x="Servicio",
    y="Egresos equivalentes/año",
    text="Egresos equivalentes/año",
    title="Capacidad anual teórica por servicio",
    labels={"Egresos equivalentes/año": "Egresos equivalentes por año"},
)
fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig.update_layout(yaxis_rangemode="tozero")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Detalle del escenario")
st.dataframe(resultados.round(1), use_container_width=True, hide_index=True)
st.download_button(
    "Descargar escenario en CSV",
    data=resultados.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
    file_name="escenario_chigorodo.csv",
    mime="text/csv",
)

with st.expander("Metodología y limitaciones"):
    st.latex(r"\text{Egresos equivalentes/año}=\frac{\text{Camas}\times365\times\text{Ocupación}}{\text{Estancia media (días)}}")
    st.write(
        "Este modelo mide producción anual teórica bajo supuestos, no demanda observada, necesidad poblacional, "
        "factibilidad clínica, económica o de habilitación. Se deben contrastar los resultados con atenciones SISPRO, "
        "referencias, estancias, ocupación real, oferta REPS y tiempos de acceso. "
        "No sumar los egresos de todos los servicios como personas únicas."
    )
