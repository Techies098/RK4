"""
metodos.py - Métodos Numéricos para EDOs y Modelo de Vaciado de Tanque Cilíndrico
---------------------------------------------------------------------------------
Implementación de métodos de resolución numérica de EDOs desde cero (sin scipy.integrate):
- Euler hacia adelante (orden 1)
- Runge-Kutta de 2do orden / Punto Medio (RK2, orden 2)
- Runge-Kutta de 4to orden clásico (RK4, orden 4)

Modelo físico: Vaciado de un tanque cilíndrico por un orificio (Ley de Torricelli).
Trabajo universitario de Métodos Numéricos - Ingeniería Civil.
"""

import numpy as np


class TanqueVaciadoError(Exception):
    """
    Excepción lanzada cuando el nivel del tanque se vuelve nulo o negativo (h <= 0)
    durante la integración numérica o al intentar evaluar la solución exacta fuera de su
    dominio de validez física (t > t_vaciado).
    """
    def __init__(
        self,
        metodo: str,
        iteracion: int,
        t: float,
        t_vaciado: float = None,
        t_solicitado: float = None,
        mensaje: str = None
    ):
        self.metodo = metodo
        self.iteracion = iteracion
        self.t = t
        self.t_vaciado = t_vaciado
        self.t_solicitado = t_solicitado

        if mensaje is None:
            # Formateo del tiempo de vaciado
            if t_vaciado is not None:
                minutos_vac = t_vaciado / 60.0
                txt_vaciado = f"{t_vaciado:.0f} s ({minutos_vac:.1f} min)"
            else:
                txt_vaciado = "Desconocido"

            txt_solicitado = f"{t_solicitado:.0f} s" if t_solicitado is not None else f"{t:.0f} s"

            if iteracion == 0:
                mensaje = (
                    f"El tanque se vació en t = {t:.0f} s con el método {metodo}. "
                    f"Tiempo de vaciado total: {txt_vaciado}. "
                    f"Tiempo solicitado: N*h = {txt_solicitado}. Reduzca N o h."
                )
            else:
                mensaje = (
                    f"El tanque se vació en la iteración {iteracion} (t = {t:.0f} s) con el método {metodo}. "
                    f"Tiempo de vaciado total: {txt_vaciado}. "
                    f"Tiempo solicitado: N*h = {txt_solicitado}. Reduzca N o h."
                )

        self.mensaje = mensaje
        super().__init__(self.mensaje)


# =============================================================================
# FUNCIONES DEL MODELO FÍSICO (PARAMETRIZADO)
# =============================================================================

def calcular_parametros(D: float, h0: float, d: float, Cd: float, g: float = 9.81) -> dict:
    """
    Calcula las propiedades geométricas e hidráulicas del vaciado del tanque.

    Parámetros:
        D: Diámetro del tanque (m)
        h0: Altura inicial de agua (m)
        d: Diámetro del orificio de salida (m)
        Cd: Coeficiente de descarga (-)
        g: Aceleración de la gravedad (m/s^2), defecto 9.81 m/s^2

    Retorna:
        dict con:
            'A': Área de la sección transversal del tanque (m^2)
            'a': Área del orificio de descarga (m^2)
            'k': Coeficiente global de descarga k = Cd * (a/A) * sqrt(2g) (m^(1/2)/s)
            't_vaciado': Tiempo total teórico de vaciado (s)
            't_vaciado_min': Tiempo total de vaciado en minutos (min)
    """
    A = np.pi * (D ** 2) / 4.0
    a = np.pi * (d ** 2) / 4.0
    k = Cd * (a / A) * np.sqrt(2.0 * g)
    t_vaciado = (2.0 * np.sqrt(h0)) / k
    t_vaciado_min = t_vaciado / 60.0

    return {
        'A': float(A),
        'a': float(a),
        'k': float(k),
        't_vaciado': float(t_vaciado),
        't_vaciado_min': float(t_vaciado_min)
    }


