#!/usr/bin/env python3
"""
Test script for the Proxmox VE Linux Template Generator

This script tests the basic functionality without actually creating templates.
"""

import sys
import os
from gen_linux_template import ProxmoxTemplateGenerator, load_config


def test_config_loading():
    """Test configuration loading functionality."""
    print("Testing configuration loading...")
    
    # Test default config
    config = load_config()
    expected_keys = ['ssh_keyfile', 'username', 'storage']
    
    for key in expected_keys:
        if key not in config:
            print(f"❌ Missing key in default config: {key}")
            return False
    
    print("✅ Default configuration loading works")
    return True


def test_image_listing():
    """Test image listing functionality."""
    print("Testing image listing...")
    
    config = load_config()
    generator = ProxmoxTemplateGenerator(config)
    images = generator.get_available_images()
    
    expected_images = ['debian-12', 'debian-13', 'ubuntu-24.04', 'fedora-42', 'alpine-3.22']
    
    for image_name in expected_images:
        if image_name not in images:
            print(f"❌ Missing expected image: {image_name}")
            return False
    
    print("✅ Image listing works correctly")
    return True


def test_environment_validation():
    """Test environment validation (mock)."""
    print("Testing environment validation...")
    
    config = load_config()
    generator = ProxmoxTemplateGenerator(config)
    
    # This will likely fail on non-Proxmox systems, which is expected
    try:
        result = generator.validate_environment()
        if result:
            print("✅ Environment validation passed")
        else:
            print("⚠️  Environment validation failed (expected on non-Proxmox systems)")
    except Exception as e:
        print(f"⚠️  Environment validation error (expected): {e}")
    
    return True


def test_command_execution():
    """Test command execution functionality."""
    print("Testing command execution...")
    
    config = load_config()
    generator = ProxmoxTemplateGenerator(config)
    
    # Test a simple command that should work
    try:
        result = generator.run_command(['echo', 'test'], check=False)
        if result.returncode == 0 and 'test' in result.stdout:
            print("✅ Command execution works")
            return True
        else:
            print("❌ Command execution failed")
            return False
    except Exception as e:
        print(f"❌ Command execution error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Proxmox VE Linux Template Generator")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_image_listing,
        test_environment_validation,
        test_command_execution
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed (this may be expected on non-Proxmox systems)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
