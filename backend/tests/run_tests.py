#!/usr/bin/env python3
"""
Test runner for the unified test suite.
"""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the unified test suite."""
    
    backend_dir = Path(__file__).parent.parent
    
    print("🧪 Running Unified Backend Test Suite")
    print("=" * 50)
    
    # Check if pytest is available
    try:
        import pytest
        print("✓ pytest is available")
    except ImportError:
        print("❌ pytest not found. Install with: pip install pytest pytest-asyncio")
        return False
    
    # Run pytest
    try:
        print("\n🚀 Running tests...")
        
        # Change to backend directory for proper imports
        import os
        original_cwd = os.getcwd()
        os.chdir(backend_dir)
        
        # Run pytest with asyncio support
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v",
            "--tb=short",
            "-x"  # Stop on first failure
        ], capture_output=True, text=True)
        
        # Restore working directory
        os.chdir(original_cwd)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("\n🎉 All tests passed!")
            return True
        else:
            print(f"\n❌ Tests failed with return code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def run_quick_validation():
    """Run quick validation without pytest."""
    
    print("🔍 Running Quick Validation (without pytest)")
    print("=" * 50)
    
    try:
        # Test configuration loading
        print("\n1. Testing configuration...")
        from config import get_settings
        settings = get_settings()
        print(f"   ✓ App: {settings.app.name} v{settings.app.version}")
        
        # Test container creation
        print("\n2. Testing dependency injection...")
        from core import get_container
        container = get_container()
        print("   ✓ Container created successfully")
        
        # Test service creation
        print("\n3. Testing core services...")
        model_service = container.model_service
        print("   ✓ Model service")
        
        storage_service = container.storage_service
        print("   ✓ Storage service")
        
        source_repo = container.source_repository
        print("   ✓ Source repository")
        
        # Test API import
        print("\n4. Testing API module...")
        from api.main import app
        print("   ✓ API application")
        
        print("\n🎉 Quick validation passed!")
        print("\nArchitecture Summary:")
        print("✅ Unified configuration system")
        print("✅ Dependency injection container")
        print("✅ Modular service implementations")
        print("✅ Clean interface abstractions")
        print("✅ API application ready")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Backend Test Suite")
    print("Choose test mode:")
    print("1. Full pytest suite (recommended)")
    print("2. Quick validation (fallback)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        success = run_tests()
    elif choice == "2":
        success = run_quick_validation()
    else:
        print("Invalid choice. Running quick validation...")
        success = run_quick_validation()
    
    if success:
        print("\n✅ Testing completed successfully!")
    else:
        print("\n❌ Testing failed. Please check the output above.")
        sys.exit(1)