@echo off
REM ============================================================
REM KA Phone — Audit Clean Runner
REM Purge les caches Python, desactive les .pyc,
REM injecte les 46 faits d'audit, et lance l'audit 91 questions.
REM Usage: run_audit_clean.bat
REM ============================================================

set PYTHONDONTWRITEBYTECODE=1

echo ============================================================
echo KA PHONE — AUDIT CLEAN RUNNER
echo ============================================================
echo.

echo [1/4] Purge des caches Python...
python -c "import os,shutil,glob;d=0;[shutil.rmtree(os.path.join(r,dd),ignore_errors=True)or(d:=d+1)for r,ds,fs in os.walk('.')for dd in ds if dd=='__pycache__'];print(f'  {d} __pycache__ supprimes')"
python -c "import os,glob;c=sum(1 for f in glob.glob('**/*.pyc',recursive=True)if not os.remove(f));print(f'  {c} .pyc supprimes')"
echo.

echo [2/4] Verification QuickFacts...
python -c "from quick_facts import QuickFacts;qf=QuickFacts();a=sum(1 for f,_,_ in qf.facts if 'audit_' in f);print(f'  Faits audit: {a}/46');print(f'  Total: {qf.get_all_facts_count()}');ans,conf=qf.lookup('Quelle est la capitale du Senegal');print(f'  Test Dakar: {ans} (conf={conf})')"
echo.

echo [3/4] Lancement de l'audit 91 questions...
echo.
python audit_100_questions.py

echo.
echo [4/4] Resultats...
type audit_report.txt | findstr /C:"Score global" /C:"Validees" /C:"Repartition" /C:"quick_facts" /C:"Date:"

echo.
echo ============================================================
echo AUDIT TERMINE
echo ============================================================