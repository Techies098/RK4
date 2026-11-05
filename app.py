"""
app.py - Interfaz Web Interactiva en Streamlit para el Vaciado de Tanque (Ley de Torricelli)
--------------------------------------------------------------------------------------------
Trabajo Universitario de Métodos Numéricos - Ingeniería Civil
Demostración de los métodos de Runge-Kutta de 4to orden (RK4), RK2 (Punto Medio) y Euler.
"""

import io
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import streamlit as st
import streamlit.components.v1 as components

from simulacion_widget import generar_html_simulador

from metodos import (
    calcular_parametros,
    crear_edo_torricelli,
    solucion_exacta,
    euler,
    rk2,
    rk4,
    desglose_rk4,
    estudio_convergencia,
    TanqueVaciadoError
)

# Forzar fondo blanco en todas las figuras de Matplotlib (independiente del tema del SO)
matplotlib.rcParams['figure.facecolor'] = 'white'
matplotlib.rcParams['axes.facecolor'] = 'white'
matplotlib.rcParams['savefig.facecolor'] = 'white'

# Configuración de página de Streamlit
st.set_page_config(
    page_title="Vaciado de Tanque - Métodos Numéricos (RK4)",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados para presentación académica
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        border-radius: 8px;
        padding: 12px 16px;
        border-left: 4px solid #2563EB;
        margin-bottom: 10px;
    }
    .formula-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 14px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# BARRA LATERAL: ENTRADA DE DATOS Y PARÁMETROS DEL MODELO
# =============================================================================
st.sidebar.header("⚙️ Parámetros del Problema")
st.sidebar.markdown("Ingrese los parámetros geométricos, hidráulicos y temporales:")

# Campos numéricos con valores por defecto
D = st.sidebar.number_input(
    "Diámetro del tanque D (m)",
    min_value=0.001,
    value=2.0,
    step=0.1,
    format="%.4f",
    help="Diámetro interior del tanque cilíndrico."
)

h0 = st.sidebar.number_input(
    "Altura inicial de agua h0 (m)",
    min_value=0.001,
    value=3.0,
    step=0.25,
    format="%.4f",
    help="Nivel inicial del agua medido desde el orificio."
)

d = st.sidebar.number_input(
    "Diámetro del orificio d (m)",
    min_value=0.0001,
    value=0.05,
    step=0.005,
    format="%.4f",
    help="Diámetro del orificio circular de descarga en el fondo."
)

Cd = st.sidebar.number_input(
    "Coeficiente de descarga Cd (-)",
    min_value=0.001,
    max_value=1.0,
    value=0.6,
    step=0.05,
    format="%.4f",
    help="Coeficiente adimensional de descarga (típicamente 0.60 - 0.65)."
)

h_step = st.sidebar.number_input(
    "Paso de tiempo h (s)",
    min_value=0.01,
    value=300.0,
    step=25.0,
    format="%.2f",
    help="Tamaño del paso de integración temporal para los métodos numéricos."
)

N = st.sidebar.number_input(
    "Número de iteraciones N (entero)",
    min_value=1,
    value=6,
    step=1,
    help="Cantidad exacta de pasos de cálculo numérico."
)

# Botón Calcular
boton_calcular = st.sidebar.button("🚀 Calcular Simulación", use_container_width=True)

# Tiempo final calculado automáticamente (NO se pide al usuario)
t_final = float(N * h_step)
t_final_min = t_final / 60.0

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Tiempo total solicitado:**")
st.sidebar.info(f"**t_final = N · h = {t_final:.1f} s** ({t_final_min:.2f} min)")


# =============================================================================
# VALIDACIONES DE ENTRADA
# =============================================================================
errores_validacion = []

if D <= 0:
    errores_validacion.append("El diámetro del tanque D debe ser estrictamente positivo (> 0).")
if h0 <= 0:
    errores_validacion.append("La altura inicial h0 debe ser estrictamente positiva (> 0).")
if d <= 0:
    errores_validacion.append("El diámetro del orificio d debe ser estrictamente positivo (> 0).")
if not (0 < Cd <= 1.0):
    errores_validacion.append("El coeficiente de descarga Cd debe cumplir: 0 < Cd <= 1.")
if d >= D:
    errores_validacion.append(f"El diámetro del orificio d ({d} m) debe ser estrictamente menor que el del tanque D ({D} m).")
if h_step <= 0:
    errores_validacion.append("El paso de tiempo h debe ser estrictamente positivo (> 0).")
if N < 1:
    errores_validacion.append("El número de iteraciones N debe ser un número entero mayor o igual a 1.")

