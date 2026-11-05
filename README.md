# 💧 Vaciado de Tanque Cilíndrico — Métodos Numéricos
### Trabajo Universitario · Ingeniería Civil

Aplicación interactiva que demuestra los métodos de **Euler**, **RK2 (Punto Medio)** y **Runge-Kutta de 4to orden (RK4)** aplicados al vaciado de un tanque cilíndrico por un orificio de fondo (Ley de Torricelli).

---

## 🖥️ Requisitos Previos

| Requisito | Versión mínima | Verificar con |
|-----------|---------------|---------------|
| Python    | 3.9 o superior | `python --version` |
| pip       | (incluido con Python) | `pip --version` |

> **¿No tienes Python?** Descárgalo desde [python.org/downloads](https://www.python.org/downloads/).  
> Durante la instalación **marca la casilla "Add Python to PATH"**.

---

## 🚀 Puesta en Marcha

### Opción Rápida (Windows): Doble Clic ⚡
Simplemente haz **doble clic en el archivo `iniciar.bat`**. 
Este script se encarga automáticamente de:
1. Verificar que Python esté instalado.
2. Instalar las dependencias de `requirements.txt` que falten.
3. Abrir la aplicación interactiva en tu navegador.

---

### Opción Manual por Terminal (paso a paso)

### Paso 1 · Abrir una terminal

- **Windows:** Abrir el Explorador de archivos → navegar a la carpeta del proyecto → clic en la barra de dirección → escribir `cmd` y presionar Enter.
- **Alternativa:** Abrir PowerShell o CMD y navegar con:
  ```
  cd ruta\a\la\carpeta\Metodos
  ```

### Paso 2 · Instalar las dependencias (solo la primera vez)

```
pip install -r requirements.txt
```

Esto instala automáticamente: `numpy`, `matplotlib`, `pandas` y `streamlit`.

> Si aparecen advertencias de PATH, ignóralas. No afectan el funcionamiento.

### Paso 3 · Ejecutar la aplicación

```
streamlit run app.py
```

Se abrirá automáticamente tu navegador en **http://localhost:8501** con la aplicación funcionando.

> Si no se abre solo, copia la dirección `http://localhost:8501` y pégala manualmente en tu navegador (Chrome, Edge, Firefox).

### Paso 4 · Usar la aplicación

1. En la **barra lateral izquierda** ajusta los parámetros (o deja los valores por defecto).
2. Navega entre las **6 pestañas** de resultados.
3. Descarga tablas (CSV) y gráficos (PNG) con los botones de descarga 📥.

### Paso 5 · Detener la aplicación

En la terminal donde la ejecutaste, presiona **Ctrl + C**.

---

## 📂 Archivos del Proyecto

```
Metodos/
├── app.py                  ← Interfaz web (Streamlit) - ARCHIVO PRINCIPAL
├── simulacion_widget.py    ← Simulador dinámico interactivo en tiempo real (animación del tanque)
├── metodos.py              ← Métodos numéricos (Euler, RK2, RK4) - lógica de cálculo
├── pruebas.py              ← Pruebas de validación automáticas
├── requirements.txt        ← Lista de librerías necesarias
├── iniciar.bat             ← Lanzador con doble clic para Windows
├── README.md               ← Este documento
├── generar_diagrama.py     ← Script que genera el diagrama del tanque
├── assets/
│   └── diagrama_tanque.png ← Diagrama esquemático del tanque
└── .streamlit/
    └── config.toml         ← Configuración de tema visual (fondo blanco)
```

---

## 🧪 Ejecutar las Pruebas (opcional)

Para verificar que todo funciona correctamente antes de la presentación:

```
python pruebas.py
```

Si todo está bien, verás al final:

```
======================================================================
TODAS LAS PRUEBAS PASARON SATISFACTORIAMENTE (100% SUCCESS)
======================================================================
```

---

## 📋 Resumen Rápido de Comandos

| Acción | Comando |
|--------|---------|
| Instalar dependencias | `pip install -r requirements.txt` |
| Ejecutar la app | `streamlit run app.py` |
| Ejecutar pruebas | `python pruebas.py` |
| Detener la app | `Ctrl + C` en la terminal |

---

## ⚠️ Solución de Problemas Comunes

| Problema | Solución |
|----------|----------|
| `python` no se reconoce como comando | Python no está en el PATH. Reinstálalo marcando "Add to PATH", o usa `python3` en su lugar. |
| `streamlit` no se reconoce como comando | Ejecuta con: `python -m streamlit run app.py` |
| Error de permisos al instalar | Usa: `pip install --user -r requirements.txt` |
| La app se ve con fondo oscuro | Recarga la página; el tema claro está configurado en `.streamlit/config.toml` |
| Error "El tanque se vació..." | Es normal si N·h supera el tiempo de vaciado. Reduce N o h en la barra lateral. |
