#!/usr/bin/env python3
"""
🚀 Enhanced Harmonic Hybrid AI v2.0 - MVP Runner
Quick start script for the MVP system
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'numpy', 
        'aiohttp', 'psutil', 'pytest', 'pytest-asyncio'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")
    
    if missing_packages:
        print(f"\n⚠️ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("✅ Dependencies installed")
    else:
        print("✅ All dependencies satisfied")

def run_tests():
    """Run the validation tests"""
    print("\n🤖 Running Hermes Test Agent...")
    
    try:
        result = subprocess.run([sys.executable, "test_validation.py"], 
                              capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def start_api_server():
    """Start the API server"""
    print("\n🚀 Starting API Server...")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Metrics: http://localhost:8000/metrics")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        import uvicorn
        from api_core import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def run_demo():
    """Run a quick demo of the system"""
    print("\n🎯 Running Quick Demo...")
    
    try:
        from mvp_moe_experts import MOEOrchestrator
        
        orchestrator = MOEOrchestrator()
        
        demo_prompts = [
            "Calculate 15 + 27",
            "If all A are B and all B are C, then all A are C",
            "Write a Python function to sort a list",
            "Explain photosynthesis"
        ]
        
        for i, prompt in enumerate(demo_prompts, 1):
            print(f"\n🧪 Demo {i}: {prompt}")
            print("-" * 40)
            
            result = orchestrator.process_request(prompt)
            
            print(f"📊 Experts: {', '.join(result['selected_experts'])}")
            print(f"⚡ Time: {result['total_processing_time']:.3f}s")
            print(f"📝 Response: {result['synthesized_response'][:200]}...")
        
        print("\n✅ Demo completed successfully")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def show_menu():
    """Show interactive menu"""
    print("\n🌊 Enhanced Harmonic Hybrid AI v2.0 - MVP")
    print("=" * 50)
    print("1. 🧪 Run Tests")
    print("2. 🎯 Run Demo")
    print("3. 🚀 Start API Server")
    print("4. 🔧 Check Dependencies")
    print("5. 📋 Show System Info")
    print("6. 🚪 Exit")
    print("=" * 50)

def show_system_info():
    """Show system information"""
    print("\n📋 System Information")
    print("-" * 30)
    
    try:
        import psutil
        import platform
        
        print(f"OS: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print(f"CPU Cores: {psutil.cpu_count()}")
        print(f"Memory: {psutil.virtual_memory().total / 1024**3:.1f} GB")
        print(f"Disk: {psutil.disk_usage('/').total / 1024**3:.1f} GB")
        
    except Exception as e:
        print(f"Error getting system info: {e}")
    
    # Check our components
    print("\n🧠 Components Status:")
    try:
        from mvp_moe_experts import MOEOrchestrator
        print("✅ MOE System")
    except:
        print("❌ MOE System")
    
    try:
        from compression_5x import HCVCompression5X
        print("✅ Compression System")
    except:
        print("❌ Compression System")
    
    try:
        from api_core import app
        print("✅ API Core")
    except:
        print("❌ API Core")

def main():
    """Main entry point"""
    print("🌊 Enhanced Harmonic Hybrid AI v2.0 - MVP Runner")
    
    # Check dependencies first
    check_dependencies()
    
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == "1":
                run_tests()
            elif choice == "2":
                run_demo()
            elif choice == "3":
                start_api_server()
            elif choice == "4":
                check_dependencies()
            elif choice == "5":
                show_system_info()
            elif choice == "6":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            run_tests()
        elif command == "demo":
            run_demo()
        elif command == "server":
            start_api_server()
        elif command == "check":
            check_dependencies()
        elif command == "info":
            show_system_info()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, demo, server, check, info")
    else:
        main()