if errores_validacion:
    for err in errores_validacion:
        st.error(f"❌ Error de Validación: {err}")
    st.stop()

# Advertencias no bloqueantes según requerimientos (N < 5 o N > 100 000)
if N < 5:
    st.warning(f"⚠️ Advertencia: El número de iteraciones N = {N} es menor que 5. Se recomiendan al menos 5 pasos para observar el comportamiento numérico.")
elif N > 100000:
    st.warning(f"⚠️ Advertencia: El número de iteraciones N = {N:,} es muy elevado (> 100,000). El cálculo podría tardar varios segundos.")


# =============================================================================
# CÁLCULO DE PARÁMETROS HIDRÁULICOS Y FÍSICOS
# =============================================================================
g_const = 9.81  # Constante de gravedad en m/s^2
params = calcular_parametros(D=D, h0=h0, d=d, Cd=Cd, g=g_const)

A_tanque = params['A']
a_orificio = params['a']
k_descarga = params['k']
t_vaciado_s = params['t_vaciado']
t_vaciado_min = params['t_vaciado_min']


# =============================================================================
# ENCABEZADO Y RESUMEN DE PROPIEDADES EN PANTALLA PRINCIPAL
# =============================================================================
st.markdown('<div class="main-title">💧 Vaciado de Tanque Cilíndrico - Métodos Numéricos</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Demostración y comparación del método de <b>Runge-Kutta de 4to Orden (RK4)</b>, '
    'RK2 (Punto Medio) y Euler hacia adelante bajo la Ley de Torricelli | Ingeniería Civil</div>',
    unsafe_allow_html=True
)

# Métricas resumen mostradas ANTES de los resultados
st.markdown("### 📋 Propiedades Geométricas e Hidráulicas Calculadas")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        label="Área Tanque A",
        value=f"{A_tanque:.4f} m²",
        help=f"A = π · D² / 4 (D = {D} m)"
    )
with col2:
    st.metric(
        label="Área Orificio a",
        value=f"{a_orificio:.6f} m²",
        help=f"a = π · d² / 4 (d = {d} m)"
    )
with col3:
    st.metric(
        label="Coeficiente k",
        value=f"{k_descarga:.7f}",
        help="k = Cd · (a / A) · √(2g)"
    )
with col4:
    st.metric(
        label="Tiempo Vaciado Total",
        value=f"{t_vaciado_s:.1f} s",
        delta=f"{t_vaciado_min:.2f} min",
        delta_color="off",
        help="t_vaciado = 2·√h0 / k"
    )
with col5:
    estado_tiempo = "Simulación válida" if t_final <= t_vaciado_s else "Excede vaciado"
    delta_color = "normal" if t_final <= t_vaciado_s else "inverse"
    st.metric(
        label="Tiempo Solicitado t_final",
        value=f"{t_final:.1f} s",
        delta=estado_tiempo,
        delta_color=delta_color,
        help="t_final = N · h"
    )

st.markdown("---")


# =============================================================================
# EJECUCIÓN DE LA SIMULACIÓN Y MANEJO DE EXCEPCIONES
# =============================================================================
f_edo = crear_edo_torricelli(k_descarga, t_vaciado=t_vaciado_s, t_solicitado=t_final)

try:
    # Solución analítica exacta
    t_malla = np.linspace(0.0, t_final, int(N) + 1)
    h_analitica = solucion_exacta(t_malla, h0, k_descarga, t_vaciado=t_vaciado_s, t_solicitado=t_final)

    # Integración numérica con los 3 métodos
    t_euler, y_euler = euler(f_edo, h0, 0.0, h_step, int(N), t_vaciado=t_vaciado_s, t_solicitado=t_final)
    t_rk2, y_rk2 = rk2(f_edo, h0, 0.0, h_step, int(N), t_vaciado=t_vaciado_s, t_solicitado=t_final)
    t_rk4, y_rk4 = rk4(f_edo, h0, 0.0, h_step, int(N), t_vaciado=t_vaciado_s, t_solicitado=t_final)

except TanqueVaciadoError as err:
    st.error(f"🚨 **Error de Tanque Vaciado:**\n\n{err.mensaje}")
    st.info("💡 **Acción recomendada:** En la barra lateral izquierda, disminuya el paso de tiempo $h$ o reduzca el número de iteraciones $N$ para que $N \\cdot h \\le t_{\\text{vaciado}}$.")
    st.stop()
except Exception as ex:
    st.error(f"❌ Error inesperado durante la simulación: {str(ex)}")
    st.stop()