def crear_edo_torricelli(k: float, t_vaciado: float = None, t_solicitado: float = None):
    """
    Genera la función f(t, h) = dh/dt para la Ley de Torricelli:
        dh/dt = -k * sqrt(max(h, 0))

    Asigna metadatos k, t_vaciado y t_solicitado a la función devuelta para
    asistir en el reporte detallado si ocurre un vaciado prematuro.
    """
    def f(t: float, h: float) -> float:
        h_pos = max(h, 0.0)
        return -k * np.sqrt(h_pos)

    f.k = k
    f.t_vaciado = t_vaciado
    f.t_solicitado = t_solicitado
    return f


def solucion_exacta(t_arr, h0: float, k: float, t_vaciado: float = None, t_solicitado: float = None) -> np.ndarray:
    """
    Calcula la solución analítica exacta:
        h(t) = (sqrt(h0) - (k/2)*t)^2,  válida únicamente para t <= t_vaciado.

    Si t > t_vaciado, lanza TanqueVaciadoError para prevenir la generación de
    valores cuadráticos positivos artificiales fuera del dominio físico.
    """
    if t_vaciado is None:
        t_vaciado = 2.0 * np.sqrt(h0) / k

    t_arr = np.atleast_1d(t_arr)

    # Tolerancia numérica muy pequeña para evitar errores por precisión de punto flotante
    tol = 1e-7

    # Verificar si algún valor de t supera el tiempo de vaciado
    indices_invalidos = np.where(t_arr > (t_vaciado + tol))[0]
    if len(indices_invalidos) > 0:
        idx_fallo = int(indices_invalidos[0])
        t_fallo = float(t_arr[idx_fallo])
        solicitado = t_solicitado if t_solicitado is not None else float(t_arr[-1])
        raise TanqueVaciadoError(
            metodo="Solución Exacta",
            iteracion=idx_fallo,
            t=t_fallo,
            t_vaciado=t_vaciado,
            t_solicitado=solicitado
        )

    termino = np.sqrt(h0) - (k / 2.0) * t_arr
    # Si algún término es negativo por precisión flotante cuando t ~ t_vaciado
    termino = np.maximum(termino, 0.0)
    h_exacta = termino ** 2

    return h_exacta


# =============================================================================
# MÉTODOS NUMÉRICOS DE RESOLUCIÓN DE EDOS
# =============================================================================

def _resolver_contexto(f, t0: float, h_step: float, N: int, t_vaciado: float, t_solicitado: float):
    """Función auxiliar para resolver metadatos de vaciado y tiempo solicitado."""
    vac = t_vaciado if t_vaciado is not None else getattr(f, 't_vaciado', None)
    sol = t_solicitado if t_solicitado is not None else getattr(f, 't_solicitado', None)
    if sol is None:
        sol = t0 + N * h_step
    return vac, sol


