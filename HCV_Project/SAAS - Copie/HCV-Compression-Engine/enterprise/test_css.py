#!/usr/bin/env python3
"""
Script de test pour vérifier que le CSS s'applique correctement
"""

import requests
import sys

def test_css_loading():
    """Test si le CSS se charge correctement"""
    base_url = "http://localhost:8081"
    
    print("🧪 Test de chargement CSS pour HCV PRO Enterprise AWS")
    print("=" * 50)
    
    # Test 1: Vérifier que le serveur répond
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            print("✅ Serveur répond correctement")
        else:
            print(f"❌ Erreur serveur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Impossible de se connecter au serveur: {e}")
        return False
    
    # Test 2: Vérifier que le CSS est accessible
    try:
        css_response = requests.get(f"{base_url}/static/style.css", timeout=5)
        if css_response.status_code == 200:
            css_size = len(css_response.content)
            print(f"✅ CSS accessible ({css_size} octets)")
            
            # Vérifier que le CSS contient des styles de base
            if ".login-container" in css_response.text:
                print("✅ Styles login trouvés")
            if ".header" in css_response.text:
                print("✅ Styles dashboard trouvés")
                
        else:
            print(f"❌ CSS non accessible: {css_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur chargement CSS: {e}")
        return False
    
    # Test 3: Vérifier que la page HTML contient le lien CSS
    try:
        html_response = requests.get(f"{base_url}/login", timeout=5)
        if 'href="/static/style.css"' in html_response.text or 'href="{{ url_for(' in html_response.text:
            print("✅ Lien CSS trouvé dans le HTML")
        else:
            print("❌ Lien CSS non trouvé dans le HTML")
            return False
    except Exception as e:
        print(f"❌ Erreur analyse HTML: {e}")
        return False
    
    print("\n🎉 Tous les tests CSS sont passés avec succès!")
    print(f"🌐 Accès à l'application: {base_url}")
    print("\n📝 Identifiants de test:")
    print("   - admin / HCV_PRO_2024_ENTERPRISE")
    print("   - aws_admin / AWS_ENTERPRISE_2024")
    print("   - user / HCV_USER_2024")
    print("   - demo / demo123")
    
    return True

if __name__ == "__main__":
    success = test_css_loading()
    sys.exit(0 if success else 1)
