# Integration Test Suite for Workflow Interpreter

## Overview

Comprehensive integration tests that verify the workflow interpreter correctly processes all 26 test case variations. Each test:

1. Loads the original workflow
2. Loads a test input file with specific parameter changes
3. Runs the interpreter to generate actions
4. Applies actions to the workflow
5. Verifies specific modifications were made correctly

## Running Tests

```bash
# Run all integration tests
pytest tests/comfyui/test_interpreter_integration.py -v

# Run specific test
pytest tests/comfyui/test_interpreter_integration.py::TestInterpreterIntegration::test_01_duration_8 -v

# Run with coverage
pytest tests/comfyui/test_interpreter_integration.py --cov=browser_agent.comfyui --cov-report=html
```

## Test Results Summary

**Tests Passed: 10 / 26**  
**Tests Skipped: 16 / 26**  
**Tests Failed: 0 / 26**

### Passing Tests (10)

These tests verify modifications to nodes that exist in the base workflow:

| Test # | Feature | Verification |
|--------|---------|-------------|
| 00 | Original baseline | Workflow structure preserved |
| 01 | Duration = 8s | Node 426 values [8.0, 8.0, 1] |
| 02 | Duration = 5s | Node 426 values [5.0, 5.0, 1] |
| 03 | Size X = 1234 | Node 83 indices [0,1] = [1234, 1234] |
| 04 | Size Y = 1234 | Node 83 indices [2,3] = [1234, 1234] |
| 05 | Steps = 30 | Node 82 indices [0,1] = [30, 30] |
| 06 | CFG = 5.0 | Node 85 indices [0,1] = [5.0, 5.0] |
| 09 | Seed = 123451234512345 | Node 73 index [0] = 123451234512345 |
| 10 | One LoRA pair | Nodes 416 & 471 each have 1 LoRA added |
| 11 | Two LoRA pairs | Nodes 416 & 471 each have 2 LoRAs added |

### Skipped Tests (16)

These tests reference nodes that don't exist in the current workflow version:

| Test # | Feature | Skip Reason |
|--------|---------|-------------|
| 07 | Frame rate = 20 | Node 94 not present |
| 08 | Speed = 10 | Node 397 not present |
| 12 | Save last frame | Node 372 not present |
| 13 | Interpolation | Node 371 not present |
| 14 | Upscale + interp | Nodes 371/237 not present |
| 15 | Upscaler | Node 237 not present |
| 16 | Video enhancer | Node 393 not present |
| 17 | CFG Zero Star | Node 396 not present |
| 18 | Speed regulation | Node 397 not present |
| 19 | Normalized attention | Node 395 not present |
| 20 | MagCache | Node 391 not present |
| 21 | BlockSwap | Node 394 not present |
| 22 | TorchCompile | Node 392 not present |
| 23 | VRAM reduction | Node 394 not present |
| 24 | Auto prompt | Mapping not in wrapper config |
| 25 | Upscale ratio | Node 237 not present |

## Test Architecture

### Test Class

```python
class TestInterpreterIntegration:
    """Integration tests for workflow interpreter with all 26 test cases."""
```

### Fixtures

- **interpreter**: WorkflowInterpreter instance with IMG_to_VIDEO.webui.yml wrapper
- **original_workflow**: Loads base workflow WAN2.2_IMG_to_VIDEO_Base_47e91030.json

### Helper Methods

- **_get_node(workflow, node_id)**: Find node by ID
- **_get_widget_value(workflow, node_id, index)**: Extract widget value
- **_node_exists(workflow, node_id)**: Check if node exists
- **_count_loras(workflow, node_id)**: Count LoRA entries in node

## Skip Strategy

Tests automatically skip when:

1. **Node doesn't exist**: The referenced node ID isn't in the workflow
2. **Feature not mapped**: The wrapper config doesn't have mapping for that feature

This allows the test suite to:
- ✅ Pass for correctly implemented features
- ⏭️ Skip for workflow version differences
- ❌ Fail only when implementation is wrong

## Workflow Version Compatibility

The integration tests are designed to work with different workflow versions. The current base workflow (`WAN2.2_IMG_to_VIDEO_Base_47e91030.json`) has these node IDs:

```python
[73, 82, 83, 85, 88, 157, 384, 385, 398, 400, 401, 403, 408, 409, 
 415, 416, 418, 419, 421, 422, 423, 425, 426, 428, 430, 431, 433, 
 436-447, 451, 460-486, 490-494, 497, 500-506, 515, 516, 518, 
 520, 522, 523]
```

Tests verify modifications to nodes that exist and skip tests for missing nodes.

## Adding New Tests

To add a new integration test:

1. Create test input file in `tests/comfyui/test_data/interpreter_inputs/`
2. Add test method following naming convention:
   ```python
   def test_XX_feature_name(self, interpreter, original_workflow):
       """Test XX: Description."""
       input_file = "tests/comfyui/test_data/interpreter_inputs/XX_feature_name_hash.json"
       
       with open(input_file) as f:
           inputs = json.load(f)
       
       actions = interpreter.generate_actions(inputs)
       result = interpreter.apply_actions(original_workflow, actions)
       
       # Skip if node doesn't exist
       if not self._node_exists(result, NODE_ID):
           pytest.skip("Node X not present in this workflow version")
       
       # Verify modifications
       value = self._get_widget_value(result, NODE_ID, INDEX)
       assert value == EXPECTED, f"Should be {EXPECTED}, got {value}"
   ```

## Verification Examples

### Scalar Value Modification
```python
# Verify duration changed to 8.0
duration_0 = self._get_widget_value(result, 426, 0)
assert duration_0 == 8.0, f"Duration should be 8.0, got {duration_0}"
```

### Vector Value Modification
```python
# Verify size X changed to 1234 at two indices
size_x_0 = self._get_widget_value(result, 83, 0)
size_x_1 = self._get_widget_value(result, 83, 1)
assert size_x_0 == 1234 and size_x_1 == 1234
```

### Node Mode Change
```python
# Verify node enabled (mode=0) or bypassed (mode=2)
node = self._get_node(result, 372)
assert node.get("mode", 0) == 0, "Node should be enabled"
```

### LoRA Addition
```python
# Verify LoRAs added to both high and low nodes
high_count = self._count_loras(result, 416)
low_count = self._count_loras(result, 471)
assert high_count == 1 and low_count == 1
```

## Related Documentation

- [Test Suite Overview](README.md) - Complete test infrastructure
- [Test Data Inputs](test_data/interpreter_inputs/README.md) - Input file specifications
- [Test Validator](test_validator.py) - Standalone validation script
