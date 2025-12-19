# ComfyUI Workflow Change Action System

## Overview

This document defines a comprehensive system for programmatically modifying ComfyUI workflows through elementary change actions. The system is designed based on analysis of 25 modified workflows to identify common modification patterns.

## Elementary Change Actions

### 1. Modify Widget Value (`modify_widget`)

**Purpose**: Change a single widget value in a node's `widgets_values` array.

**Structure**:
```python
{
    "type": "modify_widget",
    "node_id": int,                    # Target node ID
    "widget_index": int,               # Index in widgets_values array
    "new_value": Any,                  # New value to set
    "value_type": str,                 # "scalar", "vector", "object"
    "description": str                 # Human-readable description
}
```

**Examples**:
- Duration: `{"node_id": 426, "widget_index": 0, "new_value": 8}`
- CFG: `{"node_id": 85, "widget_index": 0, "new_value": 5}`
- Steps: `{"node_id": 82, "widget_index": 0, "new_value": 30}`

**Widget Value Patterns**:
- **mxSlider**: `[value, value, step]` - Modify indices 0 and 1 with same value
- **mxSlider2D**: `[x, x, y, y, isfloatX, isfloatY]` - Width at 0-1, height at 2-3
- **RandomNoise**: `[seed, control]` - Seed at index 0

### 2. Toggle Node Mode (`toggle_node_mode`)

**Purpose**: Change node execution mode (enabled/bypassed/muted).

**Structure**:
```python
{
    "type": "toggle_node_mode",
    "node_ids": List[int],             # Nodes to modify (often in groups)
    "new_mode": int,                   # Target mode value
    "description": str                 # Human-readable description
}
```

**Mode Values**:
- `0` = Enabled/Active (node executes)
- `2` = Bypassed (node skipped but passes data through)
- `4` = Muted (node completely disabled)

**Examples**:
- Enable upscaler: `{"node_ids": [372, 375, 380, 362, 381], "new_mode": 0}`
- Disable interpolation: `{"node_ids": [363, 370, 432], "new_mode": 2}`
- Mute CFGZeroStar: `{"node_ids": [351, 353], "new_mode": 4}`

### 3. Add LoRA Pair (`add_lora_pair`)

**Purpose**: Add a high/low noise LoRA pair to Power Lora Loader nodes.

**Structure**:
```python
{
    "type": "add_lora_pair",
    "high_node_id": 416,               # High noise loader node
    "low_node_id": 471,                # Low noise loader node
    "lora_config": {
        "high_path": str,              # Path to high noise LoRA
        "low_path": str,               # Path to low noise LoRA
        "strength": float,             # LoRA strength (default: 1.0)
        "enabled": bool                # Whether LoRA is active
    },
    "insert_position": int,            # Position in widgets_values array
    "description": str
}
```

**Example**:
```python
{
    "type": "add_lora_pair",
    "high_node_id": 416,
    "low_node_id": 471,
    "lora_config": {
        "high_path": "NSFW-22-H-e8.safetensors",
        "low_path": "NSFW-22-L-e8.safetensors",
        "strength": 1.0,
        "enabled": true
    },
    "insert_position": 2
}
```

### 4. Modify Vector Widget (`modify_vector_widget`)

**Purpose**: Change multiple related values in a single widget (e.g., X/Y dimensions).

**Structure**:
```python
{
    "type": "modify_vector_widget",
    "node_id": int,
    "widget_pattern": str,             # Pattern like "[x, x, y, y, 0, 0]"
    "modifications": Dict[str, Any],   # {"x": new_x, "y": new_y}
    "description": str
}
```

**Example**:
```python
{
    "type": "modify_vector_widget",
    "node_id": 83,
    "widget_pattern": "[x, x, y, y, 0, 0]",
    "modifications": {"x": 1234, "y": 1120}
}
```

## Node Type Reference

### Identified Node Types and Their Modification Patterns

| Node Type | Widget Pattern | Modification Method |
|-----------|---------------|---------------------|
| `mxSlider` | `[value, value, step]` | modify_widget (indices 0-1) |
| `mxSlider2D` | `[x, x, y, y, isfloatX, isfloatY]` | modify_vector_widget |
| `RandomNoise` | `[seed, control]` | modify_widget (index 0) |
| `Power Lora Loader` | Array of objects | add_lora_pair |
| Various feature nodes | No widgets (mode only) | toggle_node_mode |

## Node Mapping Table

### Core Parameter Nodes

| Parameter | Node ID | Node Type | Widget Index | Default Value |
|-----------|---------|-----------|--------------|---------------|
| **Duration** | 426 | mxSlider | 0-1 | 5.0 |
| **Width (X)** | 83 | mxSlider2D | 0-1 | 896 |
| **Height (Y)** | 83 | mxSlider2D | 2-3 | 1120 |
| **Steps** | 82 | mxSlider | 0-1 | 20 |
| **CFG** | 85 | mxSlider | 0-1 | 3.5 |
| **Frame Rate** | 490 | mxSlider | 0-1 | 16 |
| **Speed** | 157 | mxSlider | 0-1 | 7 |
| **Seed** | 73 | RandomNoise | 0 | (random) |
| **Upscale Ratio** | 421 | mxSlider | 0-1 | 2.0 |
| **VRAM Reduction** | 429 | mxSlider | 0-1 | 100 |

