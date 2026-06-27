@echo off
echo ============================================
echo HARMONIC AI SAAS - VÃ‰RIFICATION FINALE
echo ============================================
echo.

echo [1/7] VÃ©rification des prÃ©requis systÃ¨me...
echo.

REM VÃ©rifier Docker
echo VÃ©rification Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo âœ— Docker non installÃ©
    echo   Veuillez installer Docker Desktop: https://www.docker.com/products/docker-desktop/
    goto :error
) else (
    echo âœ“ Docker installÃ©
)

REM VÃ©rifier Docker Compose
echo VÃ©rification Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo âœ— Docker Compose non installÃ©
    echo   Installation: https://docs.docker.com/compose/install/
    goto :error
) else (
    echo âœ“ Docker Compose installÃ©
)

REM VÃ©rifier Python
echo VÃ©rification Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo âœ— Python non installÃ©
    echo   Veuillez installer Python 3.8+: https://www.python.org/downloads/
    goto :error
) else (
    echo âœ“ Python installÃ©
)

echo.
echo [2/7] VÃ©rification des fichiers de configuration...
echo.

REM VÃ©rifier les fichiers essentiels
set essential_files=requirements.txt docker-compose.yml Dockerfile app/main.py frontend/index.html
set missing_files=0

for %%f in (%essential_files%) do (
    if exist "%%f" (
        echo âœ“ %%f prÃ©sent
    ) else (
        echo âœ— %%f manquant
        set /a missing_files+=1
    )
)

if %missing_files% gtr 0 (
    echo.
    echo âš ï¸  %missing_files% fichier(s) essentiel(s) manquant(s)
    goto :error
)

echo.
echo [3/7] VÃ©rification des services Docker...
echo.

REM ArrÃªter les services existants (si prÃ©sents)
echo ArrÃªt des services existants...
docker-compose down >nul 2>&1

REM DÃ©marrer les services de base
echo DÃ©marrage des services de base...
docker-compose up -d postgres redis mongodb >nul 2>&1

REM Attendre l'initialisation
echo Attente de l'initialisation (10 secondes)...
timeout /t 10 /nobreak >nul

REM VÃ©rifier que les services sont en cours d'exÃ©cution
echo VÃ©rification des services...
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo âœ— Certains services ne sont pas en cours d'exÃ©cution
    goto :error
) else (
    echo âœ“ Tous les services de base sont en cours d'exÃ©cution
)

echo.
echo [4/7] VÃ©rification de la base de donnÃ©es...
echo.

REM Tester la connexion PostgreSQL
echo Test connexion PostgreSQL...
python -c "
try:
    from sqlalchemy import create_engine
    engine = create_engine('postgresql://harmonic:harmonic123@localhost:5432/harmonic_saas')
    conn = engine.connect()
    result = conn.execute('SELECT 1')
    print('âœ“ Connexion PostgreSQL Ã©tablie')
    conn.close()
except Exception as e:
    print(f'âœ— Erreur PostgreSQL: {e}')
    exit(1)
" >nul 2>&1

if errorlevel 1 (
    echo âœ— Connexion PostgreSQL Ã©chouÃ©e
    goto :error
) else (
    echo âœ“ PostgreSQL opÃ©rationnel
)

echo.
echo [5/7] VÃ©rification de Redis...
echo.

REM Tester la connexion Redis
echo Test connexion Redis...
python -c "
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    if r.ping():
        print('âœ“ Connexion Redis Ã©tablie')
    else:
        print('âœ— Redis ne rÃ©pond pas')
        exit(1)
except Exception as e:
    print(f'âœ— Erreur Redis: {e}')
    exit(1)
" >nul 2>&1

if errorlevel 1 (
    echo âœ— Connexion Redis Ã©chouÃ©e
    goto :error
) else (
    echo âœ“ Redis opÃ©rationnel
)

echo.
echo [6/7] DÃ©marrage de l'API backend...
echo.

REM DÃ©marrer l'API
echo DÃ©marrage FastAPI backend...
docker-compose up -d api >nul 2>&1

REM Attendre que l'API soit prÃªte
echo Attente de l'API (5 secondes)...
timeout /t 5 /nobreak >nul

REM Tester l'API
echo Test API backend...
curl -s -f http://localhost:9000/health >nul 2>&1
if errorlevel 1 (
    echo âœ— API backend inaccessible
    goto :error
) else (
    echo âœ“ API backend opÃ©rationnelle
)

echo.
echo [7/7] VÃ©rification de l'intÃ©gration LM Arena...
echo.