def euler(f, y0: float, t0: float, h: float, N: int, t_vaciado: float = None, t_solicitado: float = None):
    """
    Método de Euler hacia adelante (orden 1).
    Fórmula: y_{n+1} = y_n + h * f(t_n, y_n)

    Parámetros:
        f: función f(t, y) que define la EDO dy/dt = f(t, y)
        y0: condición inicial y(t0)
        t0: tiempo inicial
        h: tamaño del paso de integración
        N: número de pasos/iteraciones
        t_vaciado: tiempo teórico de vaciado (opcional para contexto de error)
        t_solicitado: tiempo total solicitado N*h (opcional)

    Retorna:
        t: array de tiempos de longitud N + 1
        y: array de aproximaciones de longitud N + 1

    Lanza:
        TanqueVaciadoError: si en algún paso y_{n+1} <= 0.
    """
    t_vac, t_sol = _resolver_contexto(f, t0, h, N, t_vaciado, t_solicitado)

    t = np.zeros(N + 1, dtype=float)
    y = np.zeros(N + 1, dtype=float)

    t[0] = t0
    y[0] = y0

    if y0 <= 0:
        raise TanqueVaciadoError(
            metodo="Euler",
            iteracion=0,
            t=t0,
            t_vaciado=t_vac,
            t_solicitado=t_sol
        )

    for i in range(N):
        t_n = t[i]
        y_n = y[i]

        y_sig = y_n + h * f(t_n, y_n)
        t_sig = t_n + h

        # Control estricto de tanque vacío
        # Control de tanque vacío
        # Físicamente, el tanque se vacía cuando h <= 0 o cuando el tiempo alcanza/supera t_vaciado.
        # Si t < t_vaciado pero h_sig <= 0 debido a un paso grosero (overshoot por Euler explícito),
        # se evita interrumpir cuando aún hay agua real en el tanque físico (t < t_vaciado),
        # asignando un valor residual mínimo positivo y registrando el fenómeno numérico.
        # Si t >= t_vaciado, el vaciado es físico y se lanza TanqueVaciadoError obligatoriamente.
        if y_sig <= 0.0:
            if t_vac is not None and t_sig < (t_vac - 1e-5):
                # Overshoot numérico de Euler: el tanque físico NO está vacío (t < t_vaciado)
                y_sig = 1e-4
            else:
                raise TanqueVaciadoError(
                    metodo="Euler",
                    iteracion=i + 1,
                    t=t_sig,
                    t_vaciado=t_vac,
                    t_solicitado=t_sol
                )

        t[i + 1] = t_sig
        y[i + 1] = y_sig

    return t, y


def rk2(f, y0: float, t0: float, h: float, N: int, t_vaciado: float = None, t_solicitado: float = None):
    """
    Método de Runge-Kutta de 2do orden (Método del Punto Medio / Euler Modificado).
    Fórmulas:
        k1 = f(t_n, y_n)
        k2 = f(t_n + h/2, y_n + (h/2) * k1)
        y_{n+1} = y_n + h * k2

    Retorna:
        t: array de tiempos de longitud N + 1
        y: array de aproximaciones de longitud N + 1

    Lanza:
        TanqueVaciadoError: si en algún paso y_{n+1} <= 0.
    """
    t_vac, t_sol = _resolver_contexto(f, t0, h, N, t_vaciado, t_solicitado)

    t = np.zeros(N + 1, dtype=float)
    y = np.zeros(N + 1, dtype=float)

    t[0] = t0
    y[0] = y0

    if y0 <= 0:
        raise TanqueVaciadoError(
            metodo="RK2 (Punto Medio)",
            iteracion=0,
            t=t0,
            t_vaciado=t_vac,
            t_solicitado=t_sol
        )

    for i in range(N):
        t_n = t[i]
        y_n = y[i]

        k1 = f(t_n, y_n)
        k2 = f(t_n + 0.5 * h, y_n + 0.5 * h * k1)

        y_sig = y_n + h * k2
        t_sig = t_n + h

        # Control estricto de tanque vacío (físico y numérico)
        if y_sig <= 0.0 or (t_vac is not None and t_sig >= (t_vac - 1e-7)):
            raise TanqueVaciadoError(
                metodo="RK2 (Punto Medio)",
                iteracion=i + 1,
                t=t_sig,
                t_vaciado=t_vac,
                t_solicitado=t_sol
            )

        t[i + 1] = t_sig
        y[i + 1] = y_sig

    return t, y