# =============================================================================
# SIMULACIÓN DINÁMICA INTERACTIVA EN TIEMPO REAL
# =============================================================================
html_simulador = generar_html_simulador(
    D=D,
    h0=h0,
    d=d,
    Cd=Cd,
    g=g_const,
    k=k_descarga,
    t_vaciado=t_vaciado_s,
    t_final=t_final,
    t_rk4=t_rk4,
    y_rk4=y_rk4
)
components.html(html_simulador, height=620, scrolling=False)
st.markdown("---")


# =============================================================================
# RESULTADOS ORGANIZADOS EN PESTAÑAS (st.tabs)
# =============================================================================
tabs = st.tabs([
    "1. 📖 Modelo",
    "2. 📊 Tabla Comparativa",
    "3. 🔍 Desglose RK4",
    "4. 📈 Convergencia",
    "5. 📉 Gráficos",
    "6. ⚠️ Análisis cerca de h = 0"
])


# -----------------------------------------------------------------------------
# PESTAÑA 1: MODELO
# -----------------------------------------------------------------------------
with tabs[0]:
    st.subheader("1. Modelo Matemático y Formulación Física")

    st.markdown("""
    El problema modela el vaciado hidrodinámico por gravedad de un tanque cilíndrico de sección constante
    $A$ a través de un orificio circular de fondo de área $a$, bajo la hipótesis de flujo cuasiestacionario
    descrito por la **Ley de Torricelli**.
    """)

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("#### 📐 Ecuaciones Diferenciales y Parámetros")
        st.latex(r"\frac{dh}{dt} = -k \sqrt{\max(h, 0)}")
        st.markdown("donde la constante global de vaciado $k$ agrupa las propiedades geométricas e hidráulicas:")
        st.latex(r"k = C_d \cdot \left(\frac{a}{A}\right) \sqrt{2g} = C_d \cdot \left(\frac{d}{D}\right)^2 \sqrt{2g}")
        st.markdown("con las áreas transversales:")
        st.latex(r"A = \frac{\pi D^2}{4}, \qquad a = \frac{\pi d^2}{4}")

    with col_m2:
        st.markdown("#### 🎯 Solución Analítica Exacta")
        st.markdown("""
        Integrando por separación de variables desde la condición inicial $h(0) = h_0$:
        """)
        st.latex(r"\int_{h_0}^{h} \frac{dh}{\sqrt{h}} = -k \int_0^t dt \implies 2\sqrt{h} - 2\sqrt{h_0} = -k t")
        st.latex(r"h(t) = \left(\sqrt{h_0} - \frac{k}{2} t\right)^2, \quad \text{válida únicamente para } t \le t_{\text{vaciado}}")
        st.markdown("El tiempo total de vaciado teórico se obtiene cuando el nivel de agua alcanza $h = 0$:")
        st.latex(r"t_{\text{vaciado}} = \frac{2\sqrt{h_0}}{k}")

    st.markdown("---")
    st.markdown("#### 📑 Resumen de Datos de Entrada y Valores Calculados")
    df_parametros = pd.DataFrame([
        {"Parámetro": "Diámetro del tanque (D)", "Símbolo": "D", "Valor": f"{D:.4f}", "Unidad": "m"},
        {"Parámetro": "Altura inicial de agua (h0)", "Símbolo": "h0", "Valor": f"{h0:.4f}", "Unidad": "m"},
        {"Parámetro": "Diámetro del orificio (d)", "Símbolo": "d", "Valor": f"{d:.4f}", "Unidad": "m"},
        {"Parámetro": "Coeficiente de descarga", "Símbolo": "Cd", "Valor": f"{Cd:.4f}", "Unidad": "-"},
        {"Parámetro": "Aceleración de la gravedad", "Símbolo": "g", "Valor": f"{g_const:.2f}", "Unidad": "m/s²"},
        {"Parámetro": "Paso de tiempo de integración", "Símbolo": "h", "Valor": f"{h_step:.2f}", "Unidad": "s"},
        {"Parámetro": "Número de iteraciones", "Símbolo": "N", "Valor": f"{int(N)}", "Unidad": "pasos"},
        {"Parámetro": "Área transversal del tanque", "Símbolo": "A", "Valor": f"{A_tanque:.6f}", "Unidad": "m²"},
        {"Parámetro": "Área del orificio de fondo", "Símbolo": "a", "Valor": f"{a_orificio:.8f}", "Unidad": "m²"},
        {"Parámetro": "Constante de descarga global", "Símbolo": "k", "Valor": f"{k_descarga:.8f}", "Unidad": "m^(1/2)/s"},
        {"Parámetro": "Tiempo total de vaciado teórico", "Símbolo": "t_vaciado", "Valor": f"{t_vaciado_s:.2f} s ({t_vaciado_min:.2f} min)", "Unidad": "s (min)"},
        {"Parámetro": "Tiempo total de simulación", "Símbolo": "t_final", "Valor": f"{t_final:.2f} s ({t_final_min:.2f} min)", "Unidad": "s (min)"}
    ])
    # Tabla estática sin scroll integrada en el fondo de la página
    st.table(df_parametros, hide_index=True)


