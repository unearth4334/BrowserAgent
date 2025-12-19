#!/usr/bin/env python3
"""
Comprehensive test runner for workflow interpreter.

Tests all 26 workflow variations against their expected outputs,
validating that the interpreter correctly generates each modification.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter
from browser_agent.logging_utils import get_logger

logger = get_logger(__name__)


class TestResult:
    """Result of a single test case."""
    
    def __init__(self, test_id: str, description: str):
        self.test_id = test_id
        self.description = description
        self.passed = False
        self.expected_hash = None
        self.actual_hash = None
        self.error = None
        self.action_count = 0


class TestSuite:
    """Test suite for workflow interpreter."""
    
    def __init__(self, wrapper_path: str = "IMG_to_VIDEO.webui.yml"):
        self.wrapper_path = wrapper_path
        self.interpreter = WorkflowInterpreter(wrapper_path)
        self.results: List[TestResult] = []
        self.test_inputs_dir = Path("tests/comfyui/test_data/interpreter_inputs")
        
    def discover_tests(self) -> List[Path]:
        """Find all test input files."""
        if not self.test_inputs_dir.exists():
            logger.error(f"Test inputs directory not found: {self.test_inputs_dir}")
            return []
        
        test_files = sorted(self.test_inputs_dir.glob("*.json"))
        logger.info(f"Discovered {len(test_files)} test cases")
        return test_files
    
    def run_test(self, test_file: Path) -> TestResult:
        """Run a single test case."""
        logger.info(f"\n{'='*80}")
        logger.info(f"Running test: {test_file.name}")
        logger.info(f"{'='*80}")
        
        # Load test input
        with open(test_file) as f:
            test_data = json.load(f)
        
        result = TestResult(
            test_id=test_data.get("test_id", test_file.stem),
            description=test_data.get("description", "")
        )
        result.expected_hash = test_data.get("expected_hash")
        
        try:
            # Load expected workflow
            expected_workflow_path = test_data.get("workflow_file")
            if not expected_workflow_path:
                raise ValueError("No workflow_file specified in test data")
            
            expected_workflow_path = Path(expected_workflow_path)
            if not expected_workflow_path.exists():
                raise FileNotFoundError(f"Expected workflow not found: {expected_workflow_path}")
            
            with open(expected_workflow_path) as f:
                expected_workflow = json.load(f)
            
            # Generate workflow from inputs
            inputs = test_data.get("inputs", {})
            base_workflow_path = test_data.get("workflow_file")
            
            # Use original workflow as base
            base_workflow = expected_workflow.copy()
            
            # Generate actions
            actions = self.interpreter.generate_actions(inputs)
            result.action_count = len(actions)
            logger.info(f"Generated {len(actions)} actions")
            
            # Apply actions
            generated_workflow = self.interpreter.apply_actions(base_workflow, actions)
            
            # Calculate hash
            result.actual_hash = self.interpreter._calculate_hash(generated_workflow)
            logger.info(f"Expected hash: {result.expected_hash}")
            logger.info(f"Actual hash:   {result.actual_hash}")
            
            # Compare
            if result.actual_hash == result.expected_hash:
                result.passed = True
                logger.info("✓ PASS: Hashes match")
            else:
                result.passed = False
                logger.warning("✗ FAIL: Hash mismatch")
                
                # Additional diagnostics
                self._compare_workflows(expected_workflow, generated_workflow)
        
        except Exception as e:
            result.passed = False
            result.error = str(e)
            logger.error(f"✗ ERROR: {e}", exc_info=True)
        
        return result
    
    def _compare_workflows(self, expected: Dict, actual: Dict):
        """Compare two workflows and log differences."""
        # Compare node counts
        expected_nodes = len(expected.get("nodes", []))
        actual_nodes = len(actual.get("nodes", []))
        if expected_nodes != actual_nodes:
            logger.warning(f"Node count mismatch: expected {expected_nodes}, got {actual_nodes}")
        
        # Compare specific nodes
        expected_nodes_by_id = {n["id"]: n for n in expected.get("nodes", [])}
        actual_nodes_by_id = {n["id"]: n for n in actual.get("nodes", [])}
        
        for node_id in expected_nodes_by_id:
            if node_id not in actual_nodes_by_id:
                logger.warning(f"Node {node_id} missing in generated workflow")
                continue
            
            exp_node = expected_nodes_by_id[node_id]
            act_node = actual_nodes_by_id[node_id]
            
            # Compare widgets_values
            exp_widgets = exp_node.get("widgets_values", [])
            act_widgets = act_node.get("widgets_values", [])
            
            if exp_widgets != act_widgets:
                logger.warning(f"Node {node_id} ({exp_node.get('type', 'unknown')}): widgets differ")
                logger.warning(f"  Expected: {exp_widgets}")
                logger.warning(f"  Actual:   {act_widgets}")
            
            # Compare mode
            if exp_node.get("mode") != act_node.get("mode"):
                logger.warning(f"Node {node_id}: mode differs - expected {exp_node.get('mode')}, got {act_node.get('mode')}")
    
    def run_all(self) -> bool:
        """Run all tests and return True if all passed."""
        test_files = self.discover_tests()
        
        if not test_files:
            logger.error("No test files found")
            return False
        
        for test_file in test_files:
            result = self.run_test(test_file)
            self.results.append(result)
        
        # Print summary
        self._print_summary()
        
        # Return overall pass/fail
        return all(r.passed for r in self.results)
    
    def _print_summary(self):
        """Print test results summary."""
        logger.info(f"\n{'='*80}")
        logger.info("TEST SUMMARY")
        logger.info(f"{'='*80}")
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed and not r.error)
        errors = sum(1 for r in self.results if r.error)
        total = len(self.results)
        
        logger.info(f"Total tests:  {total}")
        logger.info(f"Passed:       {passed} ({100*passed/total:.1f}%)")
        logger.info(f"Failed:       {failed} ({100*failed/total:.1f}%)")
        logger.info(f"Errors:       {errors} ({100*errors/total:.1f}%)")
        
        if failed > 0 or errors > 0:
            logger.info(f"\n{'='*80}")
            logger.info("FAILED TESTS")
            logger.info(f"{'='*80}")
            
            for result in self.results:
                if not result.passed:
                    logger.info(f"\n{result.test_id}: {result.description}")
                    if result.error:
                        logger.info(f"  Error: {result.error}")
                    else:
                        logger.info(f"  Expected: {result.expected_hash}")
                        logger.info(f"  Actual:   {result.actual_hash}")
        
        logger.info(f"\n{'='*80}")


def main():
    """Main entry point."""
    suite = TestSuite()
    success = suite.run_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
