"""
simulacion_widget.py - Generador del componente interactivo de simulación dinámica
Tanque Cilíndrico con Ley de Torricelli y gráfica sincronizada en tiempo real.
"""
import json

def generar_html_simulador(D, h0, d, Cd, g, k, t_vaciado, t_final, t_rk4, y_rk4, t_euler=None, y_euler=None):
    """
    Retorna un string HTML/JS auto-contenido con Canvas interactivo,
    animación con requestAnimationFrame, controles de velocidad (1x, 5x, 20x, 50x, 100x),
    barra de progreso temporal, gráfica sincronizada h(t), y controles de Play/Pausa/Reinicio.
    """
    # Muestreo fino de la solución analítica para graficar
    puntos_grafica = []
    pasos_curva = 100
    for i in range(pasos_curva + 1):
        t_i = (t_final * i) / pasos_curva
        # Solución exacta: h(t) = (sqrt(h0) - (k/2)*t)^2 si t <= t_vaciado, sino 0
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
                padding: 10px;
                background: #FFFFFF;
                color: #1F2937;
            }}
            .sim-container {{
                background: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 16px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }}
            .sim-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                flex-wrap: wrap;
                gap: 8px;
            }}
            .sim-title {{
                font-size: 1.05rem;
                font-weight: 700;
                color: #1E3A8A;
                display: flex;
                align-items: center;
                gap: 6px;
            }}
            .badge-live {{
                display: inline-block;
                width: 8px;
                height: 8px;
                background-color: #10B981;
                border-radius: 50%;
                animation: pulse 1.5s infinite;
            }}
            @keyframes pulse {{
                0% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.4; transform: scale(1.2); }}
                100% {{ opacity: 1; transform: scale(1); }}
            }}
            .sim-grid {{
                display: grid;
                grid-template-columns: 1.1fr 1fr;
                gap: 16px;
            }}
            @media (max-width: 768px) {{
                .sim-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            .panel {{
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                display: flex;
                flex-direction: column;
                align-items: center;
                position: relative;
            }}
            .panel-label {{
                font-size: 0.82rem;
                font-weight: 600;
                color: #4B5563;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 8px;
                align-self: flex-start;
            }}
            canvas {{
                max-width: 100%;
                background: #FFFFFF;
            }}
            .controls-bar {{
                margin-top: 14px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                background: #FFFFFF;
                padding: 12px 16px;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
            }}
            .controls-row {{
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 10px;
            }}
            .btn-group {{
                display: flex;
                gap: 6px;
                align-items: center;
            }}
            .btn {{
                background: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 0.88rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.15s ease;
                display: inline-flex;
                align-items: center;
                gap: 4px;
            }}
            .btn:hover {{
                background: #E5E7EB;
                color: #111827;
            }}
            .btn-primary {{
                background: #2563EB;
                color: white;
                border-color: #1D4ED8;
            }}
            .btn-primary:hover {{
                background: #1D4ED8;
                color: white;
            }}
            .speed-btn {{
                padding: 4px 8px;
                font-size: 0.8rem;
            }}
            .speed-btn.active {{
                background: #1E3A8A;
                color: #FFFFFF;
                border-color: #1E3A8A;
            }}
            .progress-container {{
                width: 100%;
                display: flex;
                flex-direction: column;
                gap: 4px;
            }}
            .slider-time {{
                width: 100%;
                cursor: pointer;
                accent-color: #2563EB;
            }}
            .metrics-strip {{
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 8px;
                width: 100%;
                margin-top: 8px;
            }}
            @media (max-width: 600px) {{
                .metrics-strip {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            .metric-box {{
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 6px 10px;
                text-align: center;
            }}
            .metric-box .label {{
                font-size: 0.72rem;
                color: #64748B;
                font-weight: 600;
                text-transform: uppercase;
            }}
            .metric-box .value {{
                font-size: 1.05rem;
                font-weight: 700;
                color: #1E293B;
                margin-top: 2px;
            }}
        </style>
    </head>
    <body>
        <div class="sim-container">
            <div class="sim-header">
                <div class="sim-title">
                    <span class="badge-live"></span>
                    Simulador Dinámico de Vaciado de Tanque (Ley de Torricelli)
                </div>
                <div style="font-size: 0.82rem; color: #4B5563;">
                    Física en tiempo real sincronizada con RK4
                </div>
            </div>

            <div class="sim-grid">
                <!-- Panel Izquierdo: Tanque Animado -->
                <div class="panel">
                    <div class="panel-label">Cilindro Hidráulico en Corte</div>
                    <canvas id="tankCanvas" width="360" height="300"></canvas>
                </div>

                <!-- Panel Derecho: Gráfica Dinámica h(t) -->
                <div class="panel">
                    <div class="panel-label">Curva de Vaciado h(t) vs Tiempo</div>
                    <canvas id="graphCanvas" width="380" height="300"></canvas>
                </div>
            </div>

            <!-- Tira de Métricas en Vivo -->
            <div class="metrics-strip">
                <div class="metric-box">
                    <div class="label">Tiempo Simulado</div>
                    <div class="value" id="valTiempo">0.0 s</div>
                </div>
                <div class="metric-box">
                    <div class="label">Altura Actual h(t)</div>
                    <div class="value" id="valAltura">0.00 m</div>
                </div>
                <div class="metric-box">
                    <div class="label">Velocidad Salida v</div>
                    <div class="value" id="valVelocidad">0.00 m/s</div>
                </div>
                <div class="metric-box">
                    <div class="label">Porcentaje Vaciado</div>
                    <div class="value" id="valPorcentaje">0.0%</div>
                </div>
            </div>

            <!-- Barra de Controles y Velocidad -->
            <div class="controls-bar">
                <div class="progress-container">
                    <div style="display: flex; justify-content: space-between; font-size: 0.78rem; color: #6B7280;">
                        <span>Inicio: t = 0 s</span>
                        <span id="labelBarraTiempo">Avance del tiempo (Arrastra para retroceder o avanzar)</span>
                        <span>Fin: <span id="labelTFinal">0 s</span></span>
                    </div>
                    <input type="range" id="timeSlider" class="slider-time" min="0" max="1000" value="0" step="1">
                </div>

                <div class="controls-row">
                    <div class="btn-group">
                        <button id="btnPlay" class="btn btn-primary">▶ Iniciar</button>
                        <button id="btnReset" class="btn">↺ Reiniciar</button>
                    </div>

                    <div class="btn-group">
                        <span style="font-size: 0.82rem; font-weight: 600; color: #4B5563; margin-right: 4px;">Velocidad:</span>
                        <button class="btn speed-btn" data-speed="1">1x</button>
                        <button class="btn speed-btn" data-speed="5">5x</button>
                        <button class="btn speed-btn active" data-speed="20">20x</button>
                        <button class="btn speed-btn" data-speed="50">50x</button>
                        <button class="btn speed-btn" data-speed="100">100x</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Datos inyectados desde Python
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
            const speedButtons = document.querySelectorAll('.speed-btn');

            const valTiempo = document.getElementById('valTiempo');
            const valAltura = document.getElementById('valAltura');
            const valVelocidad = document.getElementById('valVelocidad');
            const valPorcentaje = document.getElementById('valPorcentaje');
            const labelTFinal = document.getElementById('labelTFinal');

            labelTFinal.innerText = t_final.toFixed(0) + " s";

            // Estado de la animación
            let isPlaying = false;
            let currentTime = 0.0; // segundos
            let speedMultiplier = 20.0; // 20x por defecto
            let lastTimestamp = null;
            let waveOffset = 0;

            // Función analítica exacta h(t)
            function getAltura(t) {{
                if (t >= t_vaciado) return 0.0;
                const term = Math.max(0.0, Math.sqrt(h0) - (k / 2.0) * t);
                return term * term;
            }}

            // Velocidad de salida Torricelli v = sqrt(2gh)
            function getVelocidadSalida(h) {{
                if (h <= 0.0001) return 0.0;
                return Math.sqrt(2 * g * h);
            }}

            // Actualizar botones de velocidad
            speedButtons.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    speedButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    speedMultiplier = parseFloat(btn.dataset.speed);
                }});
            }});

            // Controles Play / Pausa / Reinicio
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
                actualizarVista();
            }});

            // Slider interactivo (arrastrar tiempo)
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
                btnPlay.classList.remove('btn-primary');
                btnPlay.style.background = "#D97706";
                btnPlay.style.color = "#FFFFFF";
                btnPlay.style.borderColor = "#B45309";
                lastTimestamp = performance.now();
                requestAnimationFrame(loopAnimacion);
            }}

            function pausar() {{
                isPlaying = false;
                btnPlay.innerText = "▶ Reanudar";
                btnPlay.classList.add('btn-primary');
                btnPlay.style.background = "";
                btnPlay.style.color = "";
                btnPlay.style.borderColor = "";
                lastTimestamp = null;
            }}

            // Bucle de animación
            function loopAnimacion(timestamp) {{
                if (!isPlaying) return;

                if (lastTimestamp === null) {{
                    lastTimestamp = timestamp;
                }}
                const dtRealSec = (timestamp - lastTimestamp) / 1000.0;
                lastTimestamp = timestamp;

                // Incrementar tiempo simulado escalado por la velocidad
                currentTime += dtRealSec * speedMultiplier;
                waveOffset += dtRealSec * 4.0;

                if (currentTime >= t_final) {{
                    currentTime = t_final;
                    timeSlider.value = 1000;
                    actualizarVista();
                    pausar();
                    btnPlay.innerText = "↺ Repetir";
                    return;
                }}

                timeSlider.value = Math.round((currentTime / t_final) * 1000);
                actualizarVista();
                requestAnimationFrame(loopAnimacion);
            }}

            // Actualización centralizada de toda la interfaz
            function actualizarVista() {{
                const h = getAltura(currentTime);
                const v = getVelocidadSalida(h);
                const pctVaciado = Math.min(100, Math.max(0, ((h0 - h) / h0) * 100.0));

                // Actualizar métricas textuales
                valTiempo.innerText = currentTime.toFixed(1) + " s";
                valAltura.innerText = h.toFixed(3) + " m";
                valVelocidad.innerText = v.toFixed(2) + " m/s";
                valPorcentaje.innerText = pctVaciado.toFixed(1) + "%";

                // Dibujar Canvas
                dibujarTanque(h, v);
                dibujarGrafica(currentTime, h);
            }}

            // -------------------------------------------------------------
            // DIBUJO DEL TANQUE EN CANVAS
            // -------------------------------------------------------------
            function dibujarTanque(h, v) {{
                const W = tankCanvas.width;
                const H = tankCanvas.height;
                tankCtx.clearRect(0, 0, W, H);

                // Dimensiones del tanque en pantalla
                const marginX = 60;
                const tankW = W - 2 * marginX; // ancho tanque
                const tankTopY = 35;
                const tankBottomY = 225;
                const tankH = tankBottomY - tankTopY; // altura gráfica del tanque
                const centerX = W / 2;
                const orificioW = 28;

                // Altura de agua proporcional a h0
                const fracH = Math.max(0, Math.min(1, h / h0));
                const waterTopY = tankBottomY - fracH * (tankH * 0.88);

                // 1. Fondo del tanque abierto arriba
                // Sombra suave del tanque
                tankCtx.fillStyle = '#F8FAFC';
                tankCtx.fillRect(marginX, tankTopY, tankW, tankH);

                // 2. Dibujar Agua con gradiente
                if (fracH > 0.001) {{
                    const grad = tankCtx.createLinearGradient(0, waterTopY, 0, tankBottomY);
                    grad.addColorStop(0, '#60A5FA');
                    grad.addColorStop(1, '#1E40AF');

                    tankCtx.fillStyle = grad;
                    tankCtx.beginPath();
                    tankCtx.moveTo(marginX + 3, tankBottomY);
                    tankCtx.lineTo(marginX + 3, waterTopY);

                    // Superficie ondulada sutil del agua
                    const waveAmp = (v > 0.05) ? 2.5 : 0.8;
                    const steps = 30;
                    for (let i = 0; i <= steps; i++) {{
                        const x = marginX + 3 + (i / steps) * (tankW - 6);
                        const y = waterTopY + Math.sin(i * 0.7 + waveOffset) * waveAmp;
                        tankCtx.lineTo(x, y);
                    }}
                    tankCtx.lineTo(marginX + tankW - 3, tankBottomY);
                    tankCtx.closePath();
                    tankCtx.fill();

                    // Reflejo blanco sutil
                    tankCtx.fillStyle = 'rgba(255, 255, 255, 0.25)';
                    tankCtx.fillRect(marginX + 10, waterTopY + 4, 15, tankBottomY - waterTopY - 8);
                }}

                // 3. Paredes sólidas del cilindro (Líneas gruesas)
                tankCtx.lineWidth = 4;
                tankCtx.strokeStyle = '#334155';
                tankCtx.lineCap = 'round';

                // Pared izquierda
                tankCtx.beginPath();
                tankCtx.moveTo(marginX, tankTopY - 6);
                tankCtx.lineTo(marginX, tankBottomY);
                tankCtx.stroke();

                // Pared derecha
                tankCtx.beginPath();
                tankCtx.moveTo(marginX + tankW, tankTopY - 6);
                tankCtx.lineTo(marginX + tankW, tankBottomY);
                tankCtx.stroke();

                // Fondo con apertura para orificio
                tankCtx.beginPath();
                tankCtx.moveTo(marginX - 2, tankBottomY);
                tankCtx.lineTo(centerX - orificioW / 2, tankBottomY);
                tankCtx.stroke();

                tankCtx.beginPath();
                tankCtx.moveTo(centerX + orificioW / 2, tankBottomY);
                tankCtx.lineTo(marginX + tankW + 2, tankBottomY);
                tankCtx.stroke();

                // Boquilla del orificio
                tankCtx.lineWidth = 3;
                tankCtx.strokeStyle = '#1E3A8A';
                tankCtx.beginPath();
                tankCtx.moveTo(centerX - orificioW / 2, tankBottomY);
                tankCtx.lineTo(centerX - orificioW / 2, tankBottomY + 12);
                tankCtx.moveTo(centerX + orificioW / 2, tankBottomY);
                tankCtx.lineTo(centerX + orificioW / 2, tankBottomY + 12);
                tankCtx.stroke();

                // 4. Chorro de agua saliente (si hay agua y velocidad)
                if (h > 0.005) {{
                    const jetW = Math.max(4, orificioW * 0.7 * (h / h0));
                    const jetGrad = tankCtx.createLinearGradient(0, tankBottomY, 0, H);
                    jetGrad.addColorStop(0, '#3B82F6');
                    jetGrad.addColorStop(1, 'rgba(147, 197, 253, 0.1)');

                    tankCtx.fillStyle = jetGrad;
                    tankCtx.beginPath();
                    tankCtx.moveTo(centerX - jetW / 2, tankBottomY + 12);
                    tankCtx.lineTo(centerX + jetW / 2, tankBottomY + 12);
                    tankCtx.lineTo(centerX + jetW * 0.35, H - 5);
                    tankCtx.lineTo(centerX - jetW * 0.35, H - 5);
                    tankCtx.closePath();
                    tankCtx.fill();

                    // Gotitas salpicando
                    const dropOffset = (currentTime * 10) % 20;
                    tankCtx.fillStyle = '#60A5FA';
                    tankCtx.beginPath();
                    tankCtx.arc(centerX - 4, tankBottomY + 25 + dropOffset, 2, 0, Math.PI * 2);
                    tankCtx.arc(centerX + 5, tankBottomY + 38 + (dropOffset * 1.2) % 20, 2.5, 0, Math.PI * 2);
                    tankCtx.fill();
                }}

                // 5. Cotas y flechas técnicas
                // Flecha D (diámetro)
                dibujarFlechaDoble(tankCtx, marginX, tankTopY - 14, marginX + tankW, tankTopY - 14, '#DC2626');
                tankCtx.fillStyle = '#DC2626';
                tankCtx.font = 'bold 11px sans-serif';
                tankCtx.textAlign = 'center';
                tankCtx.fillText('D = ' + D.toFixed(2) + ' m', centerX, tankTopY - 20);

                // Cota h(t) a la izquierda
                if (h > 0.05) {{
                    const xCotaH = marginX - 16;
                    dibujarFlechaDoble(tankCtx, xCotaH, tankBottomY, xCotaH, waterTopY, '#2563EB');
                    tankCtx.fillStyle = '#2563EB';
                    tankCtx.font = 'bold 11px sans-serif';
                    tankCtx.textAlign = 'right';
                    tankCtx.fillText('h(t) = ' + h.toFixed(2) + 'm', xCotaH - 4, (tankBottomY + waterTopY) / 2 + 4);
                }}

                // Cota d (orificio) abajo
                tankCtx.fillStyle = '#1E3A8A';
                tankCtx.font = '10px sans-serif';
                tankCtx.textAlign = 'center';
                tankCtx.fillText('Orificio d = ' + (d * 100).toFixed(1) + ' cm', centerX, tankBottomY + 28);
            }}

            function dibujarFlechaDoble(ctx, x1, y1, x2, y2, color) {{
                ctx.strokeStyle = color;
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(x1, y1);
                ctx.lineTo(x2, y2);
                ctx.stroke();

                // Flechas en extremos
                ctx.fillStyle = color;
                const head = 4;
                if (y1 === y2) {{ // Horizontal
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x1 + head, y1 - head);
                    ctx.lineTo(x1 + head, y1 + head);
                    ctx.fill();

                    ctx.beginPath();
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(x2 - head, y2 - head);
                    ctx.lineTo(x2 - head, y2 + head);
                    ctx.fill();
                }} else {{ // Vertical
                    ctx.beginPath();
                    ctx.moveTo(x1, y1);
                    ctx.lineTo(x1 - head, y1 - head);
                    ctx.lineTo(x1 + head, y1 - head);
                    ctx.fill();

                    ctx.beginPath();
                    ctx.moveTo(x2, y2);
                    ctx.lineTo(x2 - head, y2 + head);
                    ctx.lineTo(x2 + head, y2 + head);
                    ctx.fill();
                }}
            }}

            // -------------------------------------------------------------
            // DIBUJO DE LA GRÁFICA h(t) EN CANVAS
            // -------------------------------------------------------------
            function dibujarGrafica(tActual, hActual) {{
                const W = graphCanvas.width;
                const H = graphCanvas.height;
                graphCtx.clearRect(0, 0, W, H);

                const pL = 50, pR = 25, pT = 25, pB = 40;
                const plotW = W - pL - pR;
                const plotH = H - pT - pB;

                function mapX(t) {{
                    return pL + (t / t_final) * plotW;
                }}
                function mapY(valH) {{
                    return pT + plotH - (valH / h0) * plotH;
                }}

                // Cuadrícula y ejes
                graphCtx.strokeStyle = '#E5E7EB';
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

                // Ejes principales
                graphCtx.strokeStyle = '#9CA3AF';
                graphCtx.lineWidth = 1.5;
                graphCtx.beginPath();
                graphCtx.moveTo(pL, pT);
                graphCtx.lineTo(pL, pT + plotH);
                graphCtx.lineTo(pL + plotW, pT + plotH);
                graphCtx.stroke();

                // Etiquetas de ejes
                graphCtx.fillStyle = '#6B7280';
                graphCtx.font = '10px sans-serif';
                graphCtx.textAlign = 'right';
                graphCtx.fillText('0', pL - 6, pT + plotH + 3);
                graphCtx.fillText((h0 / 2).toFixed(2) + 'm', pL - 6, pT + plotH / 2 + 3);
                graphCtx.fillText(h0.toFixed(2) + 'm', pL - 6, pT + 4);

                graphCtx.textAlign = 'center';
                graphCtx.fillText('0', pL, pT + plotH + 16);
                graphCtx.fillText((t_final / 2).toFixed(0) + 's', pL + plotW / 2, pT + plotH + 16);
                graphCtx.fillText(t_final.toFixed(0) + 's', pL + plotW, pT + plotH + 16);

                // Títulos de ejes
                graphCtx.fillStyle = '#374151';
                graphCtx.font = 'bold 10px sans-serif';
                graphCtx.fillText('Tiempo t [s]', pL + plotW / 2, H - 6);

                graphCtx.save();
                graphCtx.translate(14, pT + plotH / 2);
                graphCtx.rotate(-Math.PI / 2);
                graphCtx.textAlign = 'center';
                graphCtx.fillText('Nivel h [m]', 0, 0);
                graphCtx.restore();

                // 1. Curva teórica completa (línea punteada gris de referencia)
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

                // 2. Trayectoria recorrida hasta currentTime (Azul fuerte continuo)
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
                        // Interpolar punto actual
                        const xNow = mapX(tActual);
                        const yNow = mapY(hActual);
                        if (started) graphCtx.lineTo(xNow, yNow);
                        break;
                    }}
                }}
                graphCtx.stroke();

                // 3. Puntos de cálculo RK4 alcanzados
                if (puntos_rk4 && puntos_rk4.length > 0) {{
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

                // Línea vertical tenue marcando tiempo actual
                graphCtx.strokeStyle = '#EF4444';
                graphCtx.lineWidth = 1;
                graphCtx.setLineDash([2, 2]);
                graphCtx.beginPath();
                graphCtx.moveTo(curX, pT);
                graphCtx.lineTo(curX, pT + plotH);
                graphCtx.stroke();
                graphCtx.setLineDash([]);

                // Punto rojo
                graphCtx.fillStyle = '#DC2626';
                graphCtx.beginPath();
                graphCtx.arc(curX, curY, 5.5, 0, Math.PI * 2);
                graphCtx.fill();
                graphCtx.strokeStyle = '#FFFFFF';
                graphCtx.lineWidth = 2;
                graphCtx.stroke();

                // Etiqueta flotante con el valor actual
                graphCtx.fillStyle = '#1E293B';
                graphCtx.font = 'bold 10px sans-serif';
                graphCtx.textAlign = 'left';
                const tagX = Math.min(plotW + pL - 50, curX + 8);
                const tagY = Math.max(pT + 12, curY - 8);
                graphCtx.fillText(hActual.toFixed(2) + ' m', tagX, tagY);
            }}

            // Dibujar estado inicial inmediatamente
            actualizarVista();
        </script>
    </body>
    </html>
    """
    return html_content