# -----------------------------------------------------------------------------
# PESTAÑA 2: TABLA COMPARATIVA
# -----------------------------------------------------------------------------
with tabs[1]:
    st.subheader("2. Tabla Comparativa de Soluciones y Errores Absolutos")
    st.markdown("""
    Comparación paso a paso de los valores obtenidos por la **Solución Exacta**, **Euler** hacia adelante,
    **RK2 (Punto Medio)** y **RK4 clásico**, junto con los correspondientes errores absolutos
    $E_{\\text{abs}} = |h_{\\text{num}}(t) - h_{\\text{exacta}}(t)|$.
    """)

    err_euler = np.abs(y_euler - h_analitica)
    err_rk2 = np.abs(y_rk2 - h_analitica)
    err_rk4 = np.abs(y_rk4 - h_analitica)

    df_comparativa = pd.DataFrame({
        "Iteración": np.arange(len(t_malla), dtype=int),
        "t (s)": t_malla,
        "Solución Exacta (m)": h_analitica,
        "Euler (m)": y_euler,
        "RK2 (m)": y_rk2,
        "RK4 (m)": y_rk4,
        "Error Abs. Euler (m)": err_euler,
        "Error Abs. RK2 (m)": err_rk2,
        "Error Abs. RK4 (m)": err_rk4
    })

    # Mostrar dataframe con formato de precisión
    st.dataframe(
        df_comparativa.style.format({
            "Iteración": "{:d}",
            "t (s)": "{:.1f}",
            "Solución Exacta (m)": "{:.6f}",
            "Euler (m)": "{:.6f}",
            "RK2 (m)": "{:.6f}",
            "RK4 (m)": "{:.6f}",
            "Error Abs. Euler (m)": "{:.6e}",
            "Error Abs. RK2 (m)": "{:.6e}",
            "Error Abs. RK4 (m)": "{:.6e}"
        }),
        use_container_width=True,
        hide_index=True
    )

    # Botón de descarga de la tabla comparativa en formato CSV
    csv_comparativa = df_comparativa.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar Tabla Comparativa (CSV)",
        data=csv_comparativa,
        file_name="tabla_comparativa_vaciado_tanque.csv",
        mime="text/csv"
    )