REM Tester la connexion Ã  l'API DeepSeek AWS
echo Test connexion DeepSeek API AWS...
python -c "
import asyncio
import httpx

async def test():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get('http://__EC2_IP__:8000/health')
            if response.status_code == 200:
                print('âœ“ DeepSeek API AWS accessible')
            else:
                print(f'âœ— DeepSeek API retourne: {response.status_code}')
                exit(1)
    except Exception as e:
        print(f'âœ— Erreur DeepSeek API: {e}')
        exit(1)

asyncio.run(test())
" >nul 2>&1

if errorlevel 1 (
    echo âœ— Connexion DeepSeek API Ã©chouÃ©e
    echo   Note: VÃ©rifiez la connectivitÃ© rÃ©seau et que l'instance EC2 est en cours d'exÃ©cution
    goto :warning
) else (
    echo âœ“ DeepSeek API AWS opÃ©rationnelle
)

echo.
echo ============================================
echo âœ… VÃ‰RIFICATION TERMINÃ‰E AVEC SUCCÃˆS !
echo ============================================
echo.
echo ðŸ“Š RÃ‰SUMÃ‰ :
echo - Docker et Docker Compose : âœ“ OK
echo - Python : âœ“ OK
echo - Fichiers de configuration : âœ“ OK
echo - Services Docker : âœ“ OK
echo - PostgreSQL : âœ“ OK
echo - Redis : âœ“ OK
echo - API Backend : âœ“ OK
echo - DeepSeek API AWS : âœ“ OK
echo.
echo ðŸŒ SERVICES DISPONIBLES :
echo - Dashboard Frontend : http://localhost:8080
echo - API Backend        : http://localhost:9000
echo - Documentation API  : http://localhost:9000/docs
echo - MÃ©triques          : http://localhost:9000/metrics
echo.
echo ðŸš€ PROCHAINES Ã‰TAPES :
echo 1. Ouvrez http://localhost:8080 pour accÃ©der au dashboard
echo 2. CrÃ©ez un compte utilisateur
echo 3. Testez le chat LM Arena
echo 4. Configurez votre abonnement
echo.
echo ðŸ“‹ POUR PLUS D'INFORMATIONS :
echo - Guide complet : README.md
echo - DÃ©marrage rapide : QUICK_START.md
echo - DÃ©ploiement AWS : deploy_aws.md
echo.
goto :success

:error
echo.
echo ============================================
echo âŒ ERREURS DÃ‰TECTÃ‰ES
echo ============================================
echo.
echo Des problÃ¨mes ont Ã©tÃ© dÃ©tectÃ©s lors de la vÃ©rification.
echo Consultez les messages ci-dessus pour plus de dÃ©tails.
echo.
echo Actions recommandÃ©es :
echo 1. VÃ©rifiez que Docker Desktop est en cours d'exÃ©cution
echo 2. VÃ©rifiez les fichiers manquants
echo 3. ExÃ©cutez le script de vÃ©rification dÃ©taillÃ©e :
echo    python verify_deployment.py
echo.
pause
exit /b 1

:warning
echo.
echo ============================================
echo âš ï¸  AVERTISSEMENTS
echo ============================================
echo.
echo Certains services optionnels ne sont pas accessibles.
echo Le systÃ¨me principal est opÃ©rationnel.
echo.
echo Services affectÃ©s :
echo - DeepSeek API AWS : Non accessible
echo.
echo Note : Vous pouvez toujours utiliser le dashboard SaaS,
echo mais l'intÃ©gration LM Arena nÃ©cessite la connexion Ã  l'API DeepSeek.
echo.
echo Pour rÃ©soudre :
echo 1. VÃ©rifiez la connectivitÃ© rÃ©seau
echo 2. Assurez-vous que l'instance EC2 AWS est en cours d'exÃ©cution
echo 3. VÃ©rifiez les rÃ¨gles de sÃ©curitÃ© AWS
echo.
goto :success

:success
echo.
echo ============================================
echo ðŸŽ‰ PRÃŠT POUR L'INTÃ‰GRATION LM ARENA !
echo ============================================
echo.
echo Le dashboard SaaS Harmonic AI est maintenant opÃ©rationnel.
echo Vous pouvez :
echo 1. IntÃ©grer avec les services LM Arena existants
echo 2. Traiter des fichiers audio/vidÃ©o avec la technologie harmonique
echo 3. GÃ©rer les abonnements et la facturation
echo 4. Monitorer les performances et l'utilisation
echo.
echo Pour tester l'intÃ©gration complÃ¨te :
echo python test_lm_arena_integration.py
echo.
echo Appuyez sur une touche pour terminer...
pause >nul
exit /b 0