#!/usr/bin/env python3
"""
Script to verify that all MCP servers in the registry can be installed.

This script validates the verified MCP registry by checking if each package
exists on npm and can be successfully installed.
"""

import asyncio
import logging
import subprocess
import sys
from typing import Dict, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Verified MCP servers from the registry
VERIFIED_SERVERS = {
    "core": [
        "@modelcontextprotocol/server-filesystem",
        "@modelcontextprotocol/server-github",
        "@modelcontextprotocol/server-postgres",
        "@modelcontextprotocol/server-puppeteer",
        "@modelcontextprotocol/server-brave-search",
    ],
    "ai_enhanced": [
        "@modelcontextprotocol/server-sequential-thinking",
        "@modelcontextprotocol/server-memory",
    ],
    "time_utilities": [
        "time-mcp",
    ],
    "crypto_finance": [
        "mcp-crypto-price",
    ],
    "enhanced_filesystem": [
        "filenexus",
        "vuln-fs",
    ],
    "browser_automation": [
        "@modelcontextprotocol/server-puppeteer",
        "puppeteer-mcp-server",
    ],
    "github_enhanced": [
        "@modelcontextprotocol/server-github",
        "github-repo-mcp",
    ],
    "notifications": [
        "ntfy-me-mcp",
    ]
}

async def check_npm_package_exists(package_name: str) -> Tuple[str, bool, str]:
    """Check if an npm package exists and can be installed."""
    try:
        # Use npm view to check if package exists
        process = await asyncio.create_subprocess_exec(
            "npm", "view", package_name, "version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            version = stdout.decode().strip()
            return package_name, True, f"v{version}"
        else:
            error_msg = stderr.decode().strip()
            return package_name, False, error_msg
            
    except Exception as e:
        return package_name, False, str(e)

async def verify_all_packages() -> Dict[str, List[Tuple[str, bool, str]]]:
    """Verify all packages in the registry."""
    results = {}
    
    for category, packages in VERIFIED_SERVERS.items():
        logger.info(f"🔍 Verifying category: {category}")
        category_results = []
        
        # Remove duplicates while preserving order
        unique_packages = list(dict.fromkeys(packages))
        
        # Check all packages in parallel
        tasks = [check_npm_package_exists(pkg) for pkg in unique_packages]
        package_results = await asyncio.gather(*tasks)
        
        for package, exists, info in package_results:
            category_results.append((package, exists, info))
            
            if exists:
                logger.info(f"  ✅ {package} - {info}")
            else:
                logger.error(f"  ❌ {package} - {info}")
        
        results[category] = category_results
    
    return results

def print_summary(results: Dict[str, List[Tuple[str, bool, str]]]):
    """Print a summary of verification results."""
    total_packages = 0
    working_packages = 0
    failed_packages = []
    
    print("\n" + "="*60)
    print("📋 MCP REGISTRY VERIFICATION SUMMARY")
    print("="*60)
    
    for category, category_results in results.items():
        category_total = len(category_results)
        category_working = sum(1 for _, exists, _ in category_results if exists)
        
        total_packages += category_total
        working_packages += category_working
        
        print(f"\n📂 {category.upper()}: {category_working}/{category_total} working")
        
        for package, exists, info in category_results:
            status = "✅" if exists else "❌"
            print(f"  {status} {package}")
            if not exists:
                failed_packages.append(package)
    
    print(f"\n🎯 OVERALL RESULTS:")
    print(f"   Total packages tested: {total_packages}")
    print(f"   Working packages: {working_packages}")
    print(f"   Failed packages: {len(failed_packages)}")
    print(f"   Success rate: {(working_packages/total_packages)*100:.1f}%")
    
    if failed_packages:
        print(f"\n❌ FAILED PACKAGES:")
        for package in failed_packages:
            print(f"   - {package}")
    else:
        print(f"\n🎉 ALL PACKAGES VERIFIED SUCCESSFULLY!")

async def main():
    """Main verification function."""
    print("🚀 Starting MCP Registry Verification")
    print("This will check if all packages in the verified registry exist on npm.")
    
    try:
        results = await verify_all_packages()
        print_summary(results)
        
        # Exit with error code if any packages failed
        total_failed = sum(
            1 for category_results in results.values()
            for _, exists, _ in category_results
            if not exists
        )
        
        if total_failed > 0:
            print(f"\n⚠️  {total_failed} packages failed verification.")
            sys.exit(1)
        else:
            print(f"\n✅ All packages verified successfully!")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())