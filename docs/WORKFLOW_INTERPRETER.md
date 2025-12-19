# Workflow Interpreter

The Workflow Interpreter applies user inputs to ComfyUI workflows using declarative wrapper configurations.

## Overview

The interpreter implements the workflow modification system designed in [WORKFLOW_CHANGE_ACTIONS.md](WORKFLOW_CHANGE_ACTIONS.md). It takes three inputs:

1. **Base Workflow** (`*.json`): Original ComfyUI workflow file
2. **Wrapper Config** (`*.webui.yml`): Declarative mapping from UI inputs to workflow nodes
3. **User Inputs** (`*_inputs.json`): User-provided values for all parameters

And produces a modified workflow JSON file with the user's settings applied.

## Usage

### Basic Usage

```python
from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter

# Initialize with wrapper config
interpreter = WorkflowInterpreter("IMG_to_VIDEO.webui.yml")

# Process with user inputs
modified_workflow = interpreter.process(
    inputs_path="IMG_to_VIDEO_inputs.json",
    output_path="outputs/workflows/my_generated_workflow.json"
)
```

### Command Line

```bash
python scripts/test_interpreter.py
```

## File Structure

### 1. Base Workflow (`WAN2.2_IMG_to_VIDEO_Base_47e91030.json`)

Standard ComfyUI workflow JSON with nodes, links, and canvas layout. This is your "template" workflow that defines the structure.

### 2. Wrapper Config (`IMG_to_VIDEO.webui.yml`)

Declarative configuration that maps user-facing inputs to internal workflow nodes:

```yaml
node_mapping:
  duration:
    node_id: 426
    node_type: "mxSlider"
    widget_indices: [0, 1]
    action_type: "modify_widget"
    
  enable_interpolation:
    node_ids: [431, 363, 370, 432]
    node_type: "VHS_FILMC_Interpolation"
    action_type: "toggle_node_mode"
    enabled_mode: 0
    disabled_mode: 2
```

### 3. User Inputs (`IMG_to_VIDEO_inputs.json`)

User-facing values organized by category:

```json
{
  "inputs": {
    "basic_settings": {
      "positive_prompt": "The subject moves naturally...",
      "seed": 701609645127340
    },
    "generation_parameters": {
      "duration": 5.0,
      "steps": 20,
      "cfg": 3.5
    },
    "advanced_features": {
      "quality_enhancements": {
        "enable_interpolation": true
      }
    }
  }
}
```

## Architecture

### Change Actions

The interpreter uses four elementary change action types:

1. **ModifyWidgetAction**: Change scalar values (sliders, seeds)
   - Updates `widgets_values` array at specified indices
   - Example: duration, steps, CFG scale

2. **ModifyVectorWidgetAction**: Change coordinated multi-dimensional values
   - Updates multiple related indices (e.g., X/Y dimensions)
   - Example: size_x and size_y both modify node 83

3. **ToggleNodeModeAction**: Enable/disable node execution
   - Changes `mode` field (0=enabled, 2=bypassed, 4=muted)
   - Can affect multiple nodes simultaneously
   - Example: enable_interpolation affects 4 nodes

4. **AddLoRAPairAction**: Add LoRA models to high/low noise loaders
   - Inserts LoRA configuration into Power Lora Loader nodes
   - Maintains high/low noise pairing

### Processing Pipeline

```
1. Load wrapper config → Parse node_mapping
2. Load base workflow → Index nodes by ID
3. Load user inputs → Flatten nested structure
4. Generate actions → Convert inputs to change actions
5. Apply actions → Modify workflow nodes
6. Calculate hash → Version tracking
7. Export workflow → Save modified JSON
```

## Implementation Details

### Widget Value Patterns

Different node types have different widget structures:

- **mxSlider**: `[value, value, step]` - value duplicated at indices 0-1
- **mxSlider2D**: `[x, x, y, y, isfloatX, isfloatY]` - X at 0-1, Y at 2-3
- **RandomNoise**: `[seed, control]` - seed at index 0
- **Power Lora Loader**: Complex nested structure with LoRA arrays

### Node Mode Values

- `0`: Enabled (executes normally)
- `2`: Bypassed (passes through, optimized)
- `4`: Muted (completely disabled)

### Hash Calculation

Generated workflows get an 8-character hex hash suffix for version tracking:
- Uses SHA256 of sorted JSON
- Enables deduplication and tracking
- Format: `workflow_name_{hash8chars}.json`

## Testing

Test the interpreter with default values:

```bash
python scripts/test_interpreter.py
```

Expected output:
- Loads wrapper config
- Generates ~21 actions from 30 inputs
- Applies modifications
- Exports workflow with hash
- Workflow should be functionally identical to original (since inputs match)

## Extending

### Adding New Parameters

1. **Add to wrapper YAML** (`node_mapping` section):
   ```yaml
   my_new_param:
     node_id: 123
     node_type: "mxSlider"
     widget_indices: [0, 1]
     action_type: "modify_widget"
   ```

2. **Add to inputs JSON**:
   ```json
   {
     "inputs": {
       "generation_parameters": {
         "my_new_param": 5.0
       }
     }
   }
   ```

3. **No code changes required** - interpreter handles it automatically!

### Adding New Action Types

If you need a new modification pattern:

1. Create new dataclass in `workflow_interpreter.py`
2. Add to `ChangeAction` union type
3. Implement `_make_*_action()` method in `WorkflowInterpreter`
4. Implement `_apply_*()` method for execution
5. Add to `generate_actions()` and `apply_actions()` dispatch

## Known Issues

- Some node IDs in wrapper config may be outdated (see warnings)
  - These are from different workflow versions
  - Only affects unused features
  - Update node_ids in YAML to fix

- Float/int type coercion
  - Inputs use JSON types (integers become floats)
  - Generally safe due to Python's type flexibility
  - May cause minor precision differences

## Future Enhancements

- [ ] Web UI generator from YAML config
- [ ] Direct ComfyUI API submission
- [ ] Interactive node ID discovery tool
- [ ] Workflow validation against config
- [ ] Batch processing multiple input sets
- [ ] Diffing tool for before/after comparison
