"""
generar_diagrama.py - Genera el diagrama esquemático del tanque cilíndrico con orificio
"""
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def generar_diagrama_tanque(ruta_salida="assets/diagrama_tanque.png"):
    """Genera un diagrama técnico limpio del tanque cilíndrico con orificio de fondo."""

    fig, ax = plt.subplots(figsize=(7, 6), dpi=200)
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # --- Dimensiones del dibujo ---
    tanque_x = 2.0       # borde izquierdo del tanque
    tanque_ancho = 4.0   # ancho visual del tanque
    tanque_base = 1.0    # coordenada Y del fondo
    tanque_alto = 5.5    # altura del cilindro
    tanque_top = tanque_base + tanque_alto

    centro_x = tanque_x + tanque_ancho / 2.0  # centro horizontal
    nivel_agua = tanque_base + 3.8             # nivel del agua (visual)

    # --- Paredes del tanque (líneas gruesas) ---
    grosor_pared = 3.0
    color_pared = '#374151'

    # Pared izquierda
    ax.plot([tanque_x, tanque_x], [tanque_base, tanque_top], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')
    # Pared derecha
    ax.plot([tanque_x + tanque_ancho, tanque_x + tanque_ancho], [tanque_base, tanque_top], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')
    # Fondo (con hueco para orificio)
    orificio_ancho = 0.35
    ax.plot([tanque_x, centro_x - orificio_ancho/2], [tanque_base, tanque_base], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')
    ax.plot([centro_x + orificio_ancho/2, tanque_x + tanque_ancho], [tanque_base, tanque_base], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')
    # Borde superior abierto (labio)
    ax.plot([tanque_x - 0.15, tanque_x + 0.01], [tanque_top, tanque_top], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')
    ax.plot([tanque_x + tanque_ancho - 0.01, tanque_x + tanque_ancho + 0.15], [tanque_top, tanque_top], color=color_pared, linewidth=grosor_pared, solid_capstyle='round')

    # --- Agua dentro del tanque ---
    agua = patches.FancyBboxPatch(
        (tanque_x + 0.05, tanque_base + 0.05),
        tanque_ancho - 0.1,
        nivel_agua - tanque_base - 0.05,
        boxstyle="square,pad=0",
        facecolor='#BFDBFE',
        edgecolor='none',
        alpha=0.7
    )
    ax.add_patch(agua)

    # Superficie del agua (línea ondulada)
    x_onda = np.linspace(tanque_x + 0.05, tanque_x + tanque_ancho - 0.05, 200)
    y_onda = nivel_agua + 0.06 * np.sin(6 * np.pi * (x_onda - tanque_x) / tanque_ancho)
    ax.plot(x_onda, y_onda, color='#2563EB', linewidth=1.8, alpha=0.9)

    # --- Orificio de salida ---
    orificio_rect = patches.FancyBboxPatch(
        (centro_x - orificio_ancho/2, tanque_base - 0.12),
        orificio_ancho,
        0.24,
        boxstyle="round,pad=0.03",
        facecolor='#1E3A8A',
        edgecolor=color_pared,
        linewidth=1.5
    )
    ax.add_patch(orificio_rect)

    # --- Chorro de agua saliente ---
    chorro_x = np.array([centro_x - 0.10, centro_x + 0.10, centro_x + 0.25, centro_x - 0.25])
    chorro_y = np.array([tanque_base - 0.12, tanque_base - 0.12, tanque_base - 1.0, tanque_base - 1.0])
    ax.fill(chorro_x, chorro_y, color='#93C5FD', alpha=0.5, edgecolor='none')

    # Gotitas
    for dx, dy, s in [(-0.1, -0.75, 15), (0.12, -0.85, 10), (0.0, -0.65, 12)]:
        ax.plot(centro_x + dx, tanque_base + dy, 'o', color='#60A5FA', markersize=s/3, alpha=0.7)

    # --- Cotas y dimensiones ---
    estilo_cota = dict(color='#DC2626', fontsize=12, fontweight='bold', ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#DC2626', linewidth=1.2, alpha=0.95))

    # Cota D (diámetro del tanque) - arriba
    y_cota_D = tanque_top + 0.45
    ax.annotate('', xy=(tanque_x, y_cota_D), xytext=(tanque_x + tanque_ancho, y_cota_D),
                arrowprops=dict(arrowstyle='<->', color='#DC2626', lw=1.8))
    ax.text(centro_x, y_cota_D + 0.3, 'D', **estilo_cota)

    # Cota h₀ (altura inicial) - a la derecha
    x_cota_h = tanque_x + tanque_ancho + 0.7
    ax.annotate('', xy=(x_cota_h, tanque_base), xytext=(x_cota_h, nivel_agua),
                arrowprops=dict(arrowstyle='<->', color='#2563EB', lw=1.8))
    ax.text(x_cota_h + 0.55, (tanque_base + nivel_agua) / 2, '$h_0$',
            color='#2563EB', fontsize=13, fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.25', facecolor='white', edgecolor='#2563EB', linewidth=1.2, alpha=0.95))

    # Líneas auxiliares punteadas para h₀
    ax.plot([tanque_x + tanque_ancho + 0.1, x_cota_h + 0.15], [tanque_base, tanque_base], ':', color='#9CA3AF', linewidth=1)
    ax.plot([tanque_x + tanque_ancho + 0.1, x_cota_h + 0.15], [nivel_agua, nivel_agua], ':', color='#9CA3AF', linewidth=1)

    # Cota d (diámetro del orificio) - abajo
    y_cota_d = tanque_base - 0.55
    ax.annotate('', xy=(centro_x - orificio_ancho/2, y_cota_d), xytext=(centro_x + orificio_ancho/2, y_cota_d),
                arrowprops=dict(arrowstyle='<->', color='#DC2626', lw=1.5))
    ax.text(centro_x, y_cota_d - 0.3, 'd', **{**estilo_cota, 'fontsize': 11})

    # Etiqueta del orificio
    ax.text(centro_x + 1.5, tanque_base - 0.3, 'Orificio\nde descarga',
            fontsize=9, ha='center', va='top', color='#4B5563', style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FEF3C7', edgecolor='#D97706', linewidth=1, alpha=0.9))
    ax.annotate('', xy=(centro_x + orificio_ancho/2 + 0.05, tanque_base),
                xytext=(centro_x + 1.0, tanque_base - 0.2),
                arrowprops=dict(arrowstyle='->', color='#D97706', lw=1.2, connectionstyle='arc3,rad=-0.2'))

    # Etiqueta de gravedad g
    x_g = tanque_x - 0.9
    y_g = (tanque_base + nivel_agua) / 2 + 0.5
    ax.annotate('', xy=(x_g, y_g - 0.8), xytext=(x_g, y_g + 0.3),
                arrowprops=dict(arrowstyle='->', color='#059669', lw=2.0, mutation_scale=15))
    ax.text(x_g + 0.02, y_g + 0.55, '$g$', fontsize=13, fontweight='bold', ha='center', va='center', color='#059669')

    # Etiqueta "Nivel de agua h(t)" dentro del tanque
    ax.text(centro_x, nivel_agua - 0.6, '$h(t)$', fontsize=14, fontweight='bold',
            ha='center', va='center', color='#1E40AF', alpha=0.8)

    # Título del diagrama
    ax.text(centro_x, tanque_top + 1.2,
            'Vaciado de Tanque Cilíndrico\npor Orificio de Fondo (Ley de Torricelli)',
            fontsize=13, fontweight='bold', ha='center', va='center', color='#1F2937',
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#EFF6FF', edgecolor='#1E3A8A', linewidth=1.5))

    # EDO en la esquina
    ax.text(tanque_x - 0.8, tanque_base - 0.6,
            r'$\frac{dh}{dt} = -k\sqrt{h}$',
            fontsize=12, ha='center', va='center', color='#1E3A8A',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#EFF6FF', edgecolor='#93C5FD', linewidth=1, alpha=0.9))

    # --- Configuración de ejes ---
    ax.set_xlim(-0.2, 8.2)
    ax.set_ylim(-0.6, tanque_top + 2.0)
    ax.set_aspect('equal')
    ax.axis('off')

    fig.tight_layout(pad=0.5)
    fig.savefig(ruta_salida, dpi=200, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"Diagrama generado exitosamente en: {ruta_salida}")


if __name__ == "__main__":
    import os
    os.makedirs("assets", exist_ok=True)
    generar_diagrama_tanque()

