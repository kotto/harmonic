#!/usr/bin/env python3
"""
VÃ©rification du dÃ©ploiement Harmonic AI SaaS
============================================
VÃ©rifie que tous les services sont correctement configurÃ©s et accessibles
"""

import sys
import os
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

def print_header(text):
    """Affiche un en-tÃªte formatÃ©"""
    print("\n" + "="*60)
    print(f" {text}")
    print("="*60)

def print_success(message):
    """Affiche un message de succÃ¨s"""
    print(f"  âœ“ {message}")

def print_warning(message):
    """Affiche un message d'avertissement"""
    print(f"  âš ï¸  {message}")

def print_error(message):
    """Affiche un message d'erreur"""
    print(f"  âœ— {message}")

def check_docker():
    """VÃ©rifie que Docker est installÃ© et en cours d'exÃ©cution"""
    print_header("VÃ‰RIFICATION DOCKER")
    
    try:
        # VÃ©rifier l'installation Docker
        result = subprocess.run(["docker", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker installÃ©: {result.stdout.strip()}")
        else:
            print_error("Docker non installÃ©")
            return False
        
        # VÃ©rifier que Docker est en cours d'exÃ©cution
        result = subprocess.run(["docker", "info"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success("Docker en cours d'exÃ©cution")
            return True
        else:
            print_error("Docker n'est pas en cours d'exÃ©cution")
            return False
            
    except FileNotFoundError:
        print_error("Docker non trouvÃ© dans le PATH")
        return False
    except Exception as e:
        print_error(f"Erreur Docker: {str(e)}")
        return False

def check_docker_compose():
    """VÃ©rifie que Docker Compose est installÃ©"""
    print_header("VÃ‰RIFICATION DOCKER COMPOSE")
    
    try:
        result = subprocess.run(["docker-compose", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print_success(f"Docker Compose installÃ©: {result.stdout.strip()}")
            return True
        else:
            print_error("Docker Compose non installÃ©")
            return False
            
    except FileNotFoundError:
        print_error("Docker Compose non trouvÃ© dans le PATH")
        return False
    except Exception as e:
        print_error(f"Erreur Docker Compose: {str(e)}")
        return False

def check_python_dependencies():
    """VÃ©rifie les dÃ©pendances Python"""
    print_header("VÃ‰RIFICATION DÃ‰PENDANCES PYTHON")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "psycopg2-binary",
        "redis",
        "pydantic",
        "httpx",
        "celery",
        "prometheus-client"
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            # Nettoyer le nom du package pour l'import
            import_name = package.split('-')[0].replace('_', '-')
            __import__(import_name)
            print_success(f"{package} installÃ©")
        except ImportError:
            print_error(f"{package} non installÃ©")
            all_installed = False
    
    return all_installed

def check_config_files():
    """VÃ©rifie les fichiers de configuration"""
    print_header("VÃ‰RIFICATION FICHIERS CONFIGURATION")
    
    required_files = [
        "requirements.txt",
        "docker-compose.yml",
        "Dockerfile",
        "app/core/config.py",
        "app/core/database.py",
        "app/services/lm_arena_integration.py",
        "frontend/index.html",
        "frontend/app.js",
        "frontend/config.js"
    ]
    
    all_exist = True
    
    for file_path in required_files:
        full_path = Path(file_path)
        if full_path.exists():
            print_success(f"{file_path} prÃ©sent")
        else:
            print_error(f"{file_path} manquant")
            all_exist = False
    
    return all_exist

def check_environment_variables():
    """VÃ©rifie les variables d'environnement"""
    print_header("VÃ‰RIFICATION VARIABLES ENVIRONNEMENT")
    
    required_vars = [
        "DATABASE_URL",
        "REDIS_URL",
        "JWT_SECRET_KEY"
    ]
    
    optional_vars = [
        "LM_ARENA_SERVICE_URL",
        "AUDIO_SERVICE_URL",
        "VIDEO_SERVICE_URL",
        "AWS_S3_BUCKET",
        "STRIPE_SECRET_KEY"
    ]
    
    all_set = True
    
    # VÃ©rifier les variables requises
    for var in required_vars:
        if os.getenv(var):
            print_success(f"{var} dÃ©finie")
        else:
            print_error(f"{var} non dÃ©finie")
            all_set = False
    
    # VÃ©rifier les variables optionnelles
    for var in optional_vars:
        if os.getenv(var):
            print_success(f"{var} dÃ©finie")
        else:
            print_warning(f"{var} non dÃ©finie (optionnel)")
    
    return all_set

def check_aws_connectivity():
    """VÃ©rifie la connectivitÃ© avec les services AWS"""
    print_header("VÃ‰RIFICATION CONNECTIVITÃ‰ AWS")
    
    services_to_check = [
        {
            "name": "DeepSeek API",
            "url": "http://__EC2_IP__:8000/health",
            "required": True
        },
        {
            "name": "Audio Service",
            "url": "http://localhost:9017/health",
            "required": False
        },
        {
            "name": "Video Service",
            "url": "http://localhost:9018/health",
            "required": False
        }
    ]
    
    all_accessible = True
    
    for service in services_to_check:
        try:
            import httpx
            import asyncio
            
            async def test():
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(service["url"])
                    return response.status_code == 200
            
            accessible = asyncio.run(test())
            
            if accessible:
                print_success(f"{service['name']} accessible")
            else:
                if service["required"]:
                    print_error(f"{service['name']} inaccessible")
                    all_accessible = False
                else:
                    print_warning(f"{service['name']} inaccessible (optionnel)")
                    
        except ImportError:
            print_warning(f"httpx non installÃ©, impossible de tester {service['name']}")
        except Exception as e:
            if service["required"]:
                print_error(f"Erreur test {service['name']}: {str(e)}")
                all_accessible = False
            else:
                print_warning(f"Erreur test {service['name']}: {str(e)}")
    
    return all_accessible

def check_database_connection():
    """VÃ©rifie la connexion Ã  la base de donnÃ©es"""
    print_header("VÃ‰RIFICATION CONNEXION BASE DE DONNÃ‰ES")
    
    try:
        # Essayer d'importer et de tester la connexion
        from app.core.database import engine
        
        # Tester la connexion
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            if result.scalar() == 1:
                print_success("Connexion PostgreSQL Ã©tablie")
                return True
            else:
                print_error("Connexion PostgreSQL Ã©chouÃ©e")
                return False
                
    except ImportError as e:
        print_error(f"Impossible d'importer les modules base de donnÃ©es: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Erreur connexion base de donnÃ©es: {str(e)}")
        return False

def check_redis_connection():
    """VÃ©rifie la connexion Ã  Redis"""
    print_header("VÃ‰RIFICATION CONNEXION REDIS")
    
    try:
        import redis
        from app.core.config import settings
        
        # Tester la connexion Redis
        redis_client = redis.Redis.from_url(settings.REDIS_URL)
        if redis_client.ping():
            print_success("Connexion Redis Ã©tablie")
            return True
        else:
            print_error("Connexion Redis Ã©chouÃ©e")
            return False
            
    except ImportError:
        print_error("Redis Python non installÃ©")
        return False
    except Exception as e:
        print_error(f"Erreur connexion Redis: {str(e)}")
        return False

def check_frontend():
    """VÃ©rifie le frontend"""
    print_header("VÃ‰RIFICATION FRONTEND")
    
    frontend_files = [
        "frontend/index.html",
        "frontend/app.js",
        "frontend/config.js"
    ]
    
    all_valid = True
    
    for file_path in frontend_files:
        full_path = Path(file_path)
        if full_path.exists():
            # VÃ©rifier que le fichier n'est pas vide
            if full_path.stat().st_size > 0:
                print_success(f"{file_path} valide")
            else:
                print_error(f"{file_path} vide")
                all_valid = False
        else:
            print_error(f"{file_path} manquant")
            all_valid = False
    
    return all_valid

def generate_deployment_report():
    """GÃ©nÃ¨re un rapport de dÃ©ploiement"""
    print_header("RAPPORT DE DÃ‰PLOIEMENT")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "docker": check_docker(),
            "docker_compose": check_docker_compose(),
            "python_dependencies": check_python_dependencies()
        },
        "configuration": {
            "config_files": check_config_files(),
            "environment_variables": check_environment_variables()
        },
        "connectivity": {
            "aws_services": check_aws_connectivity(),
            "database": check_database_connection(),
            "redis": check_redis_connection(),
            "frontend": check_frontend()
        },
        "summary": {
            "ready_for_deployment": False,
            "issues": [],
            "recommendations": []
        }
    }
    
    # Analyser les rÃ©sultats
    issues = []
    recommendations = []
    
    # VÃ©rifier Docker
    if not report["system"]["docker"]:
        issues.append("Docker non installÃ© ou non en cours d'exÃ©cution")
        recommendations.append("Installer Docker Desktop et le dÃ©marrer")
    
    if not report["system"]["docker_compose"]:
        issues.append("Docker Compose non installÃ©")
        recommendations.append("Installer Docker Compose")
    
    if not report["system"]["python_dependencies"]:
        issues.append("DÃ©pendances Python manquantes")
        recommendations.append("ExÃ©cuter: pip install -r requirements.txt")
    
    if not report["configuration"]["config_files"]:
        issues.append("Fichiers de configuration manquants")
        recommendations.append("VÃ©rifier la structure du projet")
    
    if not report["configuration"]["environment_variables"]:
        issues.append("Variables d'environnement requises non dÃ©finies")
        recommendations.append("CrÃ©er un fichier .env avec les variables requises")
    
    if not report["connectivity"]["aws_services"]:
        issues.append("Services AWS inaccessibles")
        recommendations.append("VÃ©rifier la connectivitÃ© rÃ©seau et les URLs des services")
    
    if not report["connectivity"]["database"]:
        issues.append("Connexion base de donnÃ©es Ã©chouÃ©e")
        recommendations.append("VÃ©rifier DATABASE_URL et que PostgreSQL est en cours d'exÃ©cution")
    
    if not report["connectivity"]["redis"]:
        issues.append("Connexion Redis Ã©chouÃ©e")
        recommendations.append("VÃ©rifier REDIS_URL et que Redis est en cours d'exÃ©cution")
    
    if not report["connectivity"]["frontend"]:
        issues.append("Fichiers frontend invalides")
        recommendations.append("VÃ©rifier les fichiers dans le dossier frontend/")
    
    # DÃ©terminer si le dÃ©ploiement est prÃªt
    ready = all([
        report["system"]["docker"],
        report["system"]["docker_compose"],
        report["configuration"]["config_files"],
        report["configuration"]["environment_variables"],
        report["connectivity"]["database"],
        report["connectivity"]["redis"]
    ])
    
    report["summary"]["ready_for_deployment"] = ready
    report["summary"]["issues"] = issues
    report["summary"]["recommendations"] = recommendations
    
    # Afficher le rapport
    print("\n" + "-"*60)
    print("RÃ‰SUMÃ‰ DU RAPPORT")
    print("-"*60)
    
    print(f"\nPrÃªt pour dÃ©ploiement: {'âœ“ OUI' if ready else 'âœ— NON'}")
    
    if issues:
        print(f"\nProblÃ¨mes dÃ©tectÃ©s ({len(issues)}):")
        for issue in issues:
            print(f"  â€¢ {issue}")
    
    if recommendations:
        print(f"\nRecommandations ({len(recommendations)}):")
        for rec in recommendations:
            print(f"  â€¢ {rec}")
    
    # Sauvegarder le rapport
    report_file = "deployment_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport sauvegardÃ© dans: {report_file}")
    
    return report

def main():
    """Fonction principale"""
    print("\n" + "="*60)
    print("VÃ‰RIFICATION DÃ‰PLOIEMENT HARMONIC AI SAAS")
    print("="*60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"RÃ©pertoire: {os.getcwd()}")
    
    try:
        # ExÃ©cuter toutes les vÃ©rifications
        report = generate_deployment_report()
        
        # Afficher les instructions de dÃ©ploiement
        print("\n" + "="*60)
        print("INSTRUCTIONS DE DÃ‰PLOIEMENT")
        print("="*60)
        
        if report["summary"]["ready_for_deployment"]:
            print("\nðŸŽ‰ Toutes les vÃ©rifications sont passÃ©es avec succÃ¨s !")
            print("\nPour dÃ©ployer le dashboard SaaS:")
            print("1. DÃ©marrer les services Docker:")
            print("   docker-compose up -d")
            print("\n2. DÃ©marrer le frontend:")
            print("   cd frontend && start_frontend.bat")
            print("\n3. VÃ©rifier l'accÃ¨s:")
            print("   - Frontend: http://localhost:8080")
            print("   - Backend:  http://localhost:9000")
            print("   - API Docs: http://localhost:9000/docs")
            print("\n4. Pour intÃ©gration LM Arena:")
            print("   - VÃ©rifier que l'API DeepSeek AWS est accessible")
            print("   - Tester: python test_lm_arena_integration.py")
        else:
            print("\nâš ï¸  Des problÃ¨mes ont Ã©tÃ© dÃ©tectÃ©s.")
            print("\nVeuillez rÃ©soudre les problÃ¨mes avant de dÃ©ployer:")
            for issue in report["summary"]["issues"]:
                print(f"  â€¢ {issue}")
            
            print("\nActions recommandÃ©es:")
            for rec in report["summary"]["recommendations"]:
                print(f"  â€¢ {rec}")
        
        print("\n" + "="*60)
        print("RESSOURCES UTILES")
        print("="*60)
        print("\nâ€¢ Documentation: README.md")
        print("â€¢ DÃ©ploiement AWS: deploy_aws.md")
        print("â€¢ Test intÃ©gration: test_lm_arena_integration.py")
        print("â€¢ VÃ©rification AWS: check_aws_services.py")
        print("â€¢ Script dÃ©marrage: start_all.bat")
        
        return 0 if report["summary"]["ready_for_deployment"] else 1
        
    except KeyboardInterrupt:
        print("\n\nVÃ©rification interrompue par l'utilisateur")
        return 1
    except Exception as e:
        print(f"\n[ERREUR CRITIQUE] {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\nCode de sortie: {exit_code}")
    sys.exit(exit_code)