#!/usr/bin/env python3
"""
Run workflow interpreter on all 26 test input files.

Generates output workflows for each test case and reports results.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter
from browser_agent.logging_utils import get_logger

logger = get_logger(__name__)


class TestRunner:
    """Run interpreter on all test cases."""
    
    def __init__(self, wrapper_path: str = "IMG_to_VIDEO.webui.yml"):
        self.wrapper_path = wrapper_path
        self.interpreter = WorkflowInterpreter(wrapper_path)
        self.test_inputs_dir = Path("tests/comfyui/test_data/interpreter_inputs")
        self.output_dir = Path("outputs/workflows/generated")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []
    
    def discover_tests(self) -> List[Path]:
        """Find all test input files."""
        if not self.test_inputs_dir.exists():
            logger.error(f"Test inputs directory not found: {self.test_inputs_dir}")
            return []
        
        test_files = sorted(self.test_inputs_dir.glob("*.json"))
        logger.info(f"Discovered {len(test_files)} test cases\n")
        return test_files
    
    def run_test(self, test_file: Path) -> Dict:
        """Run interpreter on a single test case."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {test_file.name}")
        logger.info(f"{'='*80}")
        
        result = {
            "test_file": test_file.name,
            "success": False,
            "expected_hash": None,
            "actual_hash": None,
            "output_file": None,
            "error": None
        }
        
        try:
            # Load test data to get expected hash
            with open(test_file) as f:
                test_data = json.load(f)
            
            result["expected_hash"] = test_data.get("expected_hash")
            test_id = test_data.get("test_id", test_file.stem)
            
            # Generate output path
            output_path = self.output_dir / f"{test_id}_{result['expected_hash']}_generated.json"
            
            # Run interpreter
            modified_workflow = self.interpreter.process(test_file, output_path)
            
            # Calculate actual hash
            result["actual_hash"] = self.interpreter._calculate_hash(modified_workflow)
            result["output_file"] = str(output_path)
            result["success"] = True
            
            # Check if hash matches
            if result["actual_hash"] == result["expected_hash"]:
                logger.info(f"✓ SUCCESS: Hash matches ({result['actual_hash']})")
            else:
                logger.warning(f"⚠ Hash mismatch:")
                logger.warning(f"  Expected: {result['expected_hash']}")
                logger.warning(f"  Actual:   {result['actual_hash']}")
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"✗ ERROR: {e}", exc_info=True)
        
        return result
    
    def run_all(self) -> bool:
        """Run all tests and return True if all succeeded."""
        test_files = self.discover_tests()
        
        if not test_files:
            logger.error("No test files found")
            return False
        
        for test_file in test_files:
            result = self.run_test(test_file)
            self.results.append(result)
        
        # Print summary
        self._print_summary()
        
        return all(r["success"] for r in self.results)
    
    def _print_summary(self):
        """Print results summary."""
        logger.info(f"\n{'='*80}")
        logger.info("SUMMARY")
        logger.info(f"{'='*80}")
        
        total = len(self.results)
        succeeded = sum(1 for r in self.results if r["success"])
        failed = sum(1 for r in self.results if not r["success"] and not r["error"])
        errors = sum(1 for r in self.results if r["error"])
        hash_matches = sum(1 for r in self.results if r["success"] and r["actual_hash"] == r["expected_hash"])
        
        logger.info(f"\nTotal tests:     {total}")
        logger.info(f"Succeeded:       {succeeded} ({100*succeeded/total:.1f}%)")
        logger.info(f"Hash matches:    {hash_matches} ({100*hash_matches/total:.1f}%)")
        logger.info(f"Hash mismatches: {succeeded - hash_matches}")
        logger.info(f"Errors:          {errors}")
        
        if hash_matches != succeeded:
            logger.info(f"\n{'='*80}")
            logger.info("HASH MISMATCHES")
            logger.info(f"{'='*80}")
            
            for result in self.results:
                if result["success"] and result["actual_hash"] != result["expected_hash"]:
                    logger.info(f"\n{result['test_file']}:")
                    logger.info(f"  Expected: {result['expected_hash']}")
                    logger.info(f"  Actual:   {result['actual_hash']}")
                    logger.info(f"  Output:   {result['output_file']}")
        
        if errors > 0:
            logger.info(f"\n{'='*80}")
            logger.info("ERRORS")
            logger.info(f"{'='*80}")
            
            for result in self.results:
                if result["error"]:
                    logger.info(f"\n{result['test_file']}:")
                    logger.info(f"  Error: {result['error']}")
        
        logger.info(f"\n{'='*80}")
        logger.info(f"Output directory: {self.output_dir}")
        logger.info(f"{'='*80}\n")


def main():
    """Main entry point."""
    runner = TestRunner()
    success = runner.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