### Feature Toggle Nodes (Mode-based)

| Feature | Node IDs | Default Mode | Description |
|---------|----------|--------------|-------------|
| **Save Last Frame** | 423, 389 | 2 (bypass) | Save final frame as image |
| **Interpolation** | 363, 370, 432 | 0 (enabled) | RIFE frame interpolation |
| **Upscale + Interpolation** | 372, 375, 380, 362, 364, 379, 430 | 2 (bypass) | Combined upscale + interp |
| **Upscaler Only** | 372, 375, 380, 362, 381 | 2 (bypass) | AI upscaling only |
| **Video Enhance** | 355, 352 | 0 (enabled) | WAN video enhancement |
| **CFGZeroStar** | 351, 353 | 0 (enabled) | CFG guidance enhancement |
| **Speed Regulation** | 348, 349 | 0 (enabled) | ModelSamplingSD3 speed control |
| **Normalized Attention** | 430, 431 | 0 (enabled) | Normalized attention guidance |
| **MagCache** | 438, 437 | 0 (enabled) | Memory caching |
| **BlockSwap** | 432, 434, 435 | 0 (enabled) | Model offloading |
| **TorchCompile** | 365, 366, 369, 377 | 4 (muted) | JIT compilation |
| **Automatic Prompting** | 357, 360, 361, 368, 371, 373, 374 | 0 (enabled) | Florence2 auto-prompting |

### LoRA Nodes

| Node Type | Node ID | Description |
|-----------|---------|-------------|
| **High Noise LoRA** | 416 | High noise LoRA loader |
| **Low Noise LoRA** | 471 | Low noise LoRA loader |

## Change Action Application Algorithm

### Pseudocode for Applying Actions

```python
def apply_change_action(workflow_json, action):
    """Apply a single change action to workflow JSON."""
    
    if action["type"] == "modify_widget":
        node = find_node(workflow_json, action["node_id"])
        widget_idx = action["widget_index"]
        
        # Handle different widget patterns
        if node["type"] == "mxSlider":
            # Set both indices 0 and 1 to same value
            node["widgets_values"][0] = action["new_value"]
            node["widgets_values"][1] = action["new_value"]
        elif node["type"] == "mxSlider2D":
            # For X: modify indices 0-1, for Y: modify indices 2-3
            if widget_idx == 0:  # X dimension
                node["widgets_values"][0] = action["new_value"]
                node["widgets_values"][1] = action["new_value"]
            elif widget_idx == 2:  # Y dimension
                node["widgets_values"][2] = action["new_value"]
                node["widgets_values"][3] = action["new_value"]
        else:
            node["widgets_values"][widget_idx] = action["new_value"]
    
    elif action["type"] == "toggle_node_mode":
        for node_id in action["node_ids"]:
            node = find_node(workflow_json, node_id)
            node["mode"] = action["new_mode"]
    
    elif action["type"] == "add_lora_pair":
        high_node = find_node(workflow_json, action["high_node_id"])
        low_node = find_node(workflow_json, action["low_node_id"])
        
        lora_obj = {
            "lora": action["lora_config"]["high_path"],
            "on": action["lora_config"]["enabled"],
            "strength": action["lora_config"]["strength"],
            "strengthTwo": None
        }
        
        high_node["widgets_values"].insert(action["insert_position"], lora_obj)
        
        lora_obj["lora"] = action["lora_config"]["low_path"]
        low_node["widgets_values"].insert(action["insert_position"], lora_obj)
    
    elif action["type"] == "modify_vector_widget":
        node = find_node(workflow_json, action["node_id"])
        mods = action["modifications"]
        
        # Parse pattern to understand indices
        if "x" in mods:
            node["widgets_values"][0] = mods["x"]
            node["widgets_values"][1] = mods["x"]
        if "y" in mods:
            node["widgets_values"][2] = mods["y"]
            node["widgets_values"][3] = mods["y"]
    
    return workflow_json
```

## YAML Configuration Schema

### Enhanced `.webui.yml` Format

