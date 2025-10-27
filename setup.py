"""
Setup script for College Basketball Data API wrapper.
Run this script to configure your API key and test the connection.
"""

#!/usr/bin/env python3

import os
import sys
from config import setup_api_key, Config
from cbb_api_wrapper import CollegeBasketballAPI, APITester


def main():
    """Main setup and testing function."""
    print("🏀 College Basketball Data API Wrapper Setup")
    print("=" * 50)
    
    # Check if API key is already set
    api_key = os.getenv('CBB_API_KEY')
    
    if not api_key:
        print("No API key found in environment variables.")
        print("You can:")
        print("1. Set it up interactively now")
        print("2. Set it manually in your environment")
        print()
        
        choice = input("Would you like to set up your API key now? (y/n): ").strip().lower()
        
        if choice == 'y':
            if setup_api_key():
                print("\n✅ API key setup complete!")
                print("Please restart your terminal or run: source ~/.cbb_api_env")
                return
            else:
                print("❌ API key setup failed.")
                return
        else:
            print("Please set your API key manually:")
            print("export CBB_API_KEY='your_api_key_here'")
            return
    
    print(f"✅ API key found: {api_key[:8]}...")
    
    # Test the API
    print("\n🧪 Testing API connection...")
    try:
        api = CollegeBasketballAPI()
        
        if api.test_connection():
            print("✅ API connection successful!")
            
            # Ask if user wants to run comprehensive tests
            choice = input("\nWould you like to run comprehensive endpoint tests? (y/n): ").strip().lower()
            
            if choice == 'y':
                print("\n🔍 Running comprehensive API tests...")
                tester = APITester(api)
                results = tester.test_all_endpoints()
                
                # Save results
                import json
                with open('api_test_results.json', 'w') as f:
                    json.dump(results, f, indent=2)
                
                print(f"\n📊 Test results saved to api_test_results.json")
            else:
                print("Skipping comprehensive tests.")
                print("You can run them later with: python cbb_api_wrapper.py")
                
        else:
            print("❌ API connection failed. Please check your API key.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Please check your API key and try again.")


if __name__ == "__main__":
    main()