# -----------------------------------------------------------------------------
# PESTAÑA 3: DESGLOSE RK4
# -----------------------------------------------------------------------------
with tabs[2]:
    st.subheader("3. Desglose Paso a Paso de Runge-Kutta de 4to Orden (RK4)")
    st.markdown("""
    Cálculo detallado de las pendientes intermedias $k_1, k_2, k_3, k_4$ para las **dos primeras iteraciones**,
    con las fórmulas algebraicas y sustitución numérica exacta, listo para incorporar directamente en el informe universitario.
    """)

    num_pasos_mostrar = min(2, int(N))
    pasos_rk4 = desglose_rk4(f_edo, h0, 0.0, h_step, num_pasos=num_pasos_mostrar)

    st.markdown("""
    #### 📐 Fórmulas del Algoritmo RK4 Clásico:
    """)
    st.latex(r"k_1 = f(t_n, y_n) = -k \sqrt{y_n}")
    st.latex(r"k_2 = f\left(t_n + \frac{h}{2}, \, y_n + \frac{h}{2} k_1\right)")
    st.latex(r"k_3 = f\left(t_n + \frac{h}{2}, \, y_n + \frac{h}{2} k_2\right)")
    st.latex(r"k_4 = f\left(t_n + h, \, y_n + h \, k_3\right)")
    st.latex(r"y_{n+1} = y_n + \frac{h}{6} \left(k_1 + 2k_2 + 2k_3 + k_4\right)")

    for paso in pasos_rk4:
        p_num = paso['paso']
        st.markdown(f"### 🔹 Iteración {p_num}: de $t_{{{p_num-1}}} = {paso['tn']:.1f}$ s a $t_{{{p_num}}} = {paso['t_sig']:.1f}$ s")

        st.markdown(f"""
        **Condición inicial del paso:**
        * $t_{{{p_num-1}}} = {paso['tn']:.2f}$ s
        * $h_{{{p_num-1}}} = {paso['yn']:.6f}$ m
        * Paso de tiempo: $h = {h_step:.2f}$ s, $\\frac{{h}}{{2}} = {h_step/2.0:.2f}$ s
        """)

        col_k12, col_k34 = st.columns(2)

        with col_k12:
            st.markdown(f"""
            **1. Cálculo de $k_1$:**
            $$k_1 = f({paso['tn']:.1f}, {paso['yn']:.6f}) = -{k_descarga:.7f} \\cdot \\sqrt{{{paso['yn']:.6f}}} = {paso['k1']:.8f} \\text{{ m/s}}$$

            **2. Cálculo de $k_2$:**
            * Punto de evaluación:
              $$t = t_n + \\frac{{h}}{{2}} = {paso['tn']:.1f} + {h_step/2.0:.1f} = {paso['t_k2']:.1f} \\text{{ s}}$$
              $$h^*_1 = h_n + \\frac{{h}}{{2}} k_1 = {paso['yn']:.6f} + ({h_step/2.0:.1f})({paso['k1']:.8f}) = {paso['y_k2']:.6f} \\text{{ m}}$$
            * Pendiente:
              $$k_2 = f({paso['t_k2']:.1f}, {paso['y_k2']:.6f}) = -{k_descarga:.7f} \\cdot \\sqrt{{{paso['y_k2']:.6f}}} = {paso['k2']:.8f} \\text{{ m/s}}$$
            """)

        with col_k34:
            st.markdown(f"""
            **3. Cálculo de $k_3$:**
            * Punto de evaluación:
              $$t = t_n + \\frac{{h}}{{2}} = {paso['tn']:.1f} + {h_step/2.0:.1f} = {paso['t_k3']:.1f} \\text{{ s}}$$
              $$h^*_2 = h_n + \\frac{{h}}{{2}} k_2 = {paso['yn']:.6f} + ({h_step/2.0:.1f})({paso['k2']:.8f}) = {paso['y_k3']:.6f} \\text{{ m}}$$
            * Pendiente:
              $$k_3 = f({paso['t_k3']:.1f}, {paso['y_k3']:.6f}) = -{k_descarga:.7f} \\cdot \\sqrt{{{paso['y_k3']:.6f}}} = {paso['k3']:.8f} \\text{{ m/s}}$$

            **4. Cálculo de $k_4$:**
            * Punto de evaluación:
              $$t = t_n + h = {paso['tn']:.1f} + {h_step:.1f} = {paso['t_k4']:.1f} \\text{{ s}}$$
              $$h^*_3 = h_n + h \\cdot k_3 = {paso['yn']:.6f} + ({h_step:.1f})({paso['k3']:.8f}) = {paso['y_k4']:.6f} \\text{{ m}}$$
            * Pendiente:
              $$k_4 = f({paso['t_k4']:.1f}, {paso['y_k4']:.6f}) = -{k_descarga:.7f} \\cdot \\sqrt{{{paso['y_k4']:.6f}}} = {paso['k4']:.8f} \\text{{ m/s}}$$
            """)

        st.markdown(f"""
        **5. Pendiente ponderada y nivel resultante $h_{{{p_num}}}$:**
        $$\\phi = \\frac{{k_1 + 2k_2 + 2k_3 + k_4}}{{6}} = \\frac{{{paso['k1']:.8f} + 2({paso['k2']:.8f}) + 2({paso['k3']:.8f}) + {paso['k4']:.8f}}}{{6}} = {paso['pend_prom']:.8f} \\text{{ m/s}}$$
        $$\\Delta h = h \\cdot \\phi = ({h_step:.1f}) \\cdot ({paso['pend_prom']:.8f}) = {paso['delta_y']:.6f} \\text{{ m}}$$
        $$h_{{{p_num}}} = h_{{{p_num-1}}} + \\Delta h = {paso['yn']:.6f} + ({paso['delta_y']:.6f}) = \\mathbf{{{paso['y_sig']:.6f}}} \\text{{ m}}$$
        """)
        st.markdown("---")


