#!/usr/bin/env python3
import json
from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter

# Initialize
interpreter = WorkflowInterpreter("IMG_to_VIDEO.webui.yml")

# Load inputs
with open("test_webui_final_input.json") as f:
    inputs = json.load(f)

# Load original workflow
with open("outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json") as f:
    original_workflow = json.load(f)

# Generate actions
actions = interpreter.generate_actions(inputs)

# Apply actions to get modified workflow
modified_workflow = interpreter.apply_actions(original_workflow, actions)

# Export
interpreter.export(modified_workflow, "outputs/workflows/my_output.json")

print("✅ Workflow exported to outputs/workflows/my_output.json")
