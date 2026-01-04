#!/usr/bin/env python3
"""
Generate ComfyUI workflow from WebUI input JSON.

Usage:
    # Generate workflow from input file
    python scripts/generate_workflow.py input.json
    
    # Specify custom output path
    python scripts/generate_workflow.py input.json -o custom_output.json
    
    # Use custom wrapper config and base workflow
    python scripts/generate_workflow.py input.json \
        -c custom_wrapper.yml \
        -b custom_base_workflow.json

Example input structure:
    {
      "inputs": {
        "basic_settings": {...},
        "generation_parameters": {...},
        "model_selection": {...},
        "advanced_features": {...}
      }
    }
"""
import argparse
import json
import sys
from pathlib import Path
from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter


def main():
    parser = argparse.ArgumentParser(
        description="Generate ComfyUI workflow from WebUI input JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "input_file",
        help="WebUI input JSON file with user settings"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="outputs/workflows/my_output.json",
        help="Output workflow JSON path (default: outputs/workflows/my_output.json)"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="IMG_to_VIDEO.webui.yml",
        help="Wrapper YAML config file (default: IMG_to_VIDEO.webui.yml)"
    )
    
    parser.add_argument(
        "-b", "--base-workflow",
        default="outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json",
        help="Base workflow template to modify"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input_file).exists():
        print(f"❌ Error: Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize interpreter
    interpreter = WorkflowInterpreter(args.config)
    
    # Load inputs
    with open(args.input_file) as f:
        inputs = json.load(f)
    
    # Load original workflow
    with open(args.base_workflow) as f:
        original_workflow = json.load(f)
    
    # Generate actions
    actions = interpreter.generate_actions(inputs)
    print(f"Generated {len(actions)} actions")
    
    # Apply actions to get modified workflow
    modified_workflow = interpreter.apply_actions(original_workflow, actions)
    
    # Export
    interpreter.export(modified_workflow, args.output)
    print(f"✅ Workflow exported to {args.output}")


if __name__ == "__main__":
    main()
