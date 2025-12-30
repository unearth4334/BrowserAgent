# WorkflowInterpreter Usage Guide

## Required Files for External Projects

### Core Source Files
- **WorkflowInterpreter Class**: `/home/sdamk/dev/BrowserAgent/src/browser_agent/comfyui/workflow_interpreter.py`
  - Main class for applying JSON inputs to ComfyUI workflows
  - Dependencies: Standard library only (json, logging, copy, pathlib, typing, dataclasses)

### Configuration & Data Files
- **Wrapper YAML**: `/home/sdamk/dev/BrowserAgent/IMG_to_VIDEO.webui.yml`
  - Defines node mappings and action configurations for IMG_to_VIDEO workflow
  
- **Base Workflow**: `/home/sdamk/dev/BrowserAgent/outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json`
  - Original ComfyUI workflow (85 nodes, hash: 47e91030)
  
- **Example Input**: `/home/sdamk/dev/BrowserAgent/tests/comfyui/test_data/interpreter_inputs/base_inputs.json`
  - Reference input file showing expected JSON structure

### Optional Test Files (for validation)
- **Test Suite**: `/home/sdamk/dev/BrowserAgent/tests/comfyui/test_interpreter_integration.py`
  - 37 integration tests demonstrating various usage scenarios
  
- **All Test Inputs**: `/home/sdamk/dev/BrowserAgent/tests/comfyui/test_data/interpreter_inputs/`
  - Contains 37 example input JSON files (base + tests 01-37)

---

## Basic Usage

```python
import json
from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter

# Initialize with wrapper YAML
interpreter = WorkflowInterpreter("IMG_to_VIDEO.webui.yml")

# Load inputs
with open("IMG_to_VIDEO_inputs.json") as f:
    inputs = json.load(f)

# Load original workflow
with open("outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json") as f:
    original_workflow = json.load(f)

# Generate actions from inputs
actions = interpreter.generate_actions(inputs)

# Apply actions to get modified workflow
modified_workflow = interpreter.apply_actions(original_workflow, actions)

# Export to file
interpreter.export(modified_workflow, "outputs/workflows/my_output.json")
```

---

## Setup for External Projects

### Option 1: Copy Files
```bash
# Create directory structure
mkdir -p your_project/browser_agent/comfyui
mkdir -p your_project/config
mkdir -p your_project/workflows

# Copy core source
cp /home/sdamk/dev/BrowserAgent/src/browser_agent/comfyui/workflow_interpreter.py \
   your_project/browser_agent/comfyui/

# Copy configuration & base workflow
cp /home/sdamk/dev/BrowserAgent/IMG_to_VIDEO.webui.yml \
   your_project/config/

cp /home/sdamk/dev/BrowserAgent/outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json \
   your_project/workflows/

# Optional: Copy example inputs for reference
cp -r /home/sdamk/dev/BrowserAgent/tests/comfyui/test_data/interpreter_inputs \
   your_project/examples/
```

### Option 2: Python Path Reference
```python
import sys
sys.path.insert(0, '/home/sdamk/dev/BrowserAgent/src')

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter
```

---

## Input JSON Structure

The input file should contain nested dictionaries with these top-level keys:

- `basic_settings`: duration, size, frame_rate, speed
- `generation_parameters`: steps, cfg, seed  
- `model_selection`: loras (high_noise/low_noise pairs)
- `advanced_features`: enable flags (interpolation, upscaler, saves, etc.)
- `performance_optimization`: VRAM settings, block swap
- `output_configuration`: save flags, upscale ratio

**Example**:
```json
{
  "basic_settings": {
    "duration": 5.0,
    "size": {"width": 896, "height": 1120},
    "frame_rate": 16.0
  },
  "generation_parameters": {
    "steps": 30,
    "cfg": 3.0,
    "seed": 701609645127340
  },
  "model_selection": {
    "loras": [
      {
        "high_noise": "example_high.safetensors",
        "low_noise": "example_low.safetensors",
        "strength": 0.8
      }
    ]
  }
}
```

See `/home/sdamk/dev/BrowserAgent/tests/comfyui/test_data/interpreter_inputs/base_inputs.json` for complete example.

---

## Method Options

### Simple Method (Recommended)
```python
interpreter = WorkflowInterpreter("IMG_to_VIDEO.webui.yml")
interpreter.process("inputs.json", "output.json")
```

### Manual Method (Advanced)
Use the code block above when you need:
- To inspect actions before applying
- To modify actions programmatically
- To apply actions to multiple workflows
- To integrate with other processing steps

---

## Validation

After generating a workflow, validate it:

```python
# Check node count (should be 85 for IMG_to_VIDEO)
assert len(modified_workflow['nodes']) == 85

# Verify specific changes (example: check duration)
duration_node = next(n for n in modified_workflow['nodes'] if n['id'] == 426)
assert duration_node['widgets_values'][0] == inputs['basic_settings']['duration']
```

---

## Notes for Coding Agents

When copying files to another project:

1. **Preserve directory structure** for imports to work
2. **Update paths** in code to match new project structure  
3. **Verify dependencies**: WorkflowInterpreter only needs Python 3.11+ stdlib
4. **Test after copy**: Run with base_inputs.json to verify setup
5. **Consider version control**: Track which version of workflow_interpreter.py was copied

**Command for bulk copy**:
```bash
cp /home/sdamk/dev/BrowserAgent/src/browser_agent/comfyui/workflow_interpreter.py /path/to/target/ && \
cp /home/sdamk/dev/BrowserAgent/IMG_to_VIDEO.webui.yml /path/to/target/ && \
cp /home/sdamk/dev/BrowserAgent/outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json /path/to/target/
```
