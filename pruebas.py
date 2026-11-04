"""
pruebas.py - Suite de pruebas y validación del modelo de vaciado de tanque y métodos numéricos
---------------------------------------------------------------------------------------------
Prueba 1: D=2, h0=3, d=0.05, Cd=0.6, h=300, N=6:
          Verifica k ≈ 0.00166, t_vaciado ≈ 2086 s, t_final = 1800 s y pendientes de convergencia ~1, ~2 y ~4.
Prueba 2: D=2, h0=3, d=0.05, Cd=0.6, h=300, N=8 (2400 s > t_vaciado):
          Verifica que se lance TanqueVaciadoError y que el mensaje contenga el tiempo de vaciado total.
"""

import sys
import numpy as np

# Asegurar codificación UTF-8 en salida de terminal para Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

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


def ejecutar_pruebas():
    print("=" * 70)
    print("INICIANDO SUITE DE PRUEBAS DE MÉTODOS NUMÉRICOS (VACIADO DE TANQUE)")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # PRUEBA 1: Verificación de parámetros físicos y convergencia estándar
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Verificación con parámetros base: D=2, h0=3, d=0.05, Cd=0.6, h=300, N=6")
    D = 2.0
    h0 = 3.0
    d = 0.05
    Cd = 0.6
    h_step = 300.0
    N = 6
    g = 9.81

    params = calcular_parametros(D=D, h0=h0, d=d, Cd=Cd, g=g)
    k = params['k']
    t_vaciado = params['t_vaciado']
    t_final = N * h_step

    print(f"  -> k calculado: {k:.7f} (Esperado: ≈ 0.00166)")
    assert abs(k - 0.001661) < 1e-4, f"k fuera de rango esperado: {k}"

    print(f"  -> t_vaciado calculado: {t_vaciado:.2f} s ({params['t_vaciado_min']:.2f} min) (Esperado: ≈ 2086 s)")
    assert abs(t_vaciado - 2085.5) < 2.0, f"t_vaciado fuera de rango: {t_vaciado}"

    print(f"  -> t_final calculado: {t_final:.1f} s (Esperado: 1800 s)")
    assert t_final == 1800.0, f"t_final incorrecto: {t_final}"

    # EDO y Solución analítica exacta
    f = crear_edo_torricelli(k, t_vaciado=t_vaciado, t_solicitado=t_final)
    t_num = np.linspace(0, t_final, N + 1)
    h_exacta = solucion_exacta(t_num, h0, k, t_vaciado, t_final)

    assert len(h_exacta) == N + 1, "Longitud de solución exacta incorrecta"
    assert np.isclose(h_exacta[0], h0, atol=1e-12), f"Condición inicial incorrecta: {h_exacta[0]} != {h0}"
    assert h_exacta[-1] > 0, "La altura final exacta debería ser positiva a t=1800 s"
    print(f"  -> h_exacta(1800 s) = {h_exacta[-1]:.4f} m (h0 = {h0} m)")

    # Métodos numéricos
    t_e, y_e = euler(f, h0, 0.0, h_step, N, t_vaciado, t_final)
    t_r2, y_r2 = rk2(f, h0, 0.0, h_step, N, t_vaciado, t_final)
    t_r4, y_r4 = rk4(f, h0, 0.0, h_step, N, t_vaciado, t_final)

    assert len(y_e) == N + 1 and len(y_r2) == N + 1 and len(y_r4) == N + 1
    err_e = abs(y_e[-1] - h_exacta[-1])
    err_r2 = abs(y_r2[-1] - h_exacta[-1])
    err_r4 = abs(y_r4[-1] - h_exacta[-1])

    print(f"  -> Error en t_final (h=300): Euler = {err_e:.6f} m, RK2 = {err_r2:.6f} m, RK4 = {err_r4:.8f} m")
    assert err_r4 < err_r2 < err_e, "El orden de precisión debería ser RK4 < RK2 < Euler"

    # Desglose de RK4
    desglose = desglose_rk4(f, h0, 0.0, h_step, num_pasos=2)
    assert len(desglose) == 2, "El desglose de RK4 debe contener 2 pasos"
    print(f"  -> Desglose RK4 paso 1: k1={desglose[0]['k1']:.6f}, k2={desglose[0]['k2']:.6f}, "
          f"k3={desglose[0]['k3']:.6f}, k4={desglose[0]['k4']:.6f}, y1={desglose[0]['y_sig']:.4f} m")

    # Estudio de convergencia
    print("\n  -> Ejecutando estudio de convergencia con refinamientos h/2, h/4, h/8, h/16...")
    tabla_conv, pendientes, advertencias = estudio_convergencia(f, h0, 0.0, h_step, N, k, t_vaciado)
    p_euler = pendientes['Euler_err']
    p_rk2 = pendientes['RK2_err']
    p_rk4 = pendientes['RK4_err']

    print(f"  -> Pendiente observada Euler: {p_euler:.2f} (Esperable: ≈ 1.0)")
    print(f"  -> Pendiente observada RK2:   {p_rk2:.2f} (Esperable: ≈ 2.0)")
    print(f"  -> Pendiente observada RK4:   {p_rk4:.2f} (Esperable: ≈ 4.0)")

    assert abs(p_euler - 1.0) < 0.25, f"Pendiente de Euler no es cercana a 1: {p_euler}"
    assert abs(p_rk2 - 2.0) < 0.25, f"Pendiente de RK2 no es cercana a 2: {p_rk2}"
    assert abs(p_rk4 - 4.0) < 0.40, f"Pendiente de RK4 no es cercana a 4: {p_rk4}"
    print("  [OK] TEST 1 COMPLETADO EXITOSAMENTE.")

    # -------------------------------------------------------------------------
    # PRUEBA 2: Verificación de excepción TanqueVaciadoError con N=8 (t_final=2400 > t_vaciado)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verificación de TanqueVaciadoError: D=2, h0=3, d=0.05, Cd=0.6, h=300, N=8")
    N_over = 8
    t_final_over = N_over * h_step
    print(f"  -> t_final = {t_final_over} s > t_vaciado ({t_vaciado:.1f} s)")

    f_over = crear_edo_torricelli(k, t_vaciado=t_vaciado, t_solicitado=t_final_over)

    # Probar que Euler lanza TanqueVaciadoError
    lanzado_euler = False
    try:
        euler(f_over, h0, 0.0, h_step, N_over, t_vaciado, t_final_over)
    except TanqueVaciadoError as ex:
        lanzado_euler = True
        print(f"  -> Excepción capturada en Euler: '{ex}'")
        assert "vació" in str(ex)
        assert f"{t_vaciado:.0f}" in str(ex) or "2086" in str(ex)
        assert f"{t_final_over:.0f}" in str(ex) or "2400" in str(ex)
    assert lanzado_euler, "Euler no lanzó TanqueVaciadoError cuando t_final > t_vaciado"

    # Probar que RK2 lanza TanqueVaciadoError
    lanzado_rk2 = False
    try:
        rk2(f_over, h0, 0.0, h_step, N_over, t_vaciado, t_final_over)
    except TanqueVaciadoError as ex:
        lanzado_rk2 = True
        print(f"  -> Excepción capturada en RK2: '{ex}'")
        assert "vació" in str(ex)
        assert f"{t_vaciado:.0f}" in str(ex) or "2086" in str(ex)
    assert lanzado_rk2, "RK2 no lanzó TanqueVaciadoError cuando t_final > t_vaciado"

    # Probar que RK4 lanza TanqueVaciadoError
    lanzado_rk4 = False
    try:
        rk4(f_over, h0, 0.0, h_step, N_over, t_vaciado, t_final_over)
    except TanqueVaciadoError as ex:
        lanzado_rk4 = True
        print(f"  -> Excepción capturada en RK4: '{ex}'")
        assert "vació" in str(ex)
        assert f"{t_vaciado:.0f}" in str(ex) or "2086" in str(ex)
    assert lanzado_rk4, "RK4 no lanzó TanqueVaciadoError cuando t_final > t_vaciado"

    # Probar que la Solución Exacta lanza TanqueVaciadoError si se le pide evaluar más allá de t_vaciado
    lanzado_exacta = False
    try:
        t_eval = np.array([0.0, 1000.0, 2000.0, 2200.0])
        solucion_exacta(t_eval, h0, k, t_vaciado, t_final_over)
    except TanqueVaciadoError as ex:
        lanzado_exacta = True
        print(f"  -> Excepción capturada en Solución Exacta: '{ex}'")
        assert "Solución Exacta" in str(ex)
        assert f"{t_vaciado:.0f}" in str(ex) or "2086" in str(ex)
    assert lanzado_exacta, "Solución Exacta no lanzó TanqueVaciadoError para t > t_vaciado"

    print("  [OK] TEST 2 COMPLETADO EXITOSAMENTE.")

    print("\n" + "=" * 70)
    print("TODAS LAS PRUEBAS PASARON SATISFACTORIAMENTE (100% SUCCESS)")
    print("=" * 70)


if __name__ == "__main__":
    ejecutar_pruebas()
