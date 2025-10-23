@echo off
chcp 65001 >nul
title Système de Conduite Accessible

echo ============================================================
echo   SYSTÈME DE CONDUITE ACCESSIBLE PAR MOUVEMENTS DE TÊTE
echo ============================================================
echo.
echo Lancement en cours...
echo.

python accessible_face_drive.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   ERREUR DÉTECTÉE
    echo ============================================================
    echo.
    echo Le programme s'est terminé avec une erreur.
    echo Consultez le message d'erreur ci-dessus.
    echo.
    echo Pour tester votre installation, lancez: python test_setup.py
    echo Pour plus d'aide, consultez GUIDE_UTILISATION.md
    echo.
    pause
) else (
    echo.
    echo Session terminée normalement.
    echo.
)
