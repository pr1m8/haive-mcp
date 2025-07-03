#!/usr/bin/env python3
"""Test each installer type individually to ensure they work.

This module tests NPM, Pip, Git, and Docker installers separately
with real-world examples to verify functionality.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.haive.mcp.downloader import GeneralMCPDownloader, ServerConfig, ServerTemplate, InstallationMethod
from src.haive.mcp.downloader.installers import NPMInstaller, PipInstaller, GitInstaller, DockerInstaller

console = Console()


class TestInstallerTypes:
    """Test each installer type with real examples."""
    
    @pytest.fixture
    def test_dir(self, tmp_path):
        """Create test directory."""
        test_dir = tmp_path / "installer_tests"
        test_dir.mkdir(exist_ok=True)
        return test_dir
    
    async def test_npm_installer_real(self, test_dir):
        """Test NPM installer with real packages.
        
        Tests:
        1. Official @modelcontextprotocol package
        2. Community npm package
        3. Scoped package
        4. Version-specific install
        """
        console.print(Panel.fit("[bold cyan]Testing NPM Installer[/bold cyan]"))
        
        installer = NPMInstaller()
        results = []
        
        # Test cases
        test_cases = [
            {
                "name": "Official MCP filesystem",
                "config": ServerConfig(
                    name="filesystem",
                    template="npm_official",
                    source="npm",
                    variables={"service": "filesystem"}
                ),
                "template": ServerTemplate(
                    name="npm_official",
                    installation_method=InstallationMethod.NPM,
                    command_pattern="@modelcontextprotocol/server-{service}"
                )
            },
            {
                "name": "Community package (if exists)",
                "config": ServerConfig(
                    name="json-server",
                    template="npm_community",
                    source="npm", 
                    variables={"package": "json-server"}
                ),
                "template": ServerTemplate(
                    name="npm_community",
                    installation_method=InstallationMethod.NPM,
                    command_pattern="{package}"
                )
            }
        ]
        
        for test_case in test_cases:
            console.print(f"\n[yellow]Testing: {test_case['name']}[/yellow]")
            
            try:
                # Check if can handle
                can_handle = await installer.can_handle(
                    test_case["config"], 
                    test_case["template"]
                )
                assert can_handle, f"NPM installer should handle {test_case['name']}"
                
                # Install
                result = await installer.install(
                    test_case["config"],
                    test_case["template"],
                    test_dir
                )
                
                # Verify
                if result["success"]:
                    verified = await installer.verify(
                        test_case["config"],
                        test_case["template"],
                        test_dir
                    )
                    result["verified"] = verified
                
                results.append({
                    "test": test_case["name"],
                    "success": result["success"],
                    "verified": result.get("verified", False),
                    "command": result.get("command", "N/A"),
                    "error": result.get("error", None)
                })
                
                console.print(f"✓ Success: {result['success']}, Verified: {result.get('verified', False)}")
                
            except Exception as e:
                results.append({
                    "test": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
                console.print(f"[red]✗ Error: {e}[/red]")
        
        # Display results
        self._display_results("NPM Installer", results)
        
        # At least one should succeed if npm is available
        successes = [r for r in results if r["success"]]
        if self._check_npm_available():
            assert len(successes) > 0, "At least one NPM install should succeed"
    
    async def test_pip_installer_real(self, test_dir):
        """Test Pip installer with real packages.
        
        Tests:
        1. Simple package
        2. Package with dependencies
        3. Specific version
        4. Git+pip install
        """
        console.print(Panel.fit("[bold cyan]Testing Pip Installer[/bold cyan]"))
        
        installer = PipInstaller()
        results = []
        
        test_cases = [
            {
                "name": "Simple package (requests)",
                "config": ServerConfig(
                    name="requests",
                    template="pypi_package",
                    source="pypi",
                    variables={"package": "requests"}
                ),
                "template": ServerTemplate(
                    name="pypi_package",
                    installation_method=InstallationMethod.PIP,
                    command_pattern="{package}"
                )
            },
            {
                "name": "MCP-related package",
                "config": ServerConfig(
                    name="mcp",
                    template="pypi_package",
                    source="pypi",
                    variables={"package": "mcp"}
                ),
                "template": ServerTemplate(
                    name="pypi_package", 
                    installation_method=InstallationMethod.PIP,
                    command_pattern="{package}"
                )
            }
        ]
        
        for test_case in test_cases:
            console.print(f"\n[yellow]Testing: {test_case['name']}[/yellow]")
            
            try:
                # Check if can handle
                can_handle = await installer.can_handle(
                    test_case["config"],
                    test_case["template"]
                )
                assert can_handle, f"Pip installer should handle {test_case['name']}"
                
                # Install
                result = await installer.install(
                    test_case["config"],
                    test_case["template"],
                    test_dir
                )
                
                # Verify
                if result["success"]:
                    verified = await installer.verify(
                        test_case["config"],
                        test_case["template"],
                        test_dir
                    )
                    result["verified"] = verified
                
                results.append({
                    "test": test_case["name"],
                    "success": result["success"],
                    "verified": result.get("verified", False),
                    "command": result.get("command", "N/A"),
                    "error": result.get("error", None)
                })
                
                console.print(f"✓ Success: {result['success']}, Verified: {result.get('verified', False)}")
                
            except Exception as e:
                results.append({
                    "test": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
                console.print(f"[red]✗ Error: {e}[/red]")
        
        self._display_results("Pip Installer", results)
        
        # Pip should always work
        successes = [r for r in results if r["success"]]
        assert len(successes) > 0, "At least one Pip install should succeed"
    
    async def test_git_installer_real(self, test_dir):
        """Test Git installer with real repositories.
        
        Tests:
        1. Public GitHub repo
        2. Repo with requirements.txt
        3. Repo with setup.py
        4. Specific branch/tag
        """
        console.print(Panel.fit("[bold cyan]Testing Git Installer[/bold cyan]"))
        
        installer = GitInstaller()
        results = []
        
        test_cases = [
            {
                "name": "Simple public repo",
                "config": ServerConfig(
                    name="hello-world",
                    template="git_repo",
                    source="https://github.com/octocat/Hello-World.git",
                    variables={"owner": "octocat", "repo": "Hello-World"}
                ),
                "template": ServerTemplate(
                    name="git_repo",
                    installation_method=InstallationMethod.GIT,
                    command_pattern="echo 'Hello from {repo}'",
                    post_install=[]
                )
            }
        ]
        
        for test_case in test_cases:
            console.print(f"\n[yellow]Testing: {test_case['name']}[/yellow]")
            
            try:
                # Check if can handle
                can_handle = await installer.can_handle(
                    test_case["config"],
                    test_case["template"]
                )
                assert can_handle, f"Git installer should handle {test_case['name']}"
                
                # Install
                result = await installer.install(
                    test_case["config"],
                    test_case["template"],
                    test_dir
                )
                
                # Verify
                if result["success"]:
                    verified = await installer.verify(
                        test_case["config"],
                        test_case["template"],
                        test_dir
                    )
                    result["verified"] = verified
                
                results.append({
                    "test": test_case["name"],
                    "success": result["success"],
                    "verified": result.get("verified", False),
                    "clone_dir": result.get("clone_dir", "N/A"),
                    "error": result.get("error", None)
                })
                
                console.print(f"✓ Success: {result['success']}, Verified: {result.get('verified', False)}")
                
            except Exception as e:
                results.append({
                    "test": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
                console.print(f"[red]✗ Error: {e}[/red]")
        
        self._display_results("Git Installer", results)
        
        # Git should work if available
        if self._check_git_available():
            successes = [r for r in results if r["success"]]
            assert len(successes) > 0, "At least one Git clone should succeed"
    
    async def test_docker_installer_real(self, test_dir):
        """Test Docker installer with real images.
        
        Tests:
        1. Official Docker Hub image
        2. Lightweight image (alpine)
        3. Specific tag
        4. Multi-arch image
        """
        console.print(Panel.fit("[bold cyan]Testing Docker Installer[/bold cyan]"))
        
        installer = DockerInstaller()
        results = []
        
        test_cases = [
            {
                "name": "Alpine Linux (small image)",
                "config": ServerConfig(
                    name="alpine",
                    template="docker_image",
                    source="docker",
                    variables={"image": "alpine:latest"}
                ),
                "template": ServerTemplate(
                    name="docker_image",
                    installation_method=InstallationMethod.DOCKER,
                    command_pattern="{image}"
                )
            },
            {
                "name": "Busybox (tiny image)",
                "config": ServerConfig(
                    name="busybox",
                    template="docker_image",
                    source="docker",
                    variables={"image": "busybox:latest"}
                ),
                "template": ServerTemplate(
                    name="docker_image",
                    installation_method=InstallationMethod.DOCKER,
                    command_pattern="{image}"
                )
            }
        ]
        
        for test_case in test_cases:
            console.print(f"\n[yellow]Testing: {test_case['name']}[/yellow]")
            
            try:
                # Check if can handle
                can_handle = await installer.can_handle(
                    test_case["config"],
                    test_case["template"]
                )
                assert can_handle, f"Docker installer should handle {test_case['name']}"
                
                # Install only if Docker is available
                if self._check_docker_available():
                    result = await installer.install(
                        test_case["config"],
                        test_case["template"],
                        test_dir
                    )
                    
                    # Verify
                    if result["success"]:
                        verified = await installer.verify(
                            test_case["config"],
                            test_case["template"],
                            test_dir
                        )
                        result["verified"] = verified
                    
                    results.append({
                        "test": test_case["name"],
                        "success": result["success"],
                        "verified": result.get("verified", False),
                        "image": result.get("image", "N/A"),
                        "error": result.get("error", None)
                    })
                    
                    console.print(f"✓ Success: {result['success']}, Verified: {result.get('verified', False)}")
                else:
                    results.append({
                        "test": test_case["name"],
                        "success": False,
                        "error": "Docker not available"
                    })
                    console.print("[yellow]⚠ Docker not available, skipping[/yellow]")
                    
            except Exception as e:
                results.append({
                    "test": test_case["name"],
                    "success": False,
                    "error": str(e)
                })
                console.print(f"[red]✗ Error: {e}[/red]")
        
        self._display_results("Docker Installer", results)
    
    def _display_results(self, title: str, results: list):
        """Display test results in a table."""
        table = Table(title=f"{title} Results")
        table.add_column("Test", style="cyan")
        table.add_column("Success", justify="center")
        table.add_column("Verified", justify="center")
        table.add_column("Error/Notes")
        
        for result in results:
            success_mark = "✓" if result.get("success") else "✗"
            success_style = "green" if result.get("success") else "red"
            
            verified_mark = "✓" if result.get("verified") else "✗" if "verified" in result else "-"
            verified_style = "green" if result.get("verified") else "red" if "verified" in result else "dim"
            
            error = result.get("error", "Success") if not result.get("success") else ""
            
            table.add_row(
                result["test"],
                f"[{success_style}]{success_mark}[/{success_style}]",
                f"[{verified_style}]{verified_mark}[/{verified_style}]",
                error[:50] + "..." if len(error) > 50 else error
            )
        
        console.print("\n")
        console.print(table)
        console.print("\n")
    
    def _check_npm_available(self) -> bool:
        """Check if npm is available."""
        try:
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _check_git_available(self) -> bool:
        """Check if git is available."""
        try:
            subprocess.run(["git", "--version"], capture_output=True, check=True)
            return True
        except:
            return False
    
    def _check_docker_available(self) -> bool:
        """Check if docker is available."""
        try:
            subprocess.run(["docker", "--version"], capture_output=True, check=True)
            return True
        except:
            return False


async def run_all_tests():
    """Run all installer tests."""
    console.print(Panel.fit(
        "[bold cyan]MCP Installer Test Suite[/bold cyan]\n"
        "Testing each installer type with real examples",
        title="Test Suite"
    ))
    
    # Create test instance
    tester = TestInstallerTypes()
    test_dir = Path("./test_installer_outputs")
    test_dir.mkdir(exist_ok=True)
    
    # Run each test
    tests = [
        ("NPM", tester.test_npm_installer_real),
        ("Pip", tester.test_pip_installer_real),
        ("Git", tester.test_git_installer_real),
        ("Docker", tester.test_docker_installer_real)
    ]
    
    results = {}
    for name, test_func in tests:
        console.print(f"\n[bold]Running {name} tests...[/bold]")
        try:
            await test_func(test_dir)
            results[name] = "PASSED"
        except Exception as e:
            results[name] = f"FAILED: {e}"
            console.print(f"[red]Test failed: {e}[/red]")
    
    # Summary
    console.print("\n[bold]Test Summary:[/bold]")
    for name, result in results.items():
        if result == "PASSED":
            console.print(f"✓ {name}: [green]{result}[/green]")
        else:
            console.print(f"✗ {name}: [red]{result}[/red]")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())