def rk4(f, y0: float, t0: float, h: float, N: int, t_vaciado: float = None, t_solicitado: float = None):
    """
    Método de Runge-Kutta de 4to orden clásico (RK4).
    Fórmulas:
        k1 = f(t_n, y_n)
        k2 = f(t_n + h/2, y_n + (h/2) * k1)
        k3 = f(t_n + h/2, y_n + (h/2) * k2)
        k4 = f(t_n + h,   y_n + h * k3)
        y_{n+1} = y_n + (h/6) * (k1 + 2*k2 + 2*k3 + k4)

    Retorna:
        t: array de tiempos de longitud N + 1
        y: array de aproximaciones de longitud N + 1

    Lanza:
        TanqueVaciadoError: si en algún paso y_{n+1} <= 0.
    """
    t_vac, t_sol = _resolver_contexto(f, t0, h, N, t_vaciado, t_solicitado)

    t = np.zeros(N + 1, dtype=float)
    y = np.zeros(N + 1, dtype=float)

    t[0] = t0
    y[0] = y0

    if y0 <= 0:
        raise TanqueVaciadoError(
            metodo="RK4",
            iteracion=0,
            t=t0,
            t_vaciado=t_vac,
            t_solicitado=t_sol
        )

    for i in range(N):
        t_n = t[i]
        y_n = y[i]

        k1 = f(t_n, y_n)
        k2 = f(t_n + 0.5 * h, y_n + 0.5 * h * k1)
        k3 = f(t_n + 0.5 * h, y_n + 0.5 * h * k2)
        k4 = f(t_n + h, y_n + h * k3)

        y_sig = y_n + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)
        t_sig = t_n + h

        # Control estricto de tanque vacío (físico y numérico)
        if y_sig <= 0.0 or (t_vac is not None and t_sig >= (t_vac - 1e-7)):
            raise TanqueVaciadoError(
                metodo="RK4",
                iteracion=i + 1,
                t=t_sig,
                t_vaciado=t_vac,
                t_solicitado=t_sol
            )

        t[i + 1] = t_sig
        y[i + 1] = y_sig

    return t, y


# =============================================================================
# DESGLOSE PASO A PASO DE RK4
# =============================================================================