```yaml
# Workflow metadata
name: "IMG to VIDEO"
description: "Generate video from image"
workflow_file: "IMG_to_VIDEO_canvas.json"
base_hash: "47e91030"  # Original workflow hash for validation

# Node mapping for parameters
node_mapping:
  # Simple scalar parameters
  duration:
    node_id: 426
    node_type: "mxSlider"
    widget_indices: [0, 1]
    action_type: "modify_widget"
    
  size_x:
    node_id: 83
    node_type: "mxSlider2D"
    widget_indices: [0, 1]
    action_type: "modify_vector_widget"
    vector_key: "x"
    
  size_y:
    node_id: 83
    node_type: "mxSlider2D"
    widget_indices: [2, 3]
    action_type: "modify_vector_widget"
    vector_key: "y"
    
  steps:
    node_id: 82
    node_type: "mxSlider"
    widget_indices: [0, 1]
    action_type: "modify_widget"
    
  cfg:
    node_id: 85
    node_type: "mxSlider"
    widget_indices: [0, 1]
    action_type: "modify_widget"
    
  # Feature toggles
  save_last_frame:
    node_ids: [423, 389]
    action_type: "toggle_node_mode"
    enabled_mode: 0
    disabled_mode: 2
    
  enable_interpolation:
    node_ids: [363, 370, 432]
    action_type: "toggle_node_mode"
    enabled_mode: 0
    disabled_mode: 2
    
  # LoRA configuration
  loras:
    high_node_id: 416
    low_node_id: 471
    action_type: "add_lora_pair"
    max_loras: 5

# Input definitions with node mappings
inputs:
  - id: "duration"
    type: "slider"
    label: "Duration"
    min: 1.0
    max: 10.0
    step: 0.5
    default: 5.0
    node_mapping: "duration"  # References node_mapping above
    
  - id: "size_x"
    type: "slider"
    label: "Width"
    min: 512
    max: 1920
    step: 64
    default: 896
    node_mapping: "size_x"
    
  - id: "enable_interpolation"
    type: "toggle"
    label: "Enable Interpolation"
    default: true
    node_mapping: "enable_interpolation"
    
  - id: "loras"
    type: "lora_pair_list"
    label: "LoRA Pairs"
    max_items: 5
    node_mapping: "loras"
```

## Implementation Strategy

### Phase 1: Action Generator

Create a function that converts UI input to change actions:

```python
def generate_change_actions(ui_inputs: Dict, node_mapping: Dict) -> List[Dict]:
    """Convert UI inputs to change actions using node mapping."""
    actions = []
    
    for input_id, value in ui_inputs.items():
        mapping = node_mapping.get(input_id)
        if not mapping:
            continue
            
        if mapping["action_type"] == "modify_widget":
            actions.append({
                "type": "modify_widget",
                "node_id": mapping["node_id"],
                "widget_index": mapping["widget_indices"][0],
                "new_value": value
            })
        elif mapping["action_type"] == "toggle_node_mode":
            mode = mapping["enabled_mode"] if value else mapping["disabled_mode"]
            actions.append({
                "type": "toggle_node_mode",
                "node_ids": mapping["node_ids"],
                "new_mode": mode
            })
        # ... handle other action types
    
    return actions
```

### Phase 2: Action Applier

Implement the action application logic:

```python
class WorkflowModifier:
    def __init__(self, base_workflow_path: str):
        with open(base_workflow_path) as f:
            self.workflow = json.load(f)
    
    def apply_actions(self, actions: List[Dict]) -> Dict:
        """Apply a list of change actions to the workflow."""
        for action in actions:
            self.apply_single_action(action)
        return self.workflow
    
    def apply_single_action(self, action: Dict):
        """Apply one change action."""
        # Implementation based on pseudocode above
        pass
```

### Phase 3: Validation

Verify that changes don't break the workflow:

```python
def validate_workflow(workflow: Dict, changes: List[Dict]) -> List[str]:
    """Validate that changes are valid."""
    errors = []
    
    for change in changes:
        # Check node exists
        if not node_exists(workflow, change["node_id"]):
            errors.append(f"Node {change['node_id']} not found")
        
        # Check widget indices are valid
        # Check mode values are valid
        # etc.
    
    return errors
```

## Usage Example

```python
# Load configuration
with open("IMG_to_VIDEO.webui.yml") as f:
    config = yaml.safe_load(f)

# User inputs from UI
ui_inputs = {
    "duration": 8.0,
    "size_x": 1234,
    "steps": 30,
    "enable_interpolation": False,
    "loras": [
        {
            "high": "NSFW-22-H-e8.safetensors",
            "low": "NSFW-22-L-e8.safetensors",
            "strength": 1.0
        }
    ]
}

# Generate actions
actions = generate_change_actions(ui_inputs, config["node_mapping"])

# Apply to workflow
modifier = WorkflowModifier(config["workflow_file"])
modified_workflow = modifier.apply_actions(actions)

# Save result
with open("output_workflow.json", "w") as f:
    json.dump(modified_workflow, f, indent=2)
```

## Extensibility

### Adding New Action Types

To add a new action type:

1. Define the action structure in this document
2. Add handling in `apply_single_action()`
3. Add generator logic in `generate_change_actions()`
4. Update the YAML schema if needed

### Adding New Parameters

To add a new parameter:

1. Identify the node ID and widget indices using diff analysis
2. Add entry to `node_mapping` in YAML
3. Add input definition to `inputs` array
4. No code changes needed if using existing action types

## Validation and Testing

Recommend testing strategy:

1. **Unit tests**: Test each action type individually
2. **Integration tests**: Apply actions and verify workflow structure
3. **Functional tests**: Run modified workflows in ComfyUI and verify output
4. **Regression tests**: Compare with known-good modified workflows
