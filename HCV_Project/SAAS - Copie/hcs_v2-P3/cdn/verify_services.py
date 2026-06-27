#!/usr/bin/env python3
"""
Vérification d'intégrité des services CDN
Valide que tous les services sont correctement configurés et présents
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

class CDNVerifier:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.config_path = self.base_dir / "config" / "services.json"
        self.services_dir = self.base_dir / "services"
        self.core_dir = self.base_dir / "core"
        self.errors = []
        self.warnings = []
        self.success = []

    def load_config(self) -> Dict:
        """Charge la configuration des services"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.errors.append(f"Impossible de charger services.json: {e}")
            return {}

    def verify_files_exist(self) -> bool:
        """Vérifie que tous les fichiers essentiels existent"""
        required_files = [
            self.config_path,
            self.services_dir / "service_base.py",
            self.services_dir / "launch_all_services.py",
            self.core_dir / "cdn_server.py",
        ]
        
        all_exist = True
        for file_path in required_files:
            if file_path.exists():
                self.success.append(f"✅ Fichier trouvé: {file_path.relative_to(self.base_dir)}")
            else:
                self.errors.append(f"❌ Fichier manquant: {file_path.relative_to(self.base_dir)}")
                all_exist = False
        
        return all_exist

    def verify_services(self, config: Dict) -> bool:
        """Vérifie que tous les services sont configurés et ont des scripts"""
        services = config.get("services", {})
        service_scripts = {
            "tv_broadcast_4k": "svc_tv_4k.py",
            "tv_broadcast_8k": "svc_tv_8k.py",
            "mobile_streaming_8k_us": "svc_mobile_us.py",
            "mobile_streaming_africa": "svc_mobile_africa.py",
            "vod_premium": "svc_vod.py",
            "live_events": "svc_live.py",
            "archive_storage": "svc_archive.py",
            "football_8k_bouquet": "svc_football_8k.py",
            "audio_upscale_8k": "svc_audio_upscale_8k.py",
            "radio_broadcast": "svc_radio_broadcast.py",
            "telephony_video_8k": "svc_telephony_8k.py",
            "webrtc_signaling": "svc_webrtc_signaling.py",
        }
        
        all_valid = True
        
        # Vérifier que tous les services attendus sont présents
        for service_id, script_name in service_scripts.items():
            if service_id in services:
                self.success.append(f"✅ Service configuré: {service_id}")
                
                # Vérifier que le script existe
                script_path = self.services_dir / script_name
                if script_path.exists():
                    self.success.append(f"   ✅ Script trouvé: {script_name}")
                else:
                    self.warnings.append(f"   ⚠️  Script manquant: {script_name} (sera auto-généré)")
            else:
                self.errors.append(f"❌ Service manquant dans config: {service_id}")
                all_valid = False
        
        # Vérifier qu'il n'y a pas de services supplémentaires non documentés
        for service_id in services:
            if service_id not in service_scripts:
                self.warnings.append(f"⚠️  Service supplémentaire non documenté: {service_id}")
        
        return all_valid

    def verify_service_config(self, config: Dict) -> bool:
        """Vérifie que chaque service a les champs requis"""
        services = config.get("services", {})
        required_fields = ["id", "name", "port", "protocol", "regions", "monthly_bandwidth_tb", "sla_uptime"]
        
        all_valid = True
        for service_id, service_config in services.items():
            missing_fields = [f for f in required_fields if f not in service_config]
            if missing_fields:
                self.errors.append(f"❌ {service_id}: champs manquants: {missing_fields}")
                all_valid = False
            else:
                self.success.append(f"✅ {service_id}: configuration valide")
        
        return all_valid

    def verify_edge_nodes(self, config: Dict) -> bool:
        """Vérifie que tous les nœuds edge sont configurés"""
        edge_nodes = config.get("edge_nodes", {})
        expected_nodes = [
            "Paris", "London", "Frankfurt", "Munich",
            "New York", "Los Angeles", "Chicago", "Dallas", "Miami", "Seattle",
            "Tokyo", "Seoul", "Sydney",
            "Dubai",
            "Sao Paulo",
            "Lagos", "Johannesburg", "Nairobi", "Cairo", "Dakar", "Casablanca"
        ]
        
        all_valid = True
        for node_name in expected_nodes:
            if node_name in edge_nodes:
                self.success.append(f"✅ Nœud edge: {node_name}")
            else:
                self.errors.append(f"❌ Nœud edge manquant: {node_name}")
                all_valid = False
        
        return all_valid

    def verify_global_stats(self, config: Dict) -> bool:
        """Vérifie les statistiques globales"""
        stats = config.get("global_stats", {})
        expected_stats = {
            "total_edge_nodes": 21,
            "regions_covered": 8,
            "countries_covered": 45,
            "active_users_million": 52,
        }
        
        all_valid = True
        for stat_name, expected_value in expected_stats.items():
            actual_value = stats.get(stat_name)
            if actual_value == expected_value:
                self.success.append(f"✅ Stat {stat_name}: {actual_value}")
            else:
                self.warnings.append(f"⚠️  Stat {stat_name}: attendu {expected_value}, trouvé {actual_value}")
        
        return all_valid

    def verify_ports(self, config: Dict) -> bool:
        """Vérifie que tous les ports sont uniques et valides"""
        services = config.get("services", {})
        ports = {}
        all_valid = True
        
        for service_id, service_config in services.items():
            port = service_config.get("port")
            if port:
                if port in ports:
                    self.errors.append(f"❌ Port dupliqué {port}: {service_id} et {ports[port]}")
                    all_valid = False
                else:
                    ports[port] = service_id
                    if 9000 <= port <= 9100:
                        self.success.append(f"✅ Port valide: {service_id} sur port {port}")
                    else:
                        self.warnings.append(f"⚠️  Port hors plage standard: {service_id} sur port {port}")
        
        return all_valid

    def verify_bandwidth(self, config: Dict) -> bool:
        """Vérifie que le trafic total correspond aux statistiques"""
        services = config.get("services", {})
        total_bandwidth = 0
        
        for service_id, service_config in services.items():
            bandwidth = service_config.get("monthly_bandwidth_tb", 0)
            total_bandwidth += bandwidth
        
        expected_total = config.get("global_stats", {}).get("monthly_traffic_pb", 0) * 1000
        
        if abs(total_bandwidth - expected_total) < 10:  # Tolérance de 10 TB
            self.success.append(f"✅ Trafic total: {total_bandwidth} TB (attendu ~{expected_total} TB)")
            return True
        else:
            self.warnings.append(f"⚠️  Trafic total: {total_bandwidth} TB (attendu ~{expected_total} TB)")
            return False

    def run_verification(self) -> Tuple[bool, int, int, int]:
        """Exécute toutes les vérifications"""
        print("\n" + "="*70)
        print("VÉRIFICATION D'INTÉGRITÉ DES SERVICES CDN")
        print("="*70 + "\n")
        
        # Charger la configuration
        config = self.load_config()
        if not config:
            print("❌ Impossible de charger la configuration")
            return False, 0, 0, 0
        
        # Exécuter les vérifications
        print("1. Vérification des fichiers...")
        self.verify_files_exist()
        
        print("\n2. Vérification des services...")
        self.verify_services(config)
        
        print("\n3. Vérification de la configuration des services...")
        self.verify_service_config(config)
        
        print("\n4. Vérification des nœuds edge...")
        self.verify_edge_nodes(config)
        
        print("\n5. Vérification des statistiques globales...")
        self.verify_global_stats(config)
        
        print("\n6. Vérification des ports...")
        self.verify_ports(config)
        
        print("\n7. Vérification du trafic...")
        self.verify_bandwidth(config)
        
        # Afficher les résultats
        print("\n" + "="*70)
        print("RÉSULTATS")
        print("="*70 + "\n")
        
        if self.success:
            print(f"✅ SUCCÈS ({len(self.success)}):")
            for msg in self.success[:10]:  # Afficher les 10 premiers
                print(f"   {msg}")
            if len(self.success) > 10:
                print(f"   ... et {len(self.success) - 10} autres")
        
        if self.warnings:
            print(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"   {msg}")
        
        if self.errors:
            print(f"\n❌ ERREURS ({len(self.errors)}):")
            for msg in self.errors:
                print(f"   {msg}")
        
        # Résumé
        print("\n" + "="*70)
        total_checks = len(self.success) + len(self.warnings) + len(self.errors)
        success_rate = (len(self.success) / total_checks * 100) if total_checks > 0 else 0
        
        if self.errors:
            status = "❌ ÉCHEC"
            return False, len(self.success), len(self.warnings), len(self.errors)
        elif self.warnings:
            status = "⚠️  AVERTISSEMENTS"
            return True, len(self.success), len(self.warnings), len(self.errors)
        else:
            status = "✅ SUCCÈS"
            return True, len(self.success), len(self.warnings), len(self.errors)
        
        print(f"Statut: {status}")
        print(f"Taux de succès: {success_rate:.1f}%")
        print(f"Total: {len(self.success)} succès, {len(self.warnings)} avertissements, {len(self.errors)} erreurs")
        print("="*70 + "\n")

def main():
    verifier = CDNVerifier()
    success, successes, warnings, errors = verifier.run_verification()
    
    # Afficher le résumé final
    print("\n" + "="*70)
    print("RÉSUMÉ FINAL")
    print("="*70)
    print(f"✅ Succès: {successes}")
    print(f"⚠️  Avertissements: {warnings}")
    print(f"❌ Erreurs: {errors}")
    
    if errors == 0:
        print("\n✅ TOUS LES SERVICES CDN SONT CORRECTEMENT CONFIGURÉS")
        print("Vous pouvez maintenant lancer: python cdn/services/launch_all_services.py")
        return 0
    else:
        print(f"\n❌ {errors} ERREUR(S) DÉTECTÉE(S)")
        print("Veuillez corriger les erreurs avant de lancer les services")
        return 1

if __name__ == "__main__":
    sys.exit(main())
