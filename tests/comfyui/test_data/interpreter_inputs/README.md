# Workflow Interpreter Test Inputs

This directory contains 26 test input files for comprehensive testing of the workflow interpreter system.

## File Naming Convention

Files are named: `{test_number}_{test_description}_{expected_hash}.json`

- **test_number**: Sequential 00-25
- **test_description**: Short identifier of what's being tested
- **expected_hash**: 8-character SHA256 hash of expected output workflow

## Test Coverage

### Scalar Parameters (10 tests)
- Duration: 8s, 5s (revert)
- Dimensions: X=1234, Y=1234
- Steps: 30
- CFG: 5.0
- Frame rate: 20
- Speed: 10
- Seed: 123451234512345
- Upscale ratio: 1.5

### LoRA Configuration (2 tests)
- Single LoRA pair
- Two LoRA pairs

### Feature Toggles (14 tests)
- Output enhancement: save_last_frame, interpolation, upscaler, upscale+interp
- Quality: video_enhancer, cfg_zero_star, speed_regulation, normalized_attention
- Performance: magcache, block_swap, torch_compile, vram_reduction (50%)
- Auto-prompting: enable/disable

## File Structure

Each JSON file contains:
```json
{
  "description": "Human-readable description",
  "test_id": "unique_test_identifier",
  "expected_hash": "8char_hash",
  "workflow_file": "path/to/expected/workflow.json",
  "inputs": {
    "basic_settings": { ... },
    "generation_parameters": { ... },
    "model_selection": { ... },
    "advanced_features": { ... }
  }
}
```

## Usage

These files are used by:
- `test_interpreter_suite.py`: Automated testing
- `test_validator.py`: Test input validation
- Manual testing and debugging

## Modification

To update test inputs:
1. Edit the relevant JSON file
2. Modify only the changed parameters in `inputs` section
3. Update `expected_hash` if workflow output should differ
4. Run validation: `python tests/comfyui/test_validator.py`
5. Run test suite: `python tests/comfyui/test_interpreter_suite.py`
