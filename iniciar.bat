@echo off
title Vaciado de Tanque - Metodos Numericos (RK4)
chcp 65001 > nul
cls

echo ======================================================================
echo    VACIADO DE TANQUE CILINDRICO - METODOS NUMERICOS (ING. CIVIL)
echo ======================================================================
echo.

:: Verificar si Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No se encontro Python en el sistema.
    echo Por favor instala Python desde https://www.python.org marcando "Add to PATH".
    echo.
    pause
    exit /b 1
)

echo [1/2] Verificando dependencias necesarias...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [2/2] Iniciando la aplicacion web en tu navegador...
echo.
echo Presiona Ctrl + C en esta ventana cuando desees cerrar la aplicacion.
echo ======================================================================
echo.

:: Iniciar Streamlit usando el interprete de python directamente
python -m streamlit run app.py

pause

