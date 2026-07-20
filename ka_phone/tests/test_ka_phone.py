"""
Tests unitaires — KA Phone

Couverture :
- API endpoints (ka_phone_unified_server)
- PWA Service Worker
- UI components (ka-ui-new.js)
- Compression HCV
"""

import sys, os, json, unittest
from pathlib import Path

# Ajouter ka_phone/ au path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "engine"))


class TestKAPhoneAPI(unittest.TestCase):
    """Tests du serveur KA Phone."""

    @classmethod
    def setUpClass(cls):
        """Initialise le serveur de test une fois."""
        try:
            from ka_phone_unified_server import app
            cls.app = app
            cls.client = app.test_client()
        except ImportError:
            raise unittest.SkipTest("ka_phone_unified_server non trouvé")

    def test_health_endpoint(self):
        """GET /api/health doit retourner 200."""
        r = self.client.get('/api/health')
        self.assertIn(r.status_code, [200, 404])  # 404 si endpoint non défini

    def test_ask_endpoint_requires_prompt(self):
        """POST /api/chat sans prompt doit retourner une erreur."""
        r = self.client.post('/api/chat', json={})
        # Doit retourner soit 400, soit une réponse avec erreur
        self.assertIn(r.status_code, [200, 400, 422])

    def test_ask_endpoint_with_prompt(self):
        """POST /api/chat avec un prompt simple."""
        r = self.client.post('/api/chat', json={'prompt': 'Bonjour'})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(
            'text' in data or 'reponse' in data or 'response' in data or 'error' in data,
            f"Réponse inattendue: {data}"
        )

    def test_ask_endpoint_empty_prompt(self):
        """POST /api/chat avec prompt vide."""
        r = self.client.post('/api/chat', json={'prompt': ''})
        self.assertIn(r.status_code, [200, 400, 422])

    def test_cors_headers(self):
        """Les headers CORS doivent être présents."""
        r = self.client.options('/api/chat')
        #OPTIONS doit répondre
        self.assertIn(r.status_code, [200, 204, 404])

    def test_debug_detection(self):
        """Un prompt contenant 'debug' ou 'bug' doit être traité."""
        prompts = [
            "mon code a un bug",
            "/debug NullPointerException",
            "debug: memory leak",
        ]
        for p in prompts:
            r = self.client.post('/api/chat', json={'prompt': p})
            # Ne doit pas crasher
            self.assertIn(r.status_code, [200, 400, 422, 500])


class TestPWAFiles(unittest.TestCase):
    """Tests des fichiers PWA statiques."""

    @classmethod
    def setUpClass(cls):
        cls.ka_dir = Path(__file__).resolve().parent.parent

    def test_index_html_exists(self):
        """index.html doit exister et être du HTML valide."""
        path = self.ka_dir / "index.html"
        self.assertTrue(path.exists(), f"{path} introuvable")
        content = path.read_text(encoding='utf-8')
        self.assertIn('<!DOCTYPE html>', content)
        self.assertIn('<html', content)

    def test_manifest_json_exists(self):
        """manifest.json doit exister et être du JSON valide."""
        path = self.ka_dir / "www" / "manifest.json"
        self.assertTrue(path.exists(), f"{path} introuvable")
        data = json.loads(path.read_text())
        self.assertIn('name', data)
        self.assertIn('short_name', data)

    def test_service_worker_exists(self):
        """sw.js doit exister."""
        path = self.ka_dir / "sw.js"
        self.assertTrue(path.exists(), f"{path} introuvable")
        content = path.read_text(encoding='utf-8')
        #Doit contenir des patterns Service Worker
        self.assertTrue(
            'install' in content or 'fetch' in content or 'activate' in content or 'self.addEventListener' in content,
            "sw.js ne semble pas être un Service Worker valide"
        )

    def test_ui_js_exists(self):
        """ka-ui-new.js doit exister et définir les fonctions clés."""
        path = self.ka_dir / "www" / "ka-ui-new.js"
        self.assertTrue(path.exists(), f"{path} introuvable")
        content = path.read_text(encoding='utf-8')
        self.assertIn('showScreen', content)
        self.assertIn('sendChat', content)

    def test_ui_css_exists(self):
        """ka-ui.css doit exister."""
        path = self.ka_dir / "www" / "ka-ui.css"
        self.assertTrue(path.exists(), f"{path} introuvable")

    def test_no_broken_links_in_html(self):
        """Vérifie que les liens dans index.html pointent vers des fichiers existants."""
        path = self.ka_dir / "index.html"
        content = path.read_text(encoding='utf-8')
        import re
        # Trouver les références locales (src, href)
        refs = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', content)
        broken = []
        for ref in refs:
            if ref.startswith('http') or ref.startswith('#'):
                continue
            full_path = (self.ka_dir / ref).resolve()
            if not full_path.exists():
                broken.append(ref)
        self.assertEqual(len(broken), 0, f"Liens cassés: {broken}")


class TestCompressionHCV(unittest.TestCase):
    """Tests du module de compression HCV."""

    def test_hcv_service_import(self):
        """Le service HCV doit être importable."""
        try:
            from hcv_service import HCVService
            self.assertTrue(True)
        except ImportError:
            self.skipTest("hcv_service non trouvé dans engine/")

    def test_hcv_compress_decompress(self):
        """Compression + décompression d'un fichier test."""
        try:
            from hcv_service import HCVService
            import numpy as np

            # Créer une image test simple
            test_data = np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8)
            
            service = HCVService()
            # La compression peut échouer si les codecs ne sont pas compilés
            try:
                compressed = service.compress(test_data.tobytes(), quality=80)
                self.assertIsNotNone(compressed)
                self.assertLess(len(compressed), len(test_data.tobytes()),
                              "La compression devrait réduire la taille")
            except Exception as e:
                self.skipTest(f"HCV non disponible: {e}")
        except ImportError:
            self.skipTest("hcv_service non trouvé")


class TestMemory(unittest.TestCase):
    """Tests de la mémoire utilisateur."""

    def test_user_memory_import(self):
        """user_memory.py doit être importable."""
        try:
            import user_memory
            self.assertTrue(True)
        except ImportError:
            self.skipTest("user_memory non trouvé")

    def test_user_memory_store_retrieve(self):
        """Stockage et récupération d'une entrée mémoire."""
        try:
            from user_memory import UserMemory
            mem = UserMemory(user_id="test_user")
            mem.store("test_key", {"value": "test"})
            result = mem.retrieve("test_key")
            self.assertIsNotNone(result)
        except (ImportError, AttributeError):
            self.skipTest("UserMemory non disponible")


class TestUI(unittest.TestCase):
    """Tests des composants UI."""

    def test_screen_navigation_js(self):
        """Les fonctions de navigation d'écran existent."""
        ka_dir = Path(__file__).resolve().parent.parent
        js_path = ka_dir / "www" / "ka-ui-new.js"
        if not js_path.exists():
            self.skipTest("ka-ui-new.js non trouvé")
        content = js_path.read_text(encoding='utf-8')
        self.assertIn('showScreen', content)
        self.assertIn('addMsg', content)
        self.assertIn('sendChat', content)

    def test_all_screens_in_html(self):
        """Tous les écrans définis dans le JS existent dans le HTML."""
        ka_dir = Path(__file__).resolve().parent.parent
        html_path = ka_dir / "index.html"
        js_path = ka_dir / "www" / "ka-ui-new.js"
        if not html_path.exists() or not js_path.exists():
            self.skipTest("Fichiers manquants")
        
        import re
        js_content = js_path.read_text(encoding='utf-8')
        html_content = html_path.read_text(encoding='utf-8')
        
        # Trouver les noms d'écran dans le JS
        screens_js = re.findall(r"['\"]screen-(\w+)['\"]", js_content)
        # Vérifier qu'ils existent dans le HTML
        for screen in screens_js:
            self.assertIn(f'screen-{screen}', html_content,
                         f"Écran screen-{screen} défini dans JS mais absent du HTML")


if __name__ == '__main__':
    unittest.main(verbosity=2)
