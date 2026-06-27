@echo off
chcp 65001 >nul
echo ============================================================
echo   KA-Next v2 - INGESTION MASSIVE
echo   Construit 12 hologrammes 64x64 + ingere toutes les sources
echo ============================================================
echo.
echo Sources :
echo   [1] Corpus UNESCO (32 faits)
echo   [2] Corpus Sciences (20 faits)
echo   [3] Corpus Philosophie (10 faits)
echo   [4] Corpus enrichi (geographie, histoire, mathematiques...)
echo   [5] QuickFacts (1030 faits)
echo   [6] Fichiers texte locaux (data/corpus/*.txt, *.md)
echo.
echo Total estime : ~2000 faits dans 12 domaines specialises
echo Temps estime : ~2 secondes
echo.

set PYTHONIOENCODING=utf-8
python "%~dp0ingest_massive_nx64.py"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   INGESTION TERMINEE AVEC SUCCES
    echo ============================================================
    echo.
    echo   Pour tester :
    echo     python ka_next_core.py --query "Quelle est la capitale du Senegal ?"
    echo     python ka_next_core.py --demo
    echo.
    echo   Pour le benchmark :
    echo     python benchmark_ensemble.py
    echo ============================================================
) else (
    echo.
    echo ============================================================
    echo   ERREUR lors de l'ingestion. Verifiez la console ci-dessus.
    echo ============================================================
)

pause