# -----------------------------------------------------------------------------
# PESTAÑA 4: CONVERGENCIA
# -----------------------------------------------------------------------------
with tabs[3]:
    st.subheader("4. Estudio de Convergencia y Orden Numérico Observado")
    st.markdown(f"""
    Se mantiene el tiempo final constante en **$t_{{\\text{{final}}}} = {t_final:.1f}$ s** y se refina
    progresivamente la discretización temporal con factores $1, 2, 4, 8, 16$:
    $$(h, N), \\; (h/2, 2N), \\; (h/4, 4N), \\; (h/8, 8N), \\; (h/16, 16N)$$
    Se evalúa el error absoluto al final de la simulación en función del paso $h$ y se calcula la pendiente
    en escala logarítmica (orden de convergencia experimental $p$, donde $E \\propto h^p$).
    """)

    datos_conv, pendientes_conv, adv_conv = estudio_convergencia(
        f=f_edo,
        h0=h0,
        t0=0.0,
        h_base=h_step,
        N_base=int(N),
        k=k_descarga,
        t_vaciado=t_vaciado_s
    )

    if adv_conv:
        for adv in adv_conv:
            st.warning(f"⚠️ {adv}")

    df_conv = pd.DataFrame(datos_conv)

    # Mostrar métricas de orden de convergencia observado
    col_p1, col_p2, col_p3 = st.columns(3)
    p_euler = pendientes_conv.get('Euler_err')
    p_rk2 = pendientes_conv.get('RK2_err')
    p_rk4 = pendientes_conv.get('RK4_err')

    with col_p1:
        st.metric(
            label="Pendiente Euler (Orden 1)",
            value=f"p ≈ {p_euler:.2f}" if p_euler is not None else "N/A",
            delta="Esperado: ~1.0",
            delta_color="off"
        )
    with col_p2:
        st.metric(
            label="Pendiente RK2 (Orden 2)",
            value=f"p ≈ {p_rk2:.2f}" if p_rk2 is not None else "N/A",
            delta="Esperado: ~2.0",
            delta_color="off"
        )
    with col_p3:
        st.metric(
            label="Pendiente RK4 (Orden 4)",
            value=f"p ≈ {p_rk4:.2f}" if p_rk4 is not None else "N/A",
            delta="Esperado: ~4.0",
            delta_color="off"
        )

    # Formateo de la tabla de convergencia
    df_conv_display = df_conv.rename(columns={
        "Factor": "Factor Malla",
        "h (s)": "Paso h (s)",
        "N": "Iteraciones N",
        "Euler_err": "Error Euler (m)",
        "RK2_err": "Error RK2 (m)",
        "RK4_err": "Error RK4 (m)"
    })

    st.dataframe(
        df_conv_display.style.format({
            "Paso h (s)": "{:.3f}",
            "Iteraciones N": "{:d}",
            "Error Euler (m)": "{:.6e}",
            "Error RK2 (m)": "{:.6e}",
            "Error RK4 (m)": "{:.6e}"
        }, na_rep="Tanque vacío"),
        use_container_width=True,
        hide_index=True
    )

    # Gráfico Log-Log de convergencia con Matplotlib
    fig_conv, ax_conv = plt.subplots(figsize=(8.5, 5.0), dpi=200)

    # Filtrar datos válidos para graficar
    hs = df_conv['h (s)'].values
    err_e = df_conv['Euler_err'].values
    err_r2 = df_conv['RK2_err'].values
    err_r4 = df_conv['RK4_err'].values

    # Euler
    mask_e = [v is not None and v > 0 for v in err_e]
    if any(mask_e):
        ax_conv.loglog(hs[mask_e], err_e[mask_e], 'o--', color='#DC2626', linewidth=1.8, markersize=7,
                       label=f"Euler (p_obs = {p_euler:.2f})" if p_euler else "Euler")

    # RK2
    mask_r2 = [v is not None and v > 0 for v in err_r2]
    if any(mask_r2):
        ax_conv.loglog(hs[mask_r2], err_r2[mask_r2], 's--', color='#D97706', linewidth=1.8, markersize=7,
                       label=f"RK2 Punto Medio (p_obs = {p_rk2:.2f})" if p_rk2 else "RK2")

    # RK4
    mask_r4 = [v is not None and v > 0 for v in err_r4]
    if any(mask_r4):
        ax_conv.loglog(hs[mask_r4], err_r4[mask_r4], '^--', color='#2563EB', linewidth=2.0, markersize=8,
                       label=f"RK4 Clásico (p_obs = {p_rk4:.2f})" if p_rk4 else "RK4")

    ax_conv.set_title("Estudio de Convergencia: Error en $t_{\\mathrm{final}}$ vs Paso $h$ (Escala Log-Log)", fontsize=12, fontweight='bold', pad=10)
    ax_conv.set_xlabel("Tamaño del paso $h$ [s]", fontsize=11)
    ax_conv.set_ylabel("Error Absoluto $|h_{\\mathrm{num}} - h_{\\mathrm{exacta}}|$ [m]", fontsize=11)

    # Configuración del eje X: evitar notación científica y mostrar los pasos h evaluados
    hs_validos = sorted(list(set(hs)))
    ax_conv.set_xticks(hs_validos)
    ax_conv.xaxis.set_major_formatter(ticker.FormatStrFormatter('%g'))
    ax_conv.xaxis.set_minor_formatter(ticker.NullFormatter())

    ax_conv.grid(True, which="both", ls=":", color='gray', alpha=0.6)
    ax_conv.legend(fontsize=10, loc='lower right', framealpha=0.95)

    st.pyplot(fig_conv)

    # Botones de descarga de la pestaña de convergencia
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        csv_conv = df_conv_display.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Tabla de Convergencia (CSV)",
            data=csv_conv,
            file_name="convergencia_vaciado_tanque.csv",
            mime="text/csv"
        )
    with col_d2:
        buf_conv = io.BytesIO()
        fig_conv.savefig(buf_conv, format='png', dpi=200, bbox_inches='tight')
        st.download_button(
            label="📥 Descargar Gráfico de Convergencia (PNG 200 DPI)",
            data=buf_conv.getvalue(),
            file_name="grafico_convergencia_loglog.png",
            mime="image/png"
        )


# -----------------------------------------------------------------------------
# PESTAÑA 5: GRÁFICOS
# -----------------------------------------------------------------------------
with tabs[4]:
    st.subheader("5. Gráficos Comparativos de Perfil de Vaciado y Error Temporal")

    col_g1, col_g2 = st.columns(2)

    # Gráfico 1: Perfil de Vaciado h(t)
    with col_g1:
        st.markdown("#### Perfil de Altura del Agua $h(t)$")
        fig_perfil, ax_p = plt.subplots(figsize=(6.5, 4.8), dpi=200)

        # Malla continua fina para solución exacta
        t_fino = np.linspace(0.0, min(t_final, t_vaciado_s), 200)
        h_fino = solucion_exacta(t_fino, h0, k_descarga, t_vaciado_s, t_final)

        ax_p.plot(t_fino, h_fino, 'k-', linewidth=2.0, label="Solución Exacta", alpha=0.9)
        ax_p.plot(t_euler, y_euler, 'o--', color='#DC2626', linewidth=1.5, markersize=5, label="Euler")
        ax_p.plot(t_rk2, y_rk2, 's--', color='#D97706', linewidth=1.5, markersize=5, label="RK2 (Punto Medio)")
        ax_p.plot(t_rk4, y_rk4, '^--', color='#2563EB', linewidth=1.7, markersize=6, label="RK4 Clásico")

        ax_p.axhline(0, color='gray', linestyle=':', alpha=0.7)
        ax_p.set_title("Altura de Agua $h(t)$ vs Tiempo", fontsize=11, fontweight='bold')
        ax_p.set_xlabel("Tiempo $t$ [s]", fontsize=10)
        ax_p.set_ylabel("Altura $h$ [m]", fontsize=10)
        ax_p.set_ylim(bottom=max(-0.1, -0.05 * h0))
        ax_p.ticklabel_format(style='plain', axis='x', useOffset=False)
        ax_p.grid(True, linestyle='--', alpha=0.5)
        ax_p.legend(fontsize=9, loc='upper right', framealpha=0.95)

        st.pyplot(fig_perfil)

        buf_perfil = io.BytesIO()
        fig_perfil.savefig(buf_perfil, format='png', dpi=200, bbox_inches='tight')
        st.download_button(
            label="📥 Descargar Gráfico h(t) (PNG 200 DPI)",
            data=buf_perfil.getvalue(),
            file_name="grafico_perfil_vaciado_ht.png",
            mime="image/png"
        )

    # Gráfico 2: Evolución Temporal del Error Absoluto
    with col_g2:
        st.markdown("#### Error Absoluto vs Tiempo $E_{\\mathrm{abs}}(t)$")
        fig_err, ax_e = plt.subplots(figsize=(6.5, 4.8), dpi=200)

        ax_e.plot(t_malla, err_euler, 'o--', color='#DC2626', linewidth=1.6, markersize=5, label="Error Euler")
        ax_e.plot(t_malla, err_rk2, 's--', color='#D97706', linewidth=1.6, markersize=5, label="Error RK2")
        ax_e.plot(t_malla, err_rk4, '^--', color='#2563EB', linewidth=1.8, markersize=6, label="Error RK4")

        ax_e.set_title("Evolución del Error Absoluto", fontsize=11, fontweight='bold')
        ax_e.set_xlabel("Tiempo $t$ [s]", fontsize=10)
        ax_e.set_ylabel("Error Absoluto $|h_{\\mathrm{num}} - h_{\\mathrm{exacta}}|$ [m]", fontsize=10)
        ax_e.ticklabel_format(style='plain', axis='x', useOffset=False)
        ax_e.grid(True, linestyle='--', alpha=0.5)
        ax_e.legend(fontsize=9, loc='upper left', framealpha=0.95)

        st.pyplot(fig_err)

        buf_err = io.BytesIO()
        fig_err.savefig(buf_err, format='png', dpi=200, bbox_inches='tight')
        st.download_button(
            label="📥 Descargar Gráfico Error vs Tiempo (PNG 200 DPI)",
            data=buf_err.getvalue(),
            file_name="grafico_error_vs_tiempo.png",
            mime="image/png"
        )


