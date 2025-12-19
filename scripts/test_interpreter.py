#!/usr/bin/env python3
"""
Test script for workflow interpreter.

Usage:
    python scripts/test_interpreter.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter
from browser_agent.logging_utils import get_logger

logger = get_logger(__name__)


def main():
    # Paths
    wrapper_path = "IMG_to_VIDEO.webui.yml"
    inputs_path = "IMG_to_VIDEO_inputs.json"
    output_path = "outputs/workflows/WAN2.2_IMG_to_VIDEO_Test_Generated.json"
    
    logger.info("=" * 60)
    logger.info("Workflow Interpreter Test")
    logger.info("=" * 60)
    
    # Initialize interpreter
    logger.info(f"\n1. Initializing interpreter with wrapper: {wrapper_path}")
    interpreter = WorkflowInterpreter(wrapper_path)
    
    # Process workflow
    logger.info(f"\n2. Processing with inputs: {inputs_path}")
    logger.info(f"   Output will be: {output_path}")
    
    try:
        modified_workflow = interpreter.process(inputs_path, output_path)
        
        logger.info("\n" + "=" * 60)
        logger.info("SUCCESS! Workflow generated successfully.")
        logger.info("=" * 60)
        logger.info(f"\nOutput: {output_path}")
        logger.info(f"Total nodes: {len(modified_workflow.get('nodes', []))}")
        
        # Compare with original
        original_path = Path(interpreter.workflow_path)
        if original_path.exists():
            import json
            with open(original_path) as f:
                original = json.load(f)
            
            logger.info(f"\nOriginal workflow: {original_path}")
            logger.info(f"Original nodes: {len(original.get('nodes', []))}")
            logger.info("\nSince inputs match the original values,")
            logger.info("the generated workflow should be functionally identical.")
        
    except Exception as e:
        logger.error(f"\nERROR: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
