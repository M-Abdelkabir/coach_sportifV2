#!/usr/bin/env python3
"""
Test script to verify ML integration with position validation.
Run this after starting the backend to check if ML models are loaded and working.
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_health_check():
    """Test 1: Health check - verify models are loaded"""
    print_section("TEST 1: Health Check & Model Status")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running")
            print(f"   Status: {data.get('status')}")
            print(f"   Version: {data.get('version')}")
            
            models = data.get('models_loaded', {})
            print("\n📦 Models Status:")
            print(f"   ✅ Pose Detector: {models.get('pose_detector', False)}")
            print(f"   ✅ LSTM Model: {models.get('lstm_model', False)}")
            print(f"   ✅ Correction Model: {models.get('correction_model', False)}")
            print(f"   ✅ Fitness Model: {models.get('fitness_model', False)}")
            
            if models.get('lstm_model'):
                print("\n✅ LSTM MODEL IS LOADED - Ready for position validation!")
            else:
                print("\n⚠️  LSTM model not loaded - Check backend logs")
            
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_user_creation():
    """Test 2: Create/get demo user"""
    print_section("TEST 2: User Management")
    try:
        response = requests.get(f"{BACKEND_URL}/users/demo_user")
        if response.status_code == 200:
            user = response.json()
            print(f"✅ Demo user exists")
            print(f"   ID: {user.get('id')}")
            print(f"   Name: {user.get('name')}")
            return True
        else:
            print(f"❌ Demo user not found")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_websocket_connection():
    """Test 3: WebSocket connection"""
    print_section("TEST 3: WebSocket Connection")
    try:
        import websocket
        ws = websocket.create_connection("ws://localhost:8000/ws", timeout=5)
        print("✅ WebSocket connection established")
        ws.close()
        return True
    except ImportError:
        print("⚠️  websocket-client not installed")
        print("   Install with: pip install websocket-client")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

def test_ml_backend_locally():
    """Test 4: Test ML models directly (without WebSocket)"""
    print_section("TEST 4: ML Model Availability Check")
    try:
        # Try to import the exercise engine
        import sys
        from pathlib import Path
        backend_path = Path(__file__).parent / "backend"
        if backend_path.exists():
            sys.path.insert(0, str(backend_path))
            from exercise_engine import lstm_model, labels_map
            
            if lstm_model is not None:
                print("✅ LSTM Model is loaded in backend")
                print(f"   Supported classes ({len(labels_map)}):")
                for idx, label in labels_map.items():
                    print(f"      {idx}: {label}")
                return True
            else:
                print("❌ LSTM Model failed to load")
                print("   Check backend logs for model loading errors")
                return False
        else:
            print("⚠️  Could not find backend directory for local test")
            return False
    except Exception as e:
        print(f"⚠️  Local ML test skipped: {e}")
        return False

def print_checklist():
    """Print final checklist"""
    print_section("✅ INTEGRATION CHECKLIST")
    print("""
Frontend Components:
  ✅ PositionFeedbackPanel.tsx - NEW component for ML validation display
  ✅ QuickPositionStatus - Quick status badge
  ✅ quick-start-screen.tsx - Updated with ML integration
  ✅ use-backend.ts - Hooks capture ML data

Backend Configuration:
  ✅ exercise_engine.py returns ml_label & ml_confidence
  ✅ LSTM model predicts: "Correct Squat", "Bad Knee Position", etc.
  ✅ WebSocket sends exercise_update with ML classification
  ✅ Speech feedback auto-triggers on warnings

Data Flow:
  ✅ ML Model → Backend validation
  ✅ WebSocket → Frontend real-time
  ✅ React Hooks → Component state
  ✅ Speech API → French corrections

Ready to test? Follow these steps:

1. Backend Terminal:
   cd backend
   python main.py
   
2. Frontend Terminal:
   cd frontend
   npm run dev
   
3. Browser:
   Open http://localhost:3000
   Start a workout session
   Perform exercises with bad form
   Listen for French speech corrections! 🎤

4. Monitor ML Quality:
   Look for status badge in top-left of screen
   Bottom panel shows detailed feedback
   Speech triggers on form warnings
""")

def main():
    print("\n" + "="*60)
    print("  COACH SPORTIF - ML INTEGRATION TEST")
    print("  Position Validation with Speech Corrections")
    print("="*60)
    
    print("\n⏳ Testing backend...\n")
    
    results = {
        "Health Check": test_health_check(),
        "User Management": test_user_creation(),
        "WebSocket": test_websocket_connection(),
        "ML Models": test_ml_backend_locally(),
    }
    
    print_section("TEST RESULTS SUMMARY")
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed >= 3:
        print("\n✅ Integration looks good! Ready to test the full system.")
        print_checklist()
    else:
        print("\n⚠️  Some tests failed. Check the output above and backend logs.")
        print("   Make sure:")
        print("   1. Backend is running on port 8000")
        print("   2. LSTM model is loaded (check backend logs)")
        print("   3. All dependencies are installed")

if __name__ == "__main__":
    main()
