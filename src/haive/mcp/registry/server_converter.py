#!/usr/bin/env python3
"""Server Registry Converter for Phase 3+.

This module converts GitHub-based server entries from the 1900+ server database
into npm package format for the MCP Manager registry.

Features:
- Converts GitHub URLs to potential npm package names
- Validates npm package existence
- Generates category mappings
- Creates installable server lists

Usage:
    from haive.mcp.registry.server_converter import ServerConverter
    
    converter = ServerConverter()
    
    # Convert known patterns
    npm_packages = await converter.convert_github_to_npm_batch([
        "https://github.com/modelcontextprotocol/server-time",
        "https://github.com/some-org/mcp-server-custom"
    ])
    
    # Validate packages exist on npm
    valid_packages = await converter.validate_npm_packages(npm_packages)
"""

import asyncio
import json
import logging
import re
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass

import aiohttp
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


@dataclass
class ServerConversion:
    """Result of converting a GitHub server to npm package format."""
    github_url: str
    potential_npm_packages: List[str]
    validated_package: Optional[str] = None
    category_guess: Optional[str] = None
    confidence: float = 0.0


class NPMPackageValidator:
    """Validates whether npm packages exist and are installable."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, bool] = {}
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def package_exists(self, package_name: str) -> bool:
        """Check if an npm package exists."""
        if package_name in self._cache:
            return self._cache[package_name]
        
        try:
            # Check npm registry
            url = f"https://registry.npmjs.org/{package_name}"
            async with self.session.get(url) as response:
                exists = response.status == 200
                self._cache[package_name] = exists
                return exists
                
        except Exception as e:
            logger.warning(f"Error checking package {package_name}: {e}")
            self._cache[package_name] = False
            return False
    
    async def validate_batch(self, package_names: List[str]) -> Dict[str, bool]:
        """Validate multiple packages in parallel."""
        tasks = [self.package_exists(name) for name in package_names]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        validated = {}
        for package_name, result in zip(package_names, results):
            if isinstance(result, Exception):
                validated[package_name] = False
            else:
                validated[package_name] = result
                
        return validated


class ServerConverter:
    """Converts server entries from GitHub format to npm package format."""
    
    def __init__(self):
        self.validator = NPMPackageValidator()
        
        # Common patterns for npm package conversion
        self.conversion_patterns = [
            # Official modelcontextprotocol packages
            (r"github\.com/modelcontextprotocol/server-(\w+)", r"@modelcontextprotocol/server-\1"),
            
            # Community packages with standard naming
            (r"github\.com/[\w-]+/mcp-server-(\w+)", r"mcp-server-\1"),
            (r"github\.com/[\w-]+/(\w+)-mcp-server", r"\1-mcp-server"),
            (r"github\.com/[\w-]+/(\w+)-mcp", r"\1-mcp"),
            
            # Custom org packages
            (r"github\.com/([\w-]+)/mcp-(\w+)", r"@\1/mcp-\2"),
        ]
        
        # Category mapping based on server names and descriptions
        self.category_mapping = {
            # Development
            "filesystem": "development",
            "git": "development", 
            "github": "development",
            "gitlab": "development",
            "docker": "development",
            "kubernetes": "development",
            "aws": "development",
            
            # Data
            "postgres": "data",
            "mysql": "data",
            "sqlite": "data",
            "mongodb": "data",
            "s3": "data",
            "gdrive": "data",
            "memory": "data",
            
            # Productivity  
            "search": "productivity",
            "brave": "productivity",
            "google": "productivity",
            "slack": "productivity",
            "notion": "productivity",
            "calendar": "productivity",
            "time": "productivity",
            
            # AI
            "thinking": "ai",
            "sequential": "ai",
            "image": "ai",
            "speech": "ai",
            "text": "ai",
            
            # Web APIs
            "twitter": "web_apis",
            "reddit": "web_apis", 
            "youtube": "web_apis",
            "stripe": "web_apis",
            "analytics": "web_apis",
            
            # Security
            "nmap": "security",
            "whois": "security",
            "ssl": "security",
            "vault": "security",
            "1password": "security",
        }
    
    def convert_github_to_npm_candidates(self, github_url: str) -> List[str]:
        """Convert a GitHub URL to potential npm package names."""
        candidates = []
        
        # Try each conversion pattern
        for pattern, replacement in self.conversion_patterns:
            match = re.search(pattern, github_url)
            if match:
                npm_name = re.sub(pattern, replacement, github_url)
                candidates.append(npm_name)
        
        # Extract repo name and create generic candidates
        repo_match = re.search(r"github\.com/[\w-]+/([\w-]+)", github_url)
        if repo_match:
            repo_name = repo_match.group(1)
            
            # Add common patterns
            candidates.extend([
                f"@modelcontextprotocol/{repo_name}",
                f"mcp-{repo_name}",
                f"{repo_name}-mcp",
                repo_name,
            ])
        
        return list(set(candidates))  # Remove duplicates
    
    def guess_category(self, server_name: str, description: str = "") -> Optional[str]:
        """Guess the category based on server name and description."""
        text = f"{server_name} {description}".lower()
        
        for keyword, category in self.category_mapping.items():
            if keyword in text:
                return category
        
        return "utility"  # Default category
    
    async def convert_server_entry(self, github_url: str, description: str = "") -> ServerConversion:
        """Convert a single server entry."""
        candidates = self.convert_github_to_npm_candidates(github_url)
        
        # Validate which candidates actually exist
        async with self.validator:
            validation_results = await self.validator.validate_batch(candidates)
        
        # Find best validated package
        validated_package = None
        confidence = 0.0
        
        for candidate in candidates:
            if validation_results.get(candidate, False):
                validated_package = candidate
                # Prefer official packages
                if candidate.startswith("@modelcontextprotocol/"):
                    confidence = 0.9
                    break
                elif confidence < 0.7:
                    confidence = 0.7
        
        # Guess category
        category = self.guess_category(github_url, description)
        
        return ServerConversion(
            github_url=github_url,
            potential_npm_packages=candidates,
            validated_package=validated_package,
            category_guess=category,
            confidence=confidence
        )
    
    async def convert_batch(self, server_entries: List[Dict]) -> List[ServerConversion]:
        """Convert multiple server entries in parallel."""
        tasks = []
        for entry in server_entries:
            github_url = entry.get("repository_url", "")
            description = entry.get("description", "")
            task = self.convert_server_entry(github_url, description)
            tasks.append(task)
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def create_registry_categories(self, conversions: List[ServerConversion]) -> Dict[str, List[str]]:
        """Create registry categories from validated conversions."""
        categories = {}
        
        for conversion in conversions:
            if not conversion.validated_package or conversion.confidence < 0.5:
                continue
                
            category = conversion.category_guess or "utility"
            
            if category not in categories:
                categories[category] = []
            
            categories[category].append(conversion.validated_package)
        
        return categories


async def main():
    """Example usage of ServerConverter."""
    converter = ServerConverter()
    
    # Test with some example GitHub URLs
    test_urls = [
        "https://github.com/modelcontextprotocol/server-filesystem",
        "https://github.com/modelcontextprotocol/server-github", 
        "https://github.com/someone/mcp-server-custom",
        "https://github.com/example/custom-mcp-server",
    ]
    
    print("🔄 Converting GitHub URLs to npm packages...")
    
    for url in test_urls:
        result = await converter.convert_server_entry(url)
        print(f"\n📦 {url}")
        print(f"   Candidates: {result.potential_npm_packages}")
        print(f"   Validated: {result.validated_package}")
        print(f"   Category: {result.category_guess}")
        print(f"   Confidence: {result.confidence:.1f}")


if __name__ == "__main__":
    asyncio.run(main())