@echo off
REM =========================================================================
REM KA PHONE - INGESTION MASSIVE COMPLETE (Windows)
REM =========================================================================
REM Orchestre les 3 phases d'ingestion dans le bon ordre.
REM Chaque phase peut etre interrompue et reprise avec Ctrl+C.
REM
REM Usage :
REM   .\run_ingestion_all.bat              # Ingestion complete
REM   .\run_ingestion_all.bat --test       # Mode test (rapide)
REM   .\run_ingestion_all.bat --resume     # Reprendre apres interruption
REM   .\run_ingestion_all.bat --status     # Voir l'etat
REM =========================================================================

REM Force UTF-8 encoding for Python
chcp 65001 >nul 2>nul
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

setlocal enabledelayedexpansion

echo.
echo ==============================================================
echo        KA PHONE - INGESTION MASSIVE GENERALISTE
echo        3 phases : Wikipedia ^| Corpus ^| QA Generation
echo ==============================================================
echo.

REM Check first argument
if "%1"=="--status" goto :status
if "%1"=="--test" set MODE=--quick
if "%1"=="--resume" set MODE=--resume
if "%1"=="" set MODE=

echo [%date% %time%] Demarrage de l'ingestion massive
echo.

REM ==================================================================
REM PHASE 1 : Wikipedia FR - MGH
REM ==================================================================
echo -------------------------------------------------------------
echo  PHASE 1/3 : Wikipedia FR - MGH (20 000+ articles)
echo -------------------------------------------------------------
echo.

if "%MODE%"=="--quick" (
    python ka_phone/ingest_real_french.py --articles 50 --resume
) else (
    python ka_phone/ingest_real_french.py --articles 20000 --resume
)

if errorlevel 1 (
    echo.
    echo [!] Phase 1 interrompue. Relancez avec : .\run_ingestion_all.bat --resume
    pause
    exit /b 1
)

echo.
echo [OK] Phase 1 terminee - MGH enrichi
echo.

REM ==================================================================
REM PHASE 2 : Corpus massif - Hologramme 256x256
REM ==================================================================
echo -------------------------------------------------------------
echo  PHASE 2/3 : Corpus Massif - Hologramme
echo  Sources : OpenSubtitles, Gutenberg, Wiktionnaire, Wikinews
echo -------------------------------------------------------------
echo.

if "%MODE%"=="--quick" (
    python ka_phone/ingest_corpus_massive.py --quick --resume
) else (
    python ka_phone/ingest_corpus_massive.py --target 1000000 --resume
)

if errorlevel 1 (
    echo.
    echo [!] Phase 2 interrompue. Relancez avec : .\run_ingestion_all.bat --resume
    pause
    exit /b 1
)

echo.
echo [OK] Phase 2 terminee - Hologramme enrichi
echo.

REM ==================================================================
REM PHASE 3 : Generation QA - Knowledge Base
REM ==================================================================
echo -------------------------------------------------------------
echo  PHASE 3/3 : Generation QA - Knowledge Base
echo  5000 articles - ~50 000 paires question-reponse
echo -------------------------------------------------------------
echo.

if "%MODE%"=="--quick" (
    python ka_phone/generate_qa_from_wikipedia.py --quick --resume
) else (
    python ka_phone/generate_qa_from_wikipedia.py --articles 5000 --resume
)

if errorlevel 1 (
    echo.
    echo [!] Phase 3 interrompue. Relancez avec : .\run_ingestion_all.bat --resume
    pause
    exit /b 1
)

echo.
echo [OK] Phase 3 terminee - QA generees
echo.

REM ==================================================================
REM FIN
REM ==================================================================
echo ==============================================================
echo        [OK] INGESTION MASSIVE TERMINEE
echo ==============================================================
echo.
echo   Pour lancer le serveur :
echo     python ka_phone/unified_server.py
echo.
echo   Pour voir les stats :
echo     python ka_phone/ingest_corpus_massive.py --status
echo     python ka_phone/generate_qa_from_wikipedia.py --status
echo.
pause
exit /b 0

:status
echo.
echo ==============================================================
echo        STATUT DE L'INGESTION
echo ==============================================================
echo.
echo --- Phase 1 : Wikipedia FR ---
python ka_phone/ingest_real_french.py --help >nul 2>&1
echo   Script disponible : ka_phone/ingest_real_french.py
if exist data\mgh\mgh_hologram.npy (
    echo   MGH hologramme : [OK] present
) else (
    echo   MGH hologramme : [--] absent
)
echo.
echo --- Phase 2 : Corpus Massif ---
python ka_phone/ingest_corpus_massive.py --status
echo.
echo --- Phase 3 : QA Generation ---
python ka_phone/generate_qa_from_wikipedia.py --status
echo.
pause
exit /b 0