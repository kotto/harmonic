#!/usr/bin/env python3
"""
Test Harmonic Audio API - Phase 1
==================================
Tests complets pour le service audio harmonique intégré avec DeepSeek API
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Configuration
API_BASE_URL = "http://localhost:9017"
TEST_TIMEOUT = 30

# Données de test
TEST_CASES = [
    {
        "name": "MP3 128kbps -> FLAC 24/96 (Clarity)",
        "source_format": "mp3_128",
        "target_mode": "hcs_clarity",
        "duration_seconds": 30.0,
        "channels": 2,
        "expected_improvements": {
            "dynamic_range_gain_db": {"min": 80, "max": 100},
            "freq_extension_khz": {"min": 30, "max": 40},
            "quality_score_improvement": {"min": 1.0, "max": 1.8}
        }
    },
    {
        "name": "MP3 320kbps -> Dolby Atmos 9.1.6 (Spatial)",
        "source_format": "mp3_320",
        "target_mode": "hcs_spatial",
        "duration_seconds": 45.0,
        "channels": 2,
        "expected_improvements": {
            "dynamic_range_gain_db": {"min": 40, "max": 60},
            "spatial_channels_added": {"min": 14, "max": 14},
            "quality_score_improvement": {"min": 0.6, "max": 1.5}
        }
    },
    {
        "name": "FLAC 16-bit -> PCM 32/192 Master",
        "source_format": "flac_16",
        "target_mode": "hcs_master",
        "duration_seconds": 60.0,
        "channels": 2,
        "expected_improvements": {
            "dynamic_range_gain_db": {"min": 90, "max": 110},
            "freq_extension_khz": {"min": 70, "max": 80},
            "quality_score_improvement": {"min": 0.4, "max": 1.2}
        }
    },
    {
        "name": "Audio GSM -> FLAC 24/96 Restauré",
        "source_format": "phone_gsm",
        "target_mode": "hcs_restore",
        "duration_seconds": 20.0,
        "channels": 1,
        "expected_improvements": {
            "dynamic_range_gain_db": {"min": 90, "max": 130},
            "freq_extension_khz": {"min": 35, "max": 50},
            "quality_score_improvement": {"min": 2.0, "max": 3.0}
        }
    }
]

class HarmonicAudioAPITester:
    """Testeur complet pour l'API audio harmonique"""
    
    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url
        self.results = []
        self.stats = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "total_time_ms": 0.0,
            "start_time": time.time()
        }
    
    async def test_health_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint /health"""
        print("Test endpoint /health...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/health",
                    timeout=TEST_TIMEOUT
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications
                        checks = [
                            data.get("status") == "healthy",
                            data.get("service") == "Harmonic Audio Service",
                            "timestamp" in data
                        ]
                        
                        success = all(checks)
                        
                        result = {
                            "test": "health_endpoint",
                            "success": success,
                            "status_code": response.status,
                            "data": data,
                            "checks": checks
                        }
                        
                        if success:
                            print("/health: PASS")
                        else:
                            print(f"ECHEC /health: FAIL - {checks}")
                        
                        return result
                    
                    else:
                        print(f"ECHEC /health: FAIL - Status {response.status}")
                        return {
                            "test": "health_endpoint",
                            "success": False,
                            "status_code": response.status,
                            "error": f"Status {response.status}"
                        }
            
            except Exception as e:
                print(f"ECHEC /health: ERROR - {e}")
                return {
                    "test": "health_endpoint",
                    "success": False,
                    "error": str(e)
                }
    
    async def test_stats_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint /stats"""
        print("Test endpoint /stats...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/stats",
                    timeout=TEST_TIMEOUT
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications
                        required_fields = [
                            "service_name", "version", "hcs_available",
                            "total_requests", "successful_requests", "success_rate"
                        ]
                        
                        checks = [
                            all(field in data for field in required_fields),
                            isinstance(data.get("total_requests"), int),
                            isinstance(data.get("success_rate"), (int, float)),
                            "timestamp" in data
                        ]
                        
                        success = all(checks)
                        
                        result = {
                            "test": "stats_endpoint",
                            "success": success,
                            "status_code": response.status,
                            "data": data,
                            "checks": checks
                        }
                        
                        if success:
                            print("/stats: PASS")
                        else:
                            print(f"ECHEC /stats: FAIL - {checks}")
                        
                        return result
                    
                    else:
                        print(f"ECHEC /stats: FAIL - Status {response.status}")
                        return {
                            "test": "stats_endpoint",
                            "success": False,
                            "status_code": response.status,
                            "error": f"Status {response.status}"
                        }
            
            except Exception as e:
                print(f"ECHEC /stats: ERROR - {e}")
                return {
                    "test": "stats_endpoint",
                    "success": False,
                    "error": str(e)
                }
    
    async def test_modes_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint /modes"""
        print("Test endpoint /modes...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{self.base_url}/modes",
                    timeout=TEST_TIMEOUT
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications
                        checks = [
                            "modes" in data,
                            isinstance(data["modes"], list),
                            len(data["modes"]) > 0,
                            all("id" in mode for mode in data["modes"]),
                            all("target_format" in mode for mode in data["modes"]),
                            "timestamp" in data
                        ]
                        
                        success = all(checks)
                        
                        result = {
                            "test": "modes_endpoint",
                            "success": success,
                            "status_code": response.status,
                            "data": data,
                            "checks": checks
                        }
                        
                        if success:
                            print("/modes: PASS")
                            print(f"   Modes disponibles: {[m['id'] for m in data['modes']]}")
                        else:
                            print(f"ECHEC /modes: FAIL - {checks}")
                        
                        return result
                    
                    else:
                        print(f"ECHEC /modes: FAIL - Status {response.status}")
                        return {
                            "test": "modes_endpoint",
                            "success": False,
                            "status_code": response.status,
                            "error": f"Status {response.status}"
                        }
            
            except Exception as e:
                print(f"ECHEC /modes: ERROR - {e}")
                return {
                    "test": "modes_endpoint",
                    "success": False,
                    "error": str(e)
                }
    
    async def test_process_endpoint(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Teste l'endpoint /process avec un cas de test"""
        test_name = test_case["name"]
        print(f"Test endpoint /process: {test_name}...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Préparation des données de test
                form_data = aiohttp.FormData()
                form_data.add_field("source_format", test_case["source_format"])
                form_data.add_field("target_mode", test_case["target_mode"])
                form_data.add_field("duration_seconds", str(test_case["duration_seconds"]))
                form_data.add_field("channels", str(test_case["channels"]))
                form_data.add_field("real_time", "false")
                
                start_time = time.time()
                
                async with session.post(
                    f"{self.base_url}/process",
                    data=form_data,
                    timeout=TEST_TIMEOUT
                ) as response:
                    
                    processing_time_ms = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications de base
                        basic_checks = [
                            data.get("success") == True,
                            "session_id" in data,
                            "source_signature" in data,
                            "upscale_result" in data,
                            "quality_improvement" in data,
                            data.get("processing_time_ms", 0) > 0
                        ]
                        
                        # Vérifications des améliorations
                        quality_improvement = data.get("quality_improvement", {})
                        expected = test_case["expected_improvements"]
                        
                        improvement_checks = []
                        
                        for key, expected_range in expected.items():
                            if key in quality_improvement:
                                value = quality_improvement[key]
                                improvement_checks.append(
                                    expected_range["min"] <= value <= expected_range["max"]
                                )
                        
                        all_checks = basic_checks + improvement_checks
                        success = all(all_checks)
                        
                        result = {
                            "test": f"process_endpoint_{test_case['source_format']}",
                            "success": success,
                            "status_code": response.status,
                            "processing_time_ms": processing_time_ms,
                            "data": data,
                            "checks": {
                                "basic": basic_checks,
                                "improvements": improvement_checks
                            },
                            "expected_improvements": expected,
                            "actual_improvements": quality_improvement
                        }
                        
                        if success:
                            print(f"/process {test_name}: PASS")
                            print(f"   Temps: {processing_time_ms:.1f}ms")
                            print(f"   Session: {data.get('session_id')}")
                            
                            # Affichage des améliorations
                            for key, value in quality_improvement.items():
                                if key in expected:
                                    range_info = expected[key]
                                    print(f"   {key}: {value:.1f} (attendu: {range_info['min']}-{range_info['max']})")
                        
                        else:
                            print(f"ECHEC /process {test_name}: FAIL")
                            print(f"   Basic checks: {basic_checks}")
                            print(f"   Improvement checks: {improvement_checks}")
                        
                        return result
                    
                    else:
                        error_text = await response.text()
                        print(f"ECHEC /process {test_name}: FAIL - Status {response.status}")
                        print(f"   Error: {error_text}")
                        
                        return {
                            "test": f"process_endpoint_{test_case['source_format']}",
                            "success": False,
                            "status_code": response.status,
                            "processing_time_ms": processing_time_ms,
                            "error": f"Status {response.status}: {error_text}"
                        }
            
            except Exception as e:
                print(f"ECHEC /process {test_name}: ERROR - {e}")
                return {
                    "test": f"process_endpoint_{test_case['source_format']}",
                    "success": False,
                    "error": str(e)
                }
    
    async def test_deepseek_enhance_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint /deepseek_enhance"""
        print("Test endpoint /deepseek_enhance...")
        
        async with aiohttp.ClientSession() as session:
            try:
                # Données de test
                request_data = {
                    "prompt": "Améliorer audio MP3 128kbps vers qualité studio FLAC 24bit/96kHz",
                    "enhancement_mode": "harmonic_master",
                    "temperature": 0.0,
                    "max_tokens": 500
                }
                
                headers = {
                    "Content-Type": "application/json"
                }
                
                async with session.post(
                    f"{self.base_url}/deepseek_enhance",
                    json=request_data,
                    headers=headers,
                    timeout=TEST_TIMEOUT
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Vérifications
                        checks = [
                            data.get("success") == True,
                            "enhanced_audio_description" in data,
                            len(data.get("enhanced_audio_description", "")) > 50,
                            "harmonic_parameters" in data,
                            "quality_score" in data,
                            data.get("quality_score", 0) > 0.5
                        ]
                        
                        success = all(checks)
                        
                        result = {
                            "test": "deepseek_enhance_endpoint",
                            "success": success,
                            "status_code": response.status,
                            "data": data,
                            "checks": checks
                        }
                        
                        if success:
                            print("/deepseek_enhance: PASS")
                            print(f"   Score qualité: {data.get('quality_score'):.3f}")
                            print(f"   Temps: {data.get('processing_time_ms'):.1f}ms")
                        else:
                            print(f"ECHEC /deepseek_enhance: FAIL - {checks}")
                        
                        return result
                    
                    else:
                        error_text = await response.text()
                        print(f"ECHEC /deepseek_enhance: FAIL - Status {response.status}")
                        print(f"   Error: {error_text}")
                        
                        return {
                            "test": "deepseek_enhance_endpoint",
                            "success": False,
                            "status_code": response.status,
                            "error": f"Status {response.status}: {error_text}"
                        }
            
            except Exception as e:
                print(f"ECHEC /deepseek_enhance: ERROR - {e}")
                return {
                    "test": "deepseek_enhance_endpoint",
                    "success": False,
                    "error": str(e)
                }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Exécute tous les tests"""
        print("Demarrage des tests Harmonic Audio API")
        print("=" * 60)
        
        start_time = time.time()
        all_results = []
        
        # Test des endpoints de base
        print("\nTests des endpoints de base:")
        print("-" * 40)
        
        health_result = await self.test_health_endpoint()
        all_results.append(health_result)
        
        stats_result = await self.test_stats_endpoint()
        all_results.append(stats_result)
        
        modes_result = await self.test_modes_endpoint()
        all_results.append(modes_result)
        
        # Test de l'endpoint DeepSeek
        print("\nTest amelioration DeepSeek:")
        print("-" * 40)
        
        deepseek_result = await self.test_deepseek_enhance_endpoint()
        all_results.append(deepseek_result)
        
        # Tests de traitement audio
        print("\nTests de traitement audio harmonique:")
        print("-" * 40)
        
        process_results = []
        for test_case in TEST_CASES:
            result = await self.test_process_endpoint(test_case)
            process_results.append(result)
            all_results.append(result)
        
        # Calcul des statistiques
        total_time = time.time() - start_time
        passed_tests = sum(1 for r in all_results if r.get("success") == True)
        failed_tests = sum(1 for r in all_results if r.get("success") == False)
        
        # Rapport final
        print("\n" + "=" * 60)
        print("RAPPORT FINAL DES TESTS")
        print("=" * 60)
        
        print(f"Temps total: {total_time:.2f}s")
        print(f"Tests reussis: {passed_tests}")
        print(f"Tests echoues: {failed_tests}")
        print(f"Taux de reussite: {passed_tests / len(all_results) * 100:.1f}%")
        
        # Détail des améliorations audio
        print("\nAmeliorations Audio Mesurees:")
        print("-" * 40)
        
        for i, test_case in enumerate(TEST_CASES):
            if i < len(process_results) and process_results[i].get("success"):
                data = process_results[i].get("data", {})
                improvements = data.get("quality_improvement", {})
                
                print(f"\n{test_case['name']}:")
                for key, value in improvements.items():
                    if isinstance(value, (int, float)):
                        print(f"  • {key}: {value:.1f}")
        
        # Résumé des performances
        print("\nPerformances:")
        print("-" * 40)
        
        avg_processing_time = sum(
            r.get("processing_time_ms", 0) for r in process_results 
            if r.get("success") and "processing_time_ms" in r
        ) / max(1, len([r for r in process_results if r.get("success")]))
        
        print(f"Temps moyen de traitement: {avg_processing_time:.1f}ms")
        print(f"Latence cible: <2000ms")
        print(f"Amelioration qualite moyenne: {self._calculate_avg_quality_improvement(process_results):.2f} points")
        
        # Vérification des exigences LM Arena
        print("\nVerification Exigences LM Arena:")
        print("-" * 40)
        
        lm_arena_checks = {
            "Latence <2000ms": avg_processing_time < 2000,
            "Amélioration qualité >1.0": self._calculate_avg_quality_improvement(process_results) > 1.0,
            "Dynamic range gain >80dB": self._check_dynamic_range_gain(process_results, 80),
            "Tous les modes supportés": all(r.get("success") for r in process_results)
        }
        
        for check_name, check_result in lm_arena_checks.items():
            status = "PASS" if check_result else "FAIL"
            print(f"{status} {check_name}")
        
        # Résultat global
        all_passed = all(r.get("success") for r in all_results)
        overall_status = "TOUS LES TESTS PASSES" if all_passed else "CERTAINS TESTS ECHOUES"
        
        print("\n" + "=" * 60)
        print(f"{overall_status}")
        print("=" * 60)
        
        return {
            "success": all_passed,
            "total_tests": len(all_results),
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_time_s": total_time,
            "avg_processing_time_ms": avg_processing_time,
            "lm_arena_checks": lm_arena_checks,
            "results": all_results
        }
    
    def _calculate_avg_quality_improvement(self, results: List[Dict[str, Any]]) -> float:
        """Calcule l'amélioration moyenne de qualité"""
        improvements = []
        for result in results:
            if result.get("success") and "data" in result:
                data = result["data"]
                if "quality_improvement" in data:
                    qi = data["quality_improvement"]
                    if "quality_score_improvement" in qi:
                        improvements.append(qi["quality_score_improvement"])
        
        return sum(improvements) / len(improvements) if improvements else 0.0
    
    def _check_dynamic_range_gain(self, results: List[Dict[str, Any]], min_gain: float) -> bool:
        """Vérifie que le gain de dynamic range est suffisant"""
        for result in results:
            if result.get("success") and "data" in result:
                data = result["data"]
                if "quality_improvement" in data:
                    qi = data["quality_improvement"]
                    if "dynamic_range_gain_db" in qi:
                        if qi["dynamic_range_gain_db"] < min_gain:
                            return False
        
        return True

async def main():
    """Fonction principale"""
    
    # Vérification que le service est en cours d'exécution
    print("Verification du service Harmonic Audio...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/health", timeout=5) as response:
                if response.status != 200:
                    print("ECHEC Service Harmonic Audio non disponible")
                    print("Veuillez démarrer le service avec: python harmonic_audio_service.py")
                    return 1
    except Exception as e:
        print(f"Impossible de se connecter au service: {e}")
        print("Veuillez demarrer le service avec: python harmonic_audio_service.py")
        return 1
    
    print("Service Harmonic Audio disponible")
    
    # Exécution des tests
    tester = HarmonicAudioAPITester()
    results = await tester.run_all_tests()
    
    # Sauvegarde des résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"harmonic_audio_test_results_{timestamp}.json"
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\nResultats sauvegardes dans: {filename}")
    
    return 0 if results["success"] else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)