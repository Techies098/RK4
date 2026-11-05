"""
simulacion_widget.py - Generador del componente interactivo de simulación dinámica
Tanque Cilíndrico con Ley de Torricelli y gráfica sincronizada en tiempo real.
Diseño robusto, auto-iniciable y con controles siempre visibles.
"""
import json

def generar_html_simulador(D, h0, d, Cd, g, k, t_vaciado, t_final, t_rk4, y_rk4, t_euler=None, y_euler=None):
    """
    Retorna un string HTML/JS auto-contenido con Canvas interactivo,
    animación con requestAnimationFrame, controles de velocidad prominentes (1x, 5x, 20x, 50x, 100x),
    barra de progreso temporal, gráfica sincronizada h(t), y controles de Play/Pausa/Reinicio.
    """
    # Muestreo fino de la solución analítica para graficar
    puntos_grafica = []
    pasos_curva = 100
    for i in range(pasos_curva + 1):
        t_i = (t_final * i) / pasos_curva
        if t_i <= t_vaciado:
            term = max(0.0, (h0**0.5) - (k / 2.0) * t_i)
            h_i = term ** 2
        else:
            h_i = 0.0
        puntos_grafica.append({"t": round(t_i, 2), "h": round(h_i, 4)})

    # Puntos calculados con RK4 para sobreponer en la gráfica
    puntos_rk4 = []
    if t_rk4 is not None and y_rk4 is not None:
        for t_val, y_val in zip(t_rk4, y_rk4):
            puntos_rk4.append({"t": round(float(t_val), 2), "h": round(float(y_val), 4)})

    datos_json = json.dumps({
        "D": float(D),
        "h0": float(h0),
        "d": float(d),
        "Cd": float(Cd),
        "g": float(g),
        "k": float(k),
        "t_vaciado": float(t_vaciado),
        "t_final": float(t_final),
        "curva_exacta": puntos_grafica,
        "puntos_rk4": puntos_rk4
    })

    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <style>
            * {{
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            }}
            body {{
                margin: 0;
                padding: 12px;
                background: #FFFFFF;
                color: #1F2937;
            }}
            .sim-container {{
                background: #F8FAFC;
                border: 2px solid #E2E8F0;
                border-radius: 14px;
                padding: 16px;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }}

            /* --- BARRA DE CONTROL PRINCIPAL ARRIBA --- */
            .control-panel-top {{
                background: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 10px;
                padding: 14px 18px;
                margin-bottom: 14px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.03);
            }}
            .control-row-1 {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 12px;
                margin-bottom: 12px;
            }}
            .btn-action {{
                padding: 10px 22px;
                font-size: 1.02rem;
                font-weight: 700;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                transition: all 0.15s ease;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }}
            .btn-play {{
                background: #2563EB;
                color: #FFFFFF;
                box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
            }}
            .btn-play:hover {{
                background: #1D4ED8;
            }}
            .btn-pause {{
                background: #D97706;
                color: #FFFFFF;
                box-shadow: 0 2px 4px rgba(217, 119, 6, 0.3);
            }}
            .btn-pause:hover {{
                background: #B45309;
            }}
            .btn-reset {{
                background: #F1F5F9;
                color: #334155;
                border: 1.5px solid #CBD5E1;
            }}
            .btn-reset:hover {{
                background: #E2E8F0;
            }}

            /* Selector de Velocidad Destacado */
            .speed-selector {{
                display: flex;
                align-items: center;
                gap: 6px;
                background: #F1F5F9;
                padding: 4px 8px;
                border-radius: 8px;
                border: 1px solid #CBD5E1;
            }}
            .speed-title {{
                font-size: 0.88rem;
                font-weight: 700;
                color: #334155;
                margin-right: 4px;
                display: flex;
                align-items: center;
                gap: 4px;
            }}
            .btn-speed {{
                padding: 6px 12px;
                font-size: 0.85rem;
                font-weight: 700;
                border-radius: 6px;
                border: 1px solid transparent;
                background: #FFFFFF;
                color: #475569;
                cursor: pointer;
                transition: all 0.15s ease;
            }}
            .btn-speed:hover {{
                background: #E2E8F0;
                color: #0F172A;
            }}
            .btn-speed.active {{
                background: #1E3A8A;
                color: #FFFFFF;
                border-color: #1E3A8A;
                box-shadow: 0 2px 4px rgba(30, 58, 138, 0.25);
            }}

            /* Barra de Tiempo / Slider */
            .timeline-container {{
                width: 100%;
            }}
            .timeline-labels {{
                display: flex;
                justify-content: space-between;
                font-size: 0.8rem;
                font-weight: 600;
                color: #475569;
                margin-bottom: 4px;
            }}
            .slider-time {{
                width: 100%;
                height: 8px;
                border-radius: 5px;
                outline: none;
                cursor: pointer;
                accent-color: #2563EB;
            }}

            /* --- PANELES GRÁFICOS (TANQUE Y CURVA) --- */
            .sim-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
                margin-bottom: 12px;
            }}
            @media (max-width: 768px) {{
                .sim-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            .panel {{
                background: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
            }}
            .panel-header {{
                width: 100%;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 0.84rem;
                font-weight: 700;
                color: #1E3A8A;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                padding-bottom: 6px;
                border-bottom: 1px solid #F1F5F9;
            }}
            canvas {{
                max-width: 100%;
                height: auto;
                background: #FFFFFF;
            }}

            /* --- TIRA DE MÉTRICAS EN VIVO --- */
            .metrics-strip {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 10px;
                width: 100%;
            }}
            @media (max-width: 600px) {{
                .metrics-strip {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            .metric-card {{
                background: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-left: 4px solid #2563EB;
                border-radius: 8px;
                padding: 8px 12px;
                text-align: center;
            }}
            .metric-card .label {{
                font-size: 0.74rem;
                color: #64748B;
                font-weight: 700;
                text-transform: uppercase;
            }}
            .metric-card .value {{
                font-size: 1.18rem;
                font-weight: 800;
                color: #0F172A;
                margin-top: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="sim-container">
            <!-- PANEL SUPERIOR: CONTROLES DE REPRODUCCIÓN Y VELOCIDAD -->
            <div class="control-panel-top">
                <div class="control-row-1">
                    <div style="display: flex; gap: 8px; align-items: center;">
                        <button id="btnPlay" class="btn-action btn-play">▶ Iniciar Simulación</button>
                        <button id="btnReset" class="btn-action btn-reset">↺ Reiniciar</button>
                    </div>

                    <!-- SELECTOR DE VELOCIDAD -->
                    <div class="speed-selector">
                        <span class="speed-title">⚡ Velocidad:</span>
                        <button class="btn-speed" data-speed="1">1x</button>
                        <button class="btn-speed" data-speed="5">5x</button>
                        <button class="btn-speed active" data-speed="20">20x</button>
                        <button class="btn-speed" data-speed="50">50x</button>
                        <button class="btn-speed" data-speed="100">100x</button>
                    </div>
                </div>

                <!-- BARRA DE TIEMPO INTERACTIVA -->
                <div class="timeline-container">
                    <div class="timeline-labels">
                        <span>t = 0 s</span>
                        <span style="color: #2563EB;">Arrastra la barra para mover el tiempo libremente</span>
                        <span>t_final = <span id="lblTFinal">0</span> s</span>
                    </div>
                    <input type="range" id="timeSlider" class="slider-time" min="0" max="1000" value="0" step="1">
                </div>
            </div>

            <!-- GRILLA DE VISUALIZACIÓN: TANQUE Y GRÁFICA -->
            <div class="sim-grid">
                <!-- Panel Tanque -->
                <div class="panel">
                    <div class="panel-header">
                        <span>🛢️ Tanque Cilíndrico y Orificio</span>
                        <span style="color: #64748B; font-weight: normal; text-transform: none;">D={D:.2f}m, d={d*100:.1f}cm</span>
                    </div>
                    <canvas id="tankCanvas" width="380" height="290"></canvas>
                </div>

                <!-- Panel Gráfica -->
                <div class="panel">
                    <div class="panel-header">
                        <span>📈 Altura h(t) vs Tiempo (Torricelli / RK4)</span>
                        <span id="badgeEstado" style="color: #10B981; font-weight: 700; text-transform: none;">● En curso</span>
                    </div>
                    <canvas id="graphCanvas" width="380" height="290"></canvas>
                </div>
            </div>

            <!-- TIRA DE MÉTRICAS EN TIEMPO REAL -->
            <div class="metrics-strip">
                <div class="metric-card" style="border-left-color: #2563EB;">
                    <div class="label">Tiempo Transcurrido</div>
                    <div class="value" id="valTiempo">0.0 s</div>
                </div>
                <div class="metric-card" style="border-left-color: #0284C7;">
                    <div class="label">Nivel Actual h(t)</div>
                    <div class="value" id="valAltura">0.00 m</div>
                </div>
                <div class="metric-card" style="border-left-color: #D97706;">
                    <div class="label">Velocidad de Salida v</div>
                    <div class="value" id="valVelocidad">0.00 m/s</div>
                </div>
                <div class="metric-card" style="border-left-color: #059669;">
                    <div class="label">Vaciado Completado</div>
                    <div class="value" id="valPorcentaje">0.0%</div>
                </div>
            </div>
        </div>

        <script>
            // Datos del modelo matemático inyectados desde Python
            const SIM_DATA = {datos_json};

            const D = SIM_DATA.D;
            const h0 = SIM_DATA.h0;
            const d = SIM_DATA.d;
            const Cd = SIM_DATA.Cd;
            const g = SIM_DATA.g;
            const k = SIM_DATA.k;
            const t_vaciado = SIM_DATA.t_vaciado;
            const t_final = SIM_DATA.t_final;
            const curva = SIM_DATA.curva_exacta;
            const puntos_rk4 = SIM_DATA.puntos_rk4;

            // Elementos DOM
            const tankCanvas = document.getElementById('tankCanvas');
            const tankCtx = tankCanvas.getContext('2d');
            const graphCanvas = document.getElementById('graphCanvas');
            const graphCtx = graphCanvas.getContext('2d');

            const btnPlay = document.getElementById('btnPlay');
            const btnReset = document.getElementById('btnReset');
            const timeSlider = document.getElementById('timeSlider');
            const speedButtons = document.querySelectorAll('.btn-speed');

            const valTiempo = document.getElementById('valTiempo');
            const valAltura = document.getElementById('valAltura');
            const valVelocidad = document.getElementById('valVelocidad');
            const valPorcentaje = document.getElementById('valPorcentaje');
            const lblTFinal = document.getElementById('lblTFinal');
            const badgeEstado = document.getElementById('badgeEstado');

            lblTFinal.innerText = t_final.toFixed(0);

            // Variables de estado
            let isPlaying = false;
            let currentTime = 0.0;
            let speedMultiplier = 20.0; // 20x por defecto
            let lastTimestamp = null;
            let waveOffset = 0;

            // Cálculo analítico exacto h(t)
            function getAltura(t) {{
                if (t >= t_vaciado) return 0.0;
                const term = Math.max(0.0, Math.sqrt(h0) - (k / 2.0) * t);
                return term * term;
            }}

            // Velocidad de salida por el orificio v = sqrt(2gh)
            function getVelocidad(h) {{
                if (h <= 0.0001) return 0.0;
                return Math.sqrt(2 * g * h);
            }}

            // Manejo de botones de velocidad
            speedButtons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    speedButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    speedMultiplier = parseFloat(btn.dataset.speed);
                }});
            }});

            // Controles Play / Pausa / Reset
            btnPlay.addEventListener('click', () => {{
                if (isPlaying) {{
                    pausar();
                }} else {{
                    iniciar();
                }}
            }});

            btnReset.addEventListener('click', () => {{
                pausar();
                currentTime = 0.0;
                timeSlider.value = 0;
                btnPlay.innerText = "▶ Iniciar Simulación";
                btnPlay.className = "btn-action btn-play";
                badgeEstado.innerText = "● Listo";
                badgeEstado.style.color = "#2563EB";
                actualizarVista();
            }});

            // Slider de tiempo interactivo
            timeSlider.addEventListener('input', (e) => {{
                const frac = parseFloat(e.target.value) / 1000.0;
                currentTime = frac * t_final;
                actualizarVista();
            }});

            function iniciar() {{
                if (currentTime >= t_final) {{
                    currentTime = 0.0;
                }}
                isPlaying = true;
                btnPlay.innerText = "⏸ Pausar";
                btnPlay.className = "btn-action btn-pause";
                badgeEstado.innerText = "● En curso (" + speedMultiplier + "x)";
                badgeEstado.style.color = "#10B981";
                lastTimestamp = performance.now();
                requestAnimationFrame(animar);
            }}

            function pausar() {{
                isPlaying = false;
                btnPlay.innerText = "▶ Reanudar";
                btnPlay.className = "btn-action btn-play";
                badgeEstado.innerText = "⏸ Pausado";
                badgeEstado.style.color = "#D97706";
                lastTimestamp = null;
            }}

            function animar(timestamp) {{
                if (!isPlaying) return;

                if (lastTimestamp === null) {{
                    lastTimestamp = timestamp;
                }}
                const dtRealSec = (timestamp - lastTimestamp) / 1000.0;
                lastTimestamp = timestamp;

                currentTime += dtRealSec * speedMultiplier;
                waveOffset += dtRealSec * 4.0;

                if (currentTime >= t_final) {{
                    currentTime = t_final;
                    timeSlider.value = 1000;
                    actualizarVista();
                    pausar();
                    btnPlay.innerText = "↺ Repetir";
                    badgeEstado.innerText = "✓ Finalizado";
                    badgeEstado.style.color = "#64748B";
                    return;
                }}

                timeSlider.value = Math.round((currentTime / t_final) * 1000);
                actualizarVista();
                requestAnimationFrame(animar);
            }}

            function actualizarVista() {{
                const h = getAltura(currentTime);
                const v = getVelocidad(h);
                const pct = Math.min(100, Math.max(0, ((h0 - h) / h0) * 100.0));

                valTiempo.innerText = currentTime.toFixed(1) + " s";
                valAltura.innerText = h.toFixed(3) + " m";
                valVelocidad.innerText = v.toFixed(2) + " m/s";
                valPorcentaje.innerText = pct.toFixed(1) + "%";

                dibujarTanque(h, v);
                dibujarGrafica(currentTime, h);
            }}

            // -----------------------------------------------------------------
            // DIBUJO DEL TANQUE CILÍNDRICO EN CANVAS
            // -----------------------------------------------------------------
            function dibujarTanque(h, v) {{
                const W = tankCanvas.width;
                const H = tankCanvas.height;
                tankCtx.clearRect(0, 0, W, H);

                const marginX = 65;
                const tankW = W - 2 * marginX;
                const tankTopY = 32;
                const tankBottomY = 220;
                const tankH = tankBottomY - tankTopY;
                const centerX = W / 2;
                const orificioW = 26;

                const fracH = Math.max(0, Math.min(1, h / h0));
                const waterTopY = tankBottomY - fracH * (tankH * 0.88);

                // Fondo interior del tanque
                tankCtx.fillStyle = '#F8FAFC';
                tankCtx.fillRect(marginX, tankTopY, tankW, tankH);

                // Agua dentro del tanque
                if (fracH > 0.001) {{
                    const grad = tankCtx.createLinearGradient(0, waterTopY, 0, tankBottomY);
                    grad.addColorStop(0, '#60A5FA');
                    grad.addColorStop(1, '#1E40AF');

                    tankCtx.fillStyle = grad;
                    tankCtx.beginPath();
                    tankCtx.moveTo(marginX + 3, tankBottomY);
                    tankCtx.lineTo(marginX + 3, waterTopY);

                    // Onda suave en la superficie
                    const steps = 30;
                    for (let i = 0; i <= steps; i++) {{
                        const x = marginX + 3 + (i / steps) * (tankW - 6);
                        const y = waterTopY + Math.sin(i * 0.7 + waveOffset) * (v > 0.05 ? 2.5 : 0.8);
                        tankCtx.lineTo(x, y);
                    }}
                    tankCtx.lineTo(marginX + tankW - 3, tankBottomY);
                    tankCtx.closePath();
                    tankCtx.fill();

                    // Brillo reflejo
                    tankCtx.fillStyle = 'rgba(255, 255, 255, 0.25)';
                    tankCtx.fillRect(marginX + 10, waterTopY + 4, 14, tankBottomY - waterTopY - 8);
                }}

                // Paredes sólidas
                tankCtx.lineWidth = 4;
                tankCtx.strokeStyle = '#334155';
                tankCtx.lineCap = 'round';

                // Pared izquierda y derecha
                tankCtx.beginPath();
                tankCtx.moveTo(marginX, tankTopY - 6);
                tankCtx.lineTo(marginX, tankBottomY);
                tankCtx.moveTo(marginX + tankW, tankTopY - 6);
                tankCtx.lineTo(marginX + tankW, tankBottomY);
                tankCtx.stroke();

                // Fondo con apertura
                tankCtx.beginPath();
                tankCtx.moveTo(marginX - 2, tankBottomY);
                tankCtx.lineTo(centerX - orificioW / 2, tankBottomY);
                tankCtx.moveTo(centerX + orificioW / 2, tankBottomY);
                tankCtx.lineTo(marginX + tankW + 2, tankBottomY);
                tankCtx.stroke();

                // Boquilla del orificio
                tankCtx.lineWidth = 3;
                tankCtx.strokeStyle = '#1E3A8A';
                tankCtx.beginPath();
                tankCtx.moveTo(centerX - orificioW / 2, tankBottomY);
                tankCtx.lineTo(centerX - orificioW / 2, tankBottomY + 10);
                tankCtx.moveTo(centerX + orificioW / 2, tankBottomY);
                tankCtx.lineTo(centerX + orificioW / 2, tankBottomY + 10);
                tankCtx.stroke();

                // Chorro de agua saliente
                if (h > 0.005) {{
                    const jetW = Math.max(4, orificioW * 0.75 * (h / h0));
                    const jetGrad = tankCtx.createLinearGradient(0, tankBottomY, 0, H);
                    jetGrad.addColorStop(0, '#3B82F6');
                    jetGrad.addColorStop(1, 'rgba(147, 197, 253, 0.1)');

                    tankCtx.fillStyle = jetGrad;
                    tankCtx.beginPath();
                    tankCtx.moveTo(centerX - jetW / 2, tankBottomY + 10);
                    tankCtx.lineTo(centerX + jetW / 2, tankBottomY + 10);
                    tankCtx.lineTo(centerX + jetW * 0.35, H - 4);
                    tankCtx.lineTo(centerX - jetW * 0.35, H - 4);
                    tankCtx.closePath();
                    tankCtx.fill();

                    // Gotitas dinámicas
                    const dropOff = (currentTime * 12) % 20;
                    tankCtx.fillStyle = '#60A5FA';
                    tankCtx.beginPath();
                    tankCtx.arc(centerX - 4, tankBottomY + 22 + dropOff, 2, 0, Math.PI * 2);
                    tankCtx.arc(centerX + 5, tankBottomY + 34 + (dropOff * 1.3) % 20, 2.5, 0, Math.PI * 2);
                    tankCtx.fill();
                }}

                // Cotas técnicas
                dibujarFlecha(tankCtx, marginX, tankTopY - 14, marginX + tankW, tankTopY - 14, '#DC2626');
                tankCtx.fillStyle = '#DC2626';
                tankCtx.font = 'bold 11px sans-serif';
                tankCtx.textAlign = 'center';
                tankCtx.fillText('D = ' + D.toFixed(2) + ' m', centerX, tankTopY - 20);

                if (h > 0.05) {{
                    const xCota = marginX - 18;
                    dibujarFlecha(tankCtx, xCota, tankBottomY, xCota, waterTopY, '#2563EB');
                    tankCtx.fillStyle = '#2563EB';
                    tankCtx.font = 'bold 11px sans-serif';
                    tankCtx.textAlign = 'right';
                    tankCtx.fillText('h = ' + h.toFixed(2) + 'm', xCota - 4, (tankBottomY + waterTopY) / 2 + 4);
                }}

                tankCtx.fillStyle = '#1E3A8A';
                tankCtx.font = '10px sans-serif';
                tankCtx.textAlign = 'center';
                tankCtx.fillText('Orificio d = ' + (d * 100).toFixed(1) + ' cm', centerX, tankBottomY + 26);
            }}

            function dibujarFlecha(ctx, x1, y1, x2, y2, color) {{
                ctx.strokeStyle = color;
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();

                ctx.fillStyle = color;
                const head = 4;
                if (y1 === y2) {{
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x1 + head, y1 - head);
                    ctx.lineTo(x1 + head, y1 + head);
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(x2 - head, y2 - head);
                    ctx.lineTo(x2 - head, y2 + head);
                    ctx.fill();
                }} else {{
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x1 - head, y1 - head);
                    ctx.lineTo(x1 + head, y1 - head);
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(x2 - head, y2 + head);
                    ctx.lineTo(x2 + head, y2 + head);
                    ctx.fill();
                }}
            }}

            // -----------------------------------------------------------------
            // DIBUJO DE LA GRÁFICA DINÁMICA h(t) EN CANVAS
            // -----------------------------------------------------------------
            function dibujarGrafica(tActual, hActual) {{
                const W = graphCanvas.width;
                const H = graphCanvas.height;
                graphCtx.clearRect(0, 0, W, H);

                const pL = 50, pR = 25, pT = 24, pB = 38;
                const plotW = W - pL - pR;
                const plotH = H - pT - pB;

                function mapX(t) {{ return pL + (t / t_final) * plotW; }}
                function mapY(valH) {{ return pT + plotH - (valH / h0) * plotH; }}

                // Rejilla
                graphCtx.strokeStyle = '#E2E8F0';
                graphCtx.lineWidth = 1;
                for (let i = 0; i <= 4; i++) {{
                    const y = pT + (i / 4) * plotH;
                    graphCtx.beginPath();
                    graphCtx.moveTo(pL, y);
                    graphCtx.lineTo(pL + plotW, y);
                    graphCtx.stroke();

                    const x = pL + (i / 4) * plotW;
                    graphCtx.beginPath();
                    graphCtx.moveTo(x, pT);
                    graphCtx.lineTo(x, pT + plotH);
                    graphCtx.stroke();
                }}

                // Ejes
                graphCtx.strokeStyle = '#94A3B8';
                graphCtx.lineWidth = 1.5;
                graphCtx.beginPath();
                graphCtx.moveTo(pL, pT);
                graphCtx.lineTo(pL, pT + plotH);
                graphCtx.lineTo(pL + plotW, pT + plotH);
                graphCtx.stroke();

                // Textos ejes
                graphCtx.fillStyle = '#64748B';
                graphCtx.font = '10px sans-serif';
                graphCtx.textAlign = 'right';
                graphCtx.fillText('0', pL - 6, pT + plotH + 3);
                graphCtx.fillText((h0 / 2).toFixed(2) + 'm', pL - 6, pT + plotH / 2 + 3);
                graphCtx.fillText(h0.toFixed(2) + 'm', pL - 6, pT + 4);

                graphCtx.textAlign = 'center';
                graphCtx.fillText('0', pL, pT + plotH + 16);
                graphCtx.fillText((t_final / 2).toFixed(0) + 's', pL + plotW / 2, pT + plotH + 16);
                graphCtx.fillText(t_final.toFixed(0) + 's', pL + plotW, pT + plotH + 16);

                graphCtx.fillStyle = '#334155';
                graphCtx.font = 'bold 10px sans-serif';
                graphCtx.fillText('Tiempo t [s]', pL + plotW / 2, H - 4);

                // 1. Curva teórica completa punteada gris
                graphCtx.strokeStyle = '#CBD5E1';
                graphCtx.lineWidth = 1.5;
                graphCtx.setLineDash([3, 3]);
                graphCtx.beginPath();
                curva.forEach((pt, idx) => {{
                    const x = mapX(pt.t);
                    const y = mapY(pt.h);
                    if (idx === 0) graphCtx.moveTo(x, y);
                    else graphCtx.lineTo(x, y);
                }});
                graphCtx.stroke();
                graphCtx.setLineDash([]);

                // 2. Trayectoria recorrida hasta el momento actual en azul
                graphCtx.strokeStyle = '#2563EB';
                graphCtx.lineWidth = 2.5;
                graphCtx.beginPath();
                let started = false;
                for (let i = 0; i < curva.length; i++) {{
                    const pt = curva[i];
                    if (pt.t <= tActual) {{
                        const x = mapX(pt.t);
                        const y = mapY(pt.h);
                        if (!started) {{
                            graphCtx.moveTo(x, y);
                            started = true;
                        }} else {{
                            graphCtx.lineTo(x, y);
                        }}
                    }} else {{
                        const xNow = mapX(tActual);
                        const yNow = mapY(hActual);
                        if (started) graphCtx.lineTo(xNow, yNow);
                        break;
                    }}
                }}
                graphCtx.stroke();

                // 3. Puntos calculados de RK4 alcanzados
                if (puntos_rk4) {{
                    puntos_rk4.forEach(pt => {{
                        if (pt.t <= tActual) {{
                            const px = mapX(pt.t);
                            const py = mapY(pt.h);
                            graphCtx.fillStyle = '#1E3A8A';
                            graphCtx.beginPath();
                            graphCtx.arc(px, py, 3.5, 0, Math.PI * 2);
                            graphCtx.fill();
                        }}
                    }});
                }}

                // 4. Cursor del momento actual (Punto rojo pulsante)
                const curX = mapX(tActual);
                const curY = mapY(hActual);

                graphCtx.strokeStyle = '#EF4444';
                graphCtx.lineWidth = 1;
                graphCtx.setLineDash([2, 2]);
                graphCtx.beginPath();
                graphCtx.moveTo(curX, pT);
                graphCtx.lineTo(curX, pT + plotH);
                graphCtx.stroke();
                graphCtx.setLineDash([]);

                graphCtx.fillStyle = '#DC2626';
                graphCtx.beginPath();
                graphCtx.arc(curX, curY, 6, 0, Math.PI * 2);
                graphCtx.fill();
                graphCtx.strokeStyle = '#FFFFFF';
                graphCtx.lineWidth = 2;
                graphCtx.stroke();

                graphCtx.fillStyle = '#0F172A';
                graphCtx.font = 'bold 10px sans-serif';
                graphCtx.textAlign = 'left';
                const tagX = Math.min(plotW + pL - 50, curX + 8);
                const tagY = Math.max(pT + 12, curY - 8);
                graphCtx.fillText(hActual.toFixed(2) + ' m', tagX, tagY);
            }}

            // Dibujar estado inicial
            actualizarVista();

            // Auto-iniciar la simulación a los 500ms para que se mueva sola al cargar
            setTimeout(() => {{
                if (!isPlaying && currentTime === 0.0) {{
                    iniciar();
                }}
            }}, 500);
        </script>
    </body>
    </html>
    """
    return html_content
