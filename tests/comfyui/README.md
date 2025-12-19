# Workflow Interpreter Test Suite

This directory contains a comprehensive test suite for the workflow interpreter system.

## Test Structure

### Test Input Files (`test_data/interpreter_inputs/`)

26 test input files covering all workflow modifications documented in [outputs/workflows/README.md](../../outputs/workflows/README.md):

| Test ID | File | Description | Expected Hash |
|---------|------|-------------|---------------|
| 00 | `00_original_47e91030.json` | Baseline - original workflow | 47e91030 |
| 01 | `01_duration_8_7c833bc9.json` | Duration = 8 seconds | 7c833bc9 |
| 02 | `02_duration_5_d045b229.json` | Duration = 5 seconds (back to original) | d045b229 |
| 03 | `03_size_x_1234_2ac2a354.json` | X-size = 1234 | 2ac2a354 |
| 04 | `04_size_y_1234_8f0a73a6.json` | Y-size = 1234 | 8f0a73a6 |
| 05 | `05_steps_30_f353077e.json` | Steps = 30 | f353077e |
| 06 | `06_cfg_5_ea8fa43c.json` | CFG = 5.0 | ea8fa43c |
| 07 | `07_frame_rate_20_a9bf4a72.json` | Frame rate = 20 | a9bf4a72 |
| 08 | `08_speed_10_4b3df0f7.json` | Speed = 10 | 4b3df0f7 |
| 09 | `09_seed_123451234512345_7cd43527.json` | Seed = 123451234512345 | 7cd43527 |
| 10 | `10_one_lora_b70c5f99.json` | Add 1 LoRA pair | b70c5f99 |
| 11 | `11_two_loras_4f7a4322.json` | Add 2 LoRA pairs | 4f7a4322 |
| 12 | `12_save_last_frame_yes_56adc96e.json` | Enable save last frame | 56adc96e |
| 13 | `13_interpolation_no_1fd5352d.json` | Disable interpolation | 1fd5352d |
| 14 | `14_upscale_interp_yes_2887ac38.json` | Enable upscale & interpolation | 2887ac38 |
| 15 | `15_upscaler_yes_ed6c5714.json` | Enable upscaler | ed6c5714 |
| 16 | `16_video_enhancer_no_a801da91.json` | Disable video enhancer | a801da91 |
| 17 | `17_cfg_zero_star_no_511510da.json` | Disable CFG Zero Star | 511510da |
| 18 | `18_speed_regulation_no_0ac7400c.json` | Disable speed regulation | 0ac7400c |
| 19 | `19_normalized_attention_no_e6f42924.json` | Disable normalized attention | e6f42924 |
| 20 | `20_magcache_no_d55a327a.json` | Disable MagCache | d55a327a |
| 21 | `21_block_swap_no_50547ca6.json` | Disable BlockSwap | 50547ca6 |
| 22 | `22_torch_compile_yes_8b7d98fb.json` | Enable TorchCompile | 8b7d98fb |
| 23 | `23_vram_reduction_50_f5be93ce.json` | VRAM reduction = 50% | f5be93ce |
| 24 | `24_auto_prompt_no_f130146e.json` | Disable automatic prompting | f130146e |
| 25 | `25_upscale_ratio_1_5_4e40676c.json` | Upscale ratio = 1.5 | 4e40676c |

Each test file contains:
- `description`: Human-readable test description
- `test_id`: Unique test identifier
- `expected_hash`: Expected workflow hash after modification
- `workflow_file`: Path to expected output workflow
- `inputs`: Complete input values for workflow generation

## Test Scripts

### `test_interpreter_suite.py`

Comprehensive test runner that:
1. Discovers all test input files
2. For each test:
   - Loads test inputs
   - Generates workflow using interpreter
   - Calculates hash of generated workflow
   - Compares with expected hash
3. Reports detailed results with diagnostics

**Usage:**
```bash
# Run all tests
python tests/comfyui/test_interpreter_suite.py

# Or via pytest
pytest tests/comfyui/test_interpreter_suite.py -v
```

**Output:**
- Per-test pass/fail status
- Generated vs expected hash comparison
- Action count for each test
- Detailed node-level differences for failures
- Summary with pass/fail/error counts

### `test_validator.py`

Validates test input files against their expected workflow files by:
1. Loading each test's expected workflow
2. Extracting actual values from workflow nodes
3. Comparing with test input values
4. Reporting mismatches

**Usage:**
```bash
# Validate all test files
python tests/comfyui/test_validator.py
```

**Validations performed:**
- Scalar parameters (duration, size_x, size_y, steps, cfg, frame_rate, speed, seed, upscale_ratio, vram_reduction)
- Boolean feature toggles (by checking node mode: 0=enabled, 2=disabled)
- LoRA configuration (presence check)
- Hash consistency with filenames

## Test Categories

### Scalar Value Modifications (Tests 01-09, 25)
Tests single numeric parameter changes:
- Generation parameters: duration, dimensions, steps, CFG, frame rate, speed, upscale ratio
- Random seed
- VRAM reduction percentage

### LoRA Additions (Tests 10-11)
Tests dynamic LoRA insertion:
- Single LoRA pair (high + low noise)
- Multiple LoRA pairs with different strengths

### Feature Toggles (Tests 12-24)
Tests enabling/disabling optional features via node mode changes:

**Output Enhancement:**
- Save last frame
- Interpolation
- Upscaler
- Upscale + interpolation

**Quality Enhancements:**
- Video enhancer
- CFG Zero Star
- Speed regulation
- Normalized attention

**Performance/Memory:**
- MagCache
- BlockSwap
- TorchCompile

**Automatic Prompting:**
- Auto-prompt generation

## Running Tests

### Full Test Suite
```bash
# From repository root
python tests/comfyui/test_interpreter_suite.py
```

### Validate Test Inputs
```bash
# Verify test files match expected workflows
python tests/comfyui/test_validator.py
```

### Individual Test Debugging
```bash
# Run interpreter on specific test input
python -c "
from src.browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter
interp = WorkflowInterpreter('IMG_to_VIDEO.webui.yml')
result = interp.process(
    'tests/comfyui/test_data/interpreter_inputs/01_duration_8_7c833bc9.json',
    '/tmp/test_output.json'
)
print(f'Generated hash: {interp._calculate_hash(result)}')
"
```

## Expected Results

All 26 tests should pass with:
- Generated hash matching expected hash
- Action count varying by test (1-21 actions typical)
- No errors during workflow generation

Failure modes to investigate:
- Hash mismatch: Workflow structure differs from expected
- Missing nodes: Node mapping references outdated IDs
- Wrong values: Input-to-node mapping incorrect
- Action errors: Widget pattern mismatch

## Extending Tests

To add new test cases:

1. **Create modified workflow** via ComfyUI or scripts
2. **Download workflow** with hash suffix: `python scripts/download_workflow.py <url> <description>`
3. **Create test input file**:
   ```bash
   cp tests/comfyui/test_data/interpreter_inputs/00_original_47e91030.json \
      tests/comfyui/test_data/interpreter_inputs/26_new_test_<hash>.json
   ```
4. **Update test input**:
   - Change `test_id`, `description`, `expected_hash`
   - Modify relevant input values
   - Update `workflow_file` path
5. **Add validation** to `test_validator.py` if needed
6. **Run test suite** to verify

## Continuous Integration

These tests validate:
- Interpreter correctly applies all modification types
- Hash-based versioning is stable
- Node mappings remain accurate
- Action generation logic is sound

Tests should be run:
- Before committing interpreter changes
- After updating node mappings in wrapper YAML
- When adding new workflow parameters
- After ComfyUI node updates
