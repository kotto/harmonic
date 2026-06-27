#!/usr/bin/env python3
"""
🤖 Hermes Test Agent - Automated Validation Testing
6-phase testing for Enhanced Harmonic Hybrid AI v2.0 MVP
"""

import time
import json
import asyncio
import aiohttp
import numpy as np
from typing import Dict, Any, List, Tuple
import unittest
from datetime import datetime
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mvp_moe_experts import MOEOrchestrator, ExpertType
from compression_5x import HCVCompression5X
from api_core import app

class TestResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        self.end_time = None
        self.passed = False
        self.error_message = None
        self.metrics = {}
    
    def complete(self, passed: bool, error_message: str = None, metrics: Dict = None):
        self.end_time = time.time()
        self.passed = passed
        self.error_message = error_message
        self.metrics = metrics or {}
    
    @property
    def duration(self) -> float:
        return (self.end_time or time.time()) - self.start_time

class HermesTestAgent:
    """Automated testing agent for 6-phase validation"""
    
    def __init__(self):
        self.moe_orchestrator = MOEOrchestrator()
        self.compression_system = HCVCompression5X()
        self.test_results = []
        self.api_base_url = "http://localhost:8000"
        
        # Test data
        self.math_prompts = [
            "Sarah has 15 apples. She gives 3 to Tom. How many apples left?",
            "If 3x + 7 = 22, what is x?",
            "A train travels 300 miles in 4 hours. What is its average speed?",
            "Calculate 25 × 16",
            "What is the area of a circle with radius 5?"
        ]
        
        self.logic_prompts = [
            "If all humans are mortal and Socrates is human, then Socrates is mortal",
            "Either it's raining or it's sunny. It's not raining, therefore it's sunny",
            "All birds can fly. Penguins are birds. Therefore penguins can fly",
            "If A implies B and B implies C, then A implies C",
            "Some cats are black. All black animals are lucky. Therefore some cats are lucky"
        ]
        
        self.code_prompts = [
            "Write a Python function to sort a list of numbers",
            "Create a JavaScript function to find the maximum in an array",
            "Implement binary search in Python",
            "Write a recursive function to calculate factorial",
            "Create a function to check if a number is prime"
        ]
        
        self.science_prompts = [
            "Explain the process of photosynthesis",
            "What is Einstein's theory of relativity?",
            "How does DNA replication work?",
            "Explain the water cycle",
            "What causes climate change?"
        ]
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all 6 test phases"""
        print("🤖 Hermes Test Agent - Starting 6-Phase Validation")
        print("=" * 60)
        
        # Phase 1: Syntax Validation
        await self._phase1_syntax_validation()
        
        # Phase 2: Semantic Coherence
        await self._phase2_semantic_coherence()
        
        # Phase 3: Performance Benchmarks
        await self._phase3_performance_benchmarks()
        
        # Phase 4: Robustness Edge Cases
        await self._phase4_robustness_testing()
        
        # Phase 5: Scalability Load Testing
        await self._phase5_scalability_testing()
        
        # Phase 6: Regression Testing
        await self._phase6_regression_testing()
        
        # Generate final report
        return self._generate_test_report()
    
    async def _phase1_syntax_validation(self):
        """Phase 1: Validate syntax and basic functionality"""
        print("\n📝 Phase 1: Syntax Validation")
        print("-" * 40)
        
        # Test MOE orchestrator initialization
        result = TestResult("MOE Initialization")
        try:
            orchestrator = MOEOrchestrator()
            assert orchestrator is not None
            assert len(orchestrator.router.experts) == 4
            result.complete(True, metrics={"experts_count": len(orchestrator.router.experts)})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test compression system initialization
        result = TestResult("Compression System Initialization")
        try:
            compressor = HCVCompression5X()
            assert compressor is not None
            assert compressor.target_compression_ratio == 5.0
            result.complete(True, metrics={"target_ratio": compressor.target_compression_ratio})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test expert response structure
        result = TestResult("Expert Response Structure")
        try:
            response = self.moe_orchestrator.process_request("Test prompt")
            required_fields = ['prompt', 'synthesized_response', 'expert_responses', 'selected_experts']
            for field in required_fields:
                assert field in response
            result.complete(True, metrics={"fields_count": len(response)})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 1 Complete: {sum(1 for r in self.test_results[-3:] if r.passed)}/3 tests passed")
    
    async def _phase2_semantic_coherence(self):
        """Phase 2: Test semantic coherence and quality"""
        print("\n🧠 Phase 2: Semantic Coherence")
        print("-" * 40)
        
        # Test math expert coherence
        result = TestResult("Math Expert Coherence")
        try:
            prompt = "What is 15 + 27?"
            response = self.moe_orchestrator.process_request(prompt)
            
            # Check if math expert was selected
            assert any('math' in expert for expert in response['selected_experts'])
            
            # Check if response contains calculation
            content = response['synthesized_response'].lower()
            assert any(word in content for word in ['calculate', 'solution', 'answer', '42'])
            
            result.complete(True, metrics={
                "experts_used": response['selected_experts'],
                "response_length": len(response['synthesized_response'])
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test logic expert coherence
        result = TestResult("Logic Expert Coherence")
        try:
            prompt = "If all A are B and all B are C, then all A are C"
            response = self.moe_orchestrator.process_request(prompt)
            
            # Check if logic expert was selected
            assert any('logic' in expert for expert in response['selected_experts'])
            
            # Check for logical reasoning indicators
            content = response['synthesized_response'].lower()
            assert any(word in content for word in ['logic', 'reasoning', 'deduction', 'valid'])
            
            result.complete(True, metrics={"confidence": self._calculate_avg_confidence(response)})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test code expert coherence
        result = TestResult("Code Expert Coherence")
        try:
            prompt = "Write a Python function to sort a list"
            response = self.moe_orchestrator.process_request(prompt)
            
            # Check if code expert was selected
            assert any('code' in expert for expert in response['selected_experts'])
            
            # Check for code-related terms
            content = response['synthesized_response'].lower()
            assert any(word in content for word in ['python', 'function', 'code', 'algorithm'])
            
            result.complete(True, metrics={"has_code_terms": True})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 2 Complete: {sum(1 for r in self.test_results[-3:] if r.passed)}/3 tests passed")
    
    async def _phase3_performance_benchmarks(self):
        """Phase 3: Performance benchmarking"""
        print("\n⚡ Phase 3: Performance Benchmarks")
        print("-" * 40)
        
        # Test response time
        result = TestResult("Response Time Benchmark")
        try:
            times = []
            for _ in range(10):
                start = time.time()
                self.moe_orchestrator.process_request("Test performance prompt")
                times.append(time.time() - start)
            
            avg_time = np.mean(times)
            max_time = np.max(times)
            
            # Performance criteria: < 2 seconds average
            passed = avg_time < 2.0
            
            result.complete(passed, None if passed else f"Average time {avg_time:.3f}s exceeds 2s limit", {
                "avg_time": avg_time,
                "max_time": max_time,
                "min_time": np.min(times)
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test compression performance
        result = TestResult("Compression Performance")
        try:
            test_data = {
                'expert_type': 'test',
                'weights': {'layer1': np.random.randn(100, 50)},
                'knowledge_base': ['test knowledge'] * 100,
                'metadata': {'version': 'test'}
            }
            
            start = time.time()
            compression_result = self.compression_system.compress_expert(test_data)
            compression_time = time.time() - start
            
            # Check compression ratio
            ratio = compression_result['metrics']['compression_ratio']
            passed = ratio >= 3.0 and compression_time < 1.0
            
            result.complete(passed, None if passed else f"Ratio {ratio:.2f}x or time {compression_time:.3f}s insufficient", {
                "compression_ratio": ratio,
                "compression_time": compression_time,
                "integrity_score": compression_result['metrics']['integrity_score']
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test memory usage
        result = TestResult("Memory Usage")
        try:
            import psutil
            process = psutil.Process()
            
            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Process multiple requests
            for i in range(50):
                self.moe_orchestrator.process_request(f"Test prompt {i}")
            
            # Peak memory
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - baseline_memory
            
            # Memory criteria: < 100MB increase
            passed = memory_increase < 100
            
            result.complete(passed, None if passed else f"Memory increase {memory_increase:.1f}MB exceeds 100MB", {
                "baseline_memory_mb": baseline_memory,
                "peak_memory_mb": peak_memory,
                "memory_increase_mb": memory_increase
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 3 Complete: {sum(1 for r in self.test_results[-3:] if r.passed)}/3 tests passed")
    
    async def _phase4_robustness_testing(self):
        """Phase 4: Robustness and edge case testing"""
        print("\n🛡️ Phase 4: Robustness Testing")
        print("-" * 40)
        
        # Test empty prompt
        result = TestResult("Empty Prompt Handling")
        try:
            response = self.moe_orchestrator.process_request("")
            assert response is not None
            assert 'synthesized_response' in response
            result.complete(True, metrics={"response_length": len(response['synthesized_response'])})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test very long prompt
        result = TestResult("Long Prompt Handling")
        try:
            long_prompt = "Test " * 1000  # 5000 characters
            response = self.moe_orchestrator.process_request(long_prompt)
            assert response is not None
            result.complete(True, metrics={"prompt_length": len(long_prompt)})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test special characters
        result = TestResult("Special Characters Handling")
        try:
            special_prompt = "Test with émojis 🚀 and 特殊字符 and العربية"
            response = self.moe_orchestrator.process_request(special_prompt)
            assert response is not None
            result.complete(True, metrics={"has_special_chars": True})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test malformed input
        result = TestResult("Malformed Input Handling")
        try:
            # This should not crash the system
            response = self.moe_orchestrator.process_request("🔥💯🎯" * 100)
            assert response is not None
            result.complete(True, metrics={"handled_unicode": True})
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 4 Complete: {sum(1 for r in self.test_results[-4:] if r.passed)}/4 tests passed")
    
    async def _phase5_scalability_testing(self):
        """Phase 5: Scalability and load testing"""
        print("\n📈 Phase 5: Scalability Testing")
        print("-" * 40)
        
        # Test concurrent requests
        result = TestResult("Concurrent Request Handling")
        try:
            async def process_single_request(prompt):
                return self.moe_orchestrator.process_request(prompt)
            
            # Run 20 concurrent requests
            tasks = [
                process_single_request(f"Concurrent test {i}")
                for i in range(20)
            ]
            
            start = time.time()
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start
            
            # All requests should complete successfully
            assert len(responses) == 20
            assert all(r is not None for r in responses)
            
            avg_concurrent_time = total_time / 20
            
            result.complete(True, metrics={
                "concurrent_requests": 20,
                "total_time": total_time,
                "avg_time_per_request": avg_concurrent_time
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test memory under load
        result = TestResult("Memory Under Load")
        try:
            import psutil
            process = psutil.Process()
            
            baseline_memory = process.memory_info().rss / 1024 / 1024
            
            # Process 100 requests sequentially
            for i in range(100):
                self.moe_orchestrator.process_request(f"Load test {i}")
            
            peak_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = peak_memory - baseline_memory
            
            # Should handle 100 requests without excessive memory growth
            passed = memory_increase < 200
            
            result.complete(passed, None if passed else f"Memory growth {memory_increase:.1f}MB too high", {
                "requests_processed": 100,
                "memory_increase_mb": memory_increase
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 5 Complete: {sum(1 for r in self.test_results[-2:] if r.passed)}/2 tests passed")
    
    async def _phase6_regression_testing(self):
        """Phase 6: Regression testing"""
        print("\n🔄 Phase 6: Regression Testing")
        print("-" * 40)
        
        # Test core functionality still works
        result = TestResult("Core Functionality Regression")
        try:
            # Test all expert types
            test_cases = [
                ("Math test", "Calculate 2 + 2", "mathematical_reasoning"),
                ("Logic test", "If A then B", "logical_deduction"),
                ("Code test", "Write function", "coding_algorithms"),
                ("Science test", "Explain physics", "scientific_knowledge")
            ]
            
            passed_cases = 0
            for name, prompt, expected_expert in test_cases:
                response = self.moe_orchestrator.process_request(prompt)
                if response and 'selected_experts' in response:
                    if any(expected_expert in expert for expert in response['selected_experts']):
                        passed_cases += 1
            
            passed = passed_cases == len(test_cases)
            
            result.complete(passed, None if passed else f"Only {passed_cases}/{len(test_cases)} cases passed", {
                "passed_cases": passed_cases,
                "total_cases": len(test_cases)
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        # Test compression still works
        result = TestResult("Compression Regression")
        try:
            test_data = {'expert_type': 'test', 'data': 'test data'}
            compression_result = self.compression_system.compress_expert(test_data)
            
            # Basic checks
            assert 'compressed_data' in compression_result
            assert 'metrics' in compression_result
            assert compression_result['metrics']['compression_ratio'] > 1.0
            
            result.complete(True, metrics={
                "compression_ratio": compression_result['metrics']['compression_ratio']
            })
        except Exception as e:
            result.complete(False, str(e))
        self.test_results.append(result)
        
        print(f"✅ Phase 6 Complete: {sum(1 for r in self.test_results[-2:] if r.passed)}/2 tests passed")
    
    def _calculate_avg_confidence(self, response: Dict[str, Any]) -> float:
        """Calculate average confidence from expert responses"""
        confidences = [resp.get('confidence', 0) for resp in response.get('expert_responses', [])]
        return np.mean(confidences) if confidences else 0.0
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.passed)
        failed_tests = total_tests - passed_tests
        
        # Group by phase
        phase_results = {}
        current_phase = 1
        phase_start = 0
        
        for i, result in enumerate(self.test_results):
            if i == 3:  # End of Phase 1
                phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:i]
                current_phase += 1
                phase_start = i
            elif i == 6:  # End of Phase 2
                phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:i]
                current_phase += 1
                phase_start = i
            elif i == 9:  # End of Phase 3
                phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:i]
                current_phase += 1
                phase_start = i
            elif i == 13:  # End of Phase 4
                phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:i]
                current_phase += 1
                phase_start = i
            elif i == 15:  # End of Phase 5
                phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:i]
                current_phase += 1
                phase_start = i
        
        # Add remaining tests (Phase 6)
        if phase_start < len(self.test_results):
            phase_results[f"Phase_{current_phase}"] = self.test_results[phase_start:]
        
        # Calculate phase statistics
        phase_stats = {}
        for phase_name, results in phase_results.items():
            phase_passed = sum(1 for r in results if r.passed)
            phase_total = len(results)
            phase_stats[phase_name] = {
                "passed": phase_passed,
                "total": phase_total,
                "success_rate": phase_passed / phase_total if phase_total > 0 else 0,
                "avg_duration": np.mean([r.duration for r in results])
            }
        
        # Performance metrics
        all_durations = [r.duration for r in self.test_results]
        performance_metrics = {
            "total_test_time": sum(all_durations),
            "avg_test_duration": np.mean(all_durations),
            "max_test_duration": np.max(all_durations),
            "min_test_duration": np.min(all_durations)
        }
        
        return {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "overall_success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "test_timestamp": datetime.now().isoformat()
            },
            "phase_statistics": phase_stats,
            "performance_metrics": performance_metrics,
            "failed_tests": [
                {
                    "test_name": result.test_name,
                    "error": result.error_message,
                    "duration": result.duration
                }
                for result in self.test_results if not result.passed
            ],
            "detailed_results": [
                {
                    "test_name": result.test_name,
                    "passed": result.passed,
                    "duration": result.duration,
                    "metrics": result.metrics,
                    "error": result.error_message
                }
                for result in self.test_results
            ]
        }

# Standalone test runner
async def main():
    """Main test execution"""
    agent = HermesTestAgent()
    report = await agent.run_all_tests()
    
    print("\n" + "="*60)
    print("📊 FINAL TEST REPORT")
    print("="*60)
    
    summary = report["test_summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed_tests']}")
    print(f"Failed: {summary['failed_tests']}")
    print(f"Success Rate: {summary['overall_success_rate']:.1%}")
    
    print("\n📈 Phase Results:")
    for phase, stats in report["phase_statistics"].items():
        status = "✅" if stats["success_rate"] == 1.0 else "⚠️" if stats["success_rate"] >= 0.8 else "❌"
        print(f"{status} {phase}: {stats['passed']}/{stats['total']} ({stats['success_rate']:.1%})")
    
    if report["failed_tests"]:
        print("\n❌ Failed Tests:")
        for failed in report["failed_tests"]:
            print(f"  - {failed['test_name']}: {failed['error']}")
    
    print(f"\n⏱️ Total Test Time: {report['performance_metrics']['total_test_time']:.2f}s")
    
    # Save report to file
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print("📁 Detailed report saved to: test_report.json")
    
    return report["test_summary"]["overall_success_rate"] >= 0.8

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