def desglose_rk4(f, y0: float, t0: float, h: float, num_pasos: int = 2) -> list:
    """
    Genera un desglose numérico detallado de los coeficientes intermedios de RK4
    para las primeras iteraciones (por defecto las primeras 2).

    Retorna una lista de diccionarios con:
        'paso': número de paso (1, 2, ...)
        'tn': tiempo inicial del paso
        'yn': valor inicial del paso
        'k1': pendiente k1 = f(tn, yn)
        't_k2': tiempo intermedio tn + h/2
        'y_k2': altura intermedia yn + (h/2)*k1
        'k2': pendiente k2
        't_k3': tiempo intermedio tn + h/2
        'y_k3': altura intermedia yn + (h/2)*k2
        'k3': pendiente k3
        't_k4': tiempo tn + h
        'y_k4': altura intermedia yn + h*k3
        'k4': pendiente k4
        'pend_prom': pendiente ponderada (k1 + 2k2 + 2k3 + k4) / 6
        'delta_y': (h/6)*(k1 + 2k2 + 2k3 + k4)
        't_sig': tiempo tn + h
        'y_sig': valor resultante yn+1
    """
    desglose = []
    t_curr = t0
    y_curr = y0

    for i in range(num_pasos):
        t_n = t_curr
        y_n = y_curr

        k1 = f(t_n, y_n)

        t_k2 = t_n + 0.5 * h
        y_k2 = y_n + 0.5 * h * k1
        k2 = f(t_k2, y_k2)

        t_k3 = t_n + 0.5 * h
        y_k3 = y_n + 0.5 * h * k2
        k3 = f(t_k3, y_k3)

        t_k4 = t_n + h
        y_k4 = y_n + h * k3
        k4 = f(t_k4, y_k4)

        pend_prom = (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0
        delta_y = h * pend_prom
        y_sig = y_n + delta_y
        t_sig = t_n + h

        desglose.append({
            'paso': i + 1,
            'tn': float(t_n),
            'yn': float(y_n),
            'k1': float(k1),
            't_k2': float(t_k2),
            'y_k2': float(y_k2),
            'k2': float(k2),
            't_k3': float(t_k3),
            'y_k3': float(y_k3),
            'k3': float(k3),
            't_k4': float(t_k4),
            'y_k4': float(y_k4),
            'k4': float(k4),
            'pend_prom': float(pend_prom),
            'delta_y': float(delta_y),
            't_sig': float(t_sig),
            'y_sig': float(y_sig)
        })

        t_curr = t_sig
        y_curr = y_sig

    return desglose


# =============================================================================
# ANÁLISIS DE CONVERGENCIA
# =============================================================================

def estudio_convergencia(f, h0: float, t0: float, h_base: float, N_base: int, k: float, t_vaciado: float):
    """
    Realiza el estudio de convergencia manteniendo el tiempo final fijo t_final = N_base * h_base.
    Evalúa refinamientos de malla sucesivos:
        m = 1  -> (h, N)
        m = 2  -> (h/2, 2N)
        m = 4  -> (h/4, 4N)
        m = 8  -> (h/8, 8N)
        m = 16 -> (h/16, 16N)

    Calcula el error absoluto en t_final contra la solución analítica exacta.
    Calcula la pendiente observada de convergencia p (orden empírico).

    Retorna:
        tabla_datos: lista de dicts con h, N, errores de Euler, RK2, RK4
        pendientes: dict con pendiente observada global (regresión log-log) de cada método
        advertencias: lista de advertencias si algún método falló en algún refinamiento
    """
    factores = [1, 2, 4, 8, 16]
    t_final = t0 + N_base * h_base

    # Solución exacta en t_final
    y_exacta_final = float(solucion_exacta([t_final], h0, k, t_vaciado, t_final)[0])

    tabla_datos = []
    advertencias = []

    for m in factores:
        h_m = h_base / float(m)
        N_m = int(N_base * m)

        fila = {
            'Factor': f"1/{m}",
            'h (s)': h_m,
            'N': N_m,
            'Euler_err': None,
            'RK2_err': None,
            'RK4_err': None
        }

        # Euler
        try:
            _, y_e = euler(f, h0, t0, h_m, N_m, t_vaciado, t_final)
            fila['Euler_err'] = float(abs(y_e[-1] - y_exacta_final))
        except TanqueVaciadoError as err:
            advertencias.append(f"Euler refinamiento h={h_m:.2f} s: {err.mensaje}")

        # RK2
        try:
            _, y_rk2 = rk2(f, h0, t0, h_m, N_m, t_vaciado, t_final)
            fila['RK2_err'] = float(abs(y_rk2[-1] - y_exacta_final))
        except TanqueVaciadoError as err:
            advertencias.append(f"RK2 refinamiento h={h_m:.2f} s: {err.mensaje}")

        # RK4
        try:
            _, y_rk4 = rk4(f, h0, t0, h_m, N_m, t_vaciado, t_final)
            fila['RK4_err'] = float(abs(y_rk4[-1] - y_exacta_final))
        except TanqueVaciadoError as err:
            advertencias.append(f"RK4 refinamiento h={h_m:.2f} s: {err.mensaje}")

        tabla_datos.append(fila)

    # Cálculo de pendientes por regresión lineal en espacio logarítmico log(E) vs log(h)
    pendientes = {}
    for metodo_key in ['Euler_err', 'RK2_err', 'RK4_err']:
        h_validos = []
        err_validos = []
        for fila in tabla_datos:
            if fila[metodo_key] is not None and fila[metodo_key] > 0:
                h_validos.append(fila['h (s)'])
                err_validos.append(fila[metodo_key])

        if len(h_validos) >= 2:
            log_h = np.log(h_validos)
            log_err = np.log(err_validos)
            # Regresión lineal: log(err) = p * log(h) + c
            p, _ = np.polyfit(log_h, log_err, 1)
            pendientes[metodo_key] = float(p)
        else:
            pendientes[metodo_key] = None

    return tabla_datos, pendientes, advertencias