# -----------------------------------------------------------------------------
# PESTAÑA 6: ANÁLISIS CERCA DE H = 0
# -----------------------------------------------------------------------------
with tabs[5]:
    st.subheader("6. Análisis del Comportamiento Numérico cerca de h = 0")

    st.markdown("""
    En el vaciado de un depósito por un orificio mediante la Ley de Torricelli, la ecuación diferencial
    ordinaria presenta una particularidad matemática de gran relevancia para la ingeniería:
    """)

    st.latex(r"\frac{dh}{dt} = f(t, h) = -k \sqrt{\max(h, 0)}")

    col_a1, col_a2 = st.columns(2)

    with col_a1:
        st.markdown("#### 1. Pérdida de Diferenciabilidad y Condición de Lipschitz")
        st.markdown("""
        Al calcular la derivada parcial de la función $f(t, h)$ con respecto a la variable de estado $h$:
        """)
        st.latex(r"\frac{\partial f}{\partial h} = -\frac{k}{2\sqrt{h}}")
        st.markdown("""
        Cuando el nivel del agua se aproxima al fondo del tanque ($h \\to 0^+$):
        """)
        st.latex(r"\lim_{h \to 0^+} \left| \frac{\partial f}{\partial h} \right| = \lim_{h \to 0^+} \frac{k}{2\sqrt{h}} = +\infty")
        st.markdown("""
        * **No diferenciable en $h = 0$:** La función raíz cuadrada no posee derivada finita en cero.
        * **Falla de la condición de Lipschitz:** En un entorno de $h = 0$, no existe una constante finita $L < \\infty$ tal que:
          $$|f(t, h_1) - f(t, h_2)| \\le L |h_1 - h_2|$$
        * Por el **Teorema de Existencia y Unicidad de Picard-Lindelöf**, la unicidad de soluciones se compromete
          en el punto singular $h = 0$.
        """)

    with col_a2:
        st.markdown("#### 2. Crecimiento del Error al Acercarse a $t_{\\text{vaciado}}$")
        st.markdown(r"""
        Los métodos de Runge-Kutta clásicos (incluidos Euler, RK2 y RK4) se fundamentan en la expansión en
        **series de Taylor** de la solución exacta alrededor de cada paso $t_n$:
        $$h(t_n + h) = h(t_n) + h h'(t_n) + \frac{h^2}{2} h''(t_n) + \frac{h^3}{6} h'''(t_n) + \dots$$
        Sin embargo, al calcular derivadas sucesivas de $h(t)$:
        * $h'(t) = -k \sqrt{h}$
        * $h''(t) = \frac{k^2}{2} = \text{constante}$
        * $h'''(t) = 0$ (para $t < t_{\text{vaciado}}$)
        
        A medida que $t \\to t_{\\text{vaciado}}$:
        1. **Overshoot numérico en Euler:** Euler proyecta una tangente recta con pendiente constante durante todo el paso $h$.
           Si el paso es relativamente grande ($h = 300$ s), el decremento calculado $\\Delta h = h \\cdot f(t_n, h_n)$ supera
           la cantidad física remanente de agua, provocando valores negativos artificiales ($h \\le 0$).
        2. **Ventaja de RK4:** RK4 muestrea 4 puntos intermedios en el intervalo $[t_n, t_n + h]$, capturando la curvatura
           suave parabólica $h(t) \\propto (t - t_{\\text{vaciado}})^2$ y manteniendo alta precisión hasta las proximidades del vaciado.
        3. **Implicación en Ingeniería Civil:** En sistemas hidráulicos reales (vaciado de presas, canales con frente seco),
           los modelos con singularidades en la frontera requieren pasos adaptativos o formulaciones implícitas conservativas.
        """)

    st.info("""
    💡 **Conclusión Académica:** Cuando la simulación se extiende cerca o más allá del tiempo teórico de vaciado
    ($N \\cdot h \\approx t_{\\text{vaciado}}$), el error relativo crece exponencialmente y cualquier integración numérica
    de paso fijo explícito debe detenerse formalmente al detectar $h \\le 0$ para evitar violar el balance de masa físico.
    """)
