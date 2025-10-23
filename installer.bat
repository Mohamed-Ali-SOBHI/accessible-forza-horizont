@echo off
chcp 65001 >nul
title Installation - Système de Conduite Accessible

echo ============================================================
echo   INSTALLATION DU SYSTÈME DE CONDUITE ACCESSIBLE
echo ============================================================
echo.
echo Ce script va installer toutes les dépendances nécessaires.
echo.
pause
echo.

echo [1/3] Vérification de Python...
python --version
if errorlevel 1 (
    echo.
    echo ERREUR: Python n'est pas installé ou n'est pas dans le PATH.
    echo Téléchargez Python depuis: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Installation des dépendances...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERREUR: L'installation des dépendances a échoué.
    echo Essayez manuellement: pip install opencv-python mediapipe pyautogui numpy
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] Test de l'installation...
echo.
python test_setup.py

echo.
echo ============================================================
echo   INSTALLATION TERMINÉE
echo ============================================================
echo.
echo Pour lancer le programme:
echo   - Double-cliquez sur lancer.bat
echo   - Ou tapez: python accessible_face_drive.py
echo.
echo Consultez GUIDE_UTILISATION.md pour plus d'informations.
echo.
pause
