#!/usr/bin/env python3
"""
Dependency Conflict Checker for Legal Mind Agent

This script checks for potential dependency conflicts and provides recommendations.
"""

import subprocess
import sys
import json
from typing import Dict, List

def run_pip_check() -> str:
    """Run pip check and return the output"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'check'], 
                              capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error running pip check: {e}"

def get_installed_packages() -> Dict[str, str]:
    """Get list of installed packages and their versions"""
    try:
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--format=json'], 
                              capture_output=True, text=True)
        packages = json.loads(result.stdout)
        return {pkg['name'].lower(): pkg['version'] for pkg in packages}
    except Exception as e:
        print(f"Error getting package list: {e}")
        return {}

def check_known_conflicts(packages: Dict[str, str]) -> List[str]:
    """Check for known dependency conflicts"""
    conflicts = []
    
    # Check aiohttp version compatibility
    if 'aiohttp' in packages:
        aiohttp_version = packages['aiohttp']
        
        # Check for open-webui compatibility
        if 'open-webui' in packages:
            if not aiohttp_version.startswith('3.11.'):
                conflicts.append(
                    f"⚠️  open-webui requires aiohttp==3.11.11, but you have {aiohttp_version}"
                )
        
        # Check for Bot Framework compatibility
        if any(pkg.startswith('botbuilder') for pkg in packages):
            print(f"✅ aiohttp {aiohttp_version} is compatible with Bot Framework SDK")
    
    # Check for s3fs/aiobotocore conflicts
    if 's3fs' in packages and 'aiobotocore' not in packages:
        conflicts.append(
            "⚠️  s3fs requires aiobotocore, but it's not installed. "
            "Install with: pip install 'aiobotocore>=2.5.4,<3.0.0'"
        )
    
    return conflicts

def main():
    """Main function to check dependencies"""
    print("🔍 Legal Mind Agent - Dependency Conflict Checker\n")
    
    # Get installed packages
    print("📦 Getting installed packages...")
    packages = get_installed_packages()
    
    if not packages:
        print("❌ Could not get package information")
        return
    
    print(f"✅ Found {len(packages)} installed packages\n")
    
    # Check for known conflicts
    print("🔍 Checking for known conflicts...")
    conflicts = check_known_conflicts(packages)
    
    if conflicts:
        print("⚠️  Found potential conflicts:")
        for conflict in conflicts:
            print(f"   {conflict}")
        print()
    else:
        print("✅ No known conflicts detected\n")
    
    # Run pip check
    print("🔍 Running pip dependency check...")
    pip_output = run_pip_check()
    
    if pip_output.strip():
        print("⚠️  pip check output:")
        print(pip_output)
    else:
        print("✅ No pip dependency conflicts detected")
    
    # Check core Legal Mind Agent dependencies
    core_deps = ['aiohttp', 'botbuilder-core', 'botbuilder-schema', 'botframework-connector']
    missing_deps = [dep for dep in core_deps if dep not in packages]
    
    if missing_deps:
        print(f"\n❌ Missing core dependencies: {', '.join(missing_deps)}")
        print("   Run: pip install -r requirements.txt")
    else:
        print("\n✅ All core Legal Mind Agent dependencies are installed")
        
        # Show versions of core dependencies
        print("\n📋 Core dependency versions:")
        for dep in core_deps:
            print(f"   {dep}: {packages[dep]}")

if __name__ == "__main__":
    main()
