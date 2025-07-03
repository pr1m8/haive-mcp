#!/usr/bin/env python
"""Run all MCP examples programmatically with proper process management."""

import os
import subprocess
import time
from pathlib import Path
import json
from datetime import datetime


class MCPExampleRunner:
    """Runner for MCP examples with process management."""
    
    def __init__(self):
        self.examples_dir = Path("examples")
        self.output_dir = Path("example_outputs")
        self.output_dir.mkdir(exist_ok=True)
        
        # List of example files to run
        self.examples = [
            "basic_mcp_agent_fixed.py",
            "complete_mcp_integration.py", 
            "mcp_documentation_example.py",
            "ai_enhanced_coding.py",
            "procedural_mcp_addition.py"
        ]
        
        # Simple examples that don't need nohup
        self.simple_examples = ["basic_mcp_agent_fixed.py"]
        
    def run_example(self, example_file: str, use_nohup: bool = True) -> dict:
        """Run a single example with appropriate process management."""
        
        example_path = self.examples_dir / example_file
        if not example_path.exists():
            return {
                "example": example_file,
                "status": "error",
                "error": f"File not found: {example_path}"
            }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / f"{example_file}_{timestamp}.log"
        error_file = self.output_dir / f"{example_file}_{timestamp}.err"
        
        print(f"\n{'='*60}")
        print(f"Running: {example_file}")
        print(f"Output: {output_file}")
        print(f"Using nohup: {use_nohup}")
        print(f"{'='*60}")
        
        try:
            if use_nohup and example_file not in self.simple_examples:
                # Use nohup for long-running processes
                cmd = [
                    "nohup",
                    "poetry", "run", "python", str(example_path)
                ]
                
                with open(output_file, 'w') as out, open(error_file, 'w') as err:
                    process = subprocess.Popen(
                        cmd,
                        stdout=out,
                        stderr=err,
                        start_new_session=True,  # Detach from current session
                        cwd=str(Path.cwd())
                    )
                
                # Give it a moment to start
                time.sleep(2)
                
                # Check if process started successfully
                if process.poll() is None:
                    print(f"✓ Started successfully with PID: {process.pid}")
                    return {
                        "example": example_file,
                        "status": "running",
                        "pid": process.pid,
                        "output_file": str(output_file),
                        "error_file": str(error_file)
                    }
                else:
                    with open(error_file, 'r') as f:
                        error_content = f.read()
                    return {
                        "example": example_file,
                        "status": "error",
                        "error": error_content[:500]  # First 500 chars
                    }
            else:
                # Run directly for simple examples
                cmd = ["poetry", "run", "python", str(example_path)]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # 30 second timeout for simple examples
                )
                
                # Save output
                with open(output_file, 'w') as f:
                    f.write(result.stdout)
                
                if result.stderr:
                    with open(error_file, 'w') as f:
                        f.write(result.stderr)
                
                if result.returncode == 0:
                    print("✓ Completed successfully")
                    return {
                        "example": example_file,
                        "status": "completed",
                        "output_file": str(output_file)
                    }
                else:
                    print(f"✗ Failed with return code: {result.returncode}")
                    return {
                        "example": example_file,
                        "status": "error",
                        "return_code": result.returncode,
                        "error": result.stderr[:500] if result.stderr else "Unknown error"
                    }
                    
        except subprocess.TimeoutExpired:
            return {
                "example": example_file,
                "status": "timeout",
                "error": "Example timed out after 30 seconds"
            }
        except Exception as e:
            return {
                "example": example_file,
                "status": "error",
                "error": str(e)
            }
    
    def run_all(self):
        """Run all examples and save results."""
        
        print(f"MCP Example Runner")
        print(f"Found {len(self.examples)} examples to run")
        
        results = []
        
        for example in self.examples:
            result = self.run_example(example)
            results.append(result)
            
            # Brief pause between examples
            time.sleep(1)
        
        # Save results summary
        summary_file = self.output_dir / f"run_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        
        for result in results:
            status_symbol = {
                "completed": "✓",
                "running": "⚡",
                "error": "✗",
                "timeout": "⏱"
            }.get(result["status"], "?")
            
            print(f"{status_symbol} {result['example']}: {result['status']}")
            
            if result["status"] == "running":
                print(f"   PID: {result['pid']}")
                print(f"   Output: {result['output_file']}")
            elif result["status"] == "error":
                print(f"   Error: {result.get('error', 'Unknown')[:100]}...")
        
        print(f"\nResults saved to: {summary_file}")
        
        # Show how to monitor running processes
        running = [r for r in results if r["status"] == "running"]
        if running:
            print(f"\n{'='*60}")
            print("MONITORING RUNNING PROCESSES")
            print(f"{'='*60}")
            print("To check on running processes:")
            for r in running:
                print(f"\n{r['example']}:")
                print(f"  tail -f {r['output_file']}")
                print(f"  ps -p {r['pid']}")
                
    def check_status(self, pid: int) -> str:
        """Check if a process is still running."""
        try:
            # Check if process exists
            os.kill(pid, 0)
            return "running"
        except ProcessLookupError:
            return "completed"
        except PermissionError:
            return "unknown"


def main():
    """Main entry point."""
    runner = MCPExampleRunner()
    
    # First, let's just test the simple example
    print("Testing simple example first...")
    result = runner.run_example("test_simple.py", use_nohup=False)
    print(f"Test result: {result}")
    
    if result["status"] == "completed":
        print("\nTest successful! Running all examples...")
        runner.run_all()
    else:
        print("\nTest failed. Please fix the issues before running all examples.")
        if result.get("error"):
            print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()