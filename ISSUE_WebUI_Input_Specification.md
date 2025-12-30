# Issue: Revise WebUI Input File Generation to Match WorkflowInterpreter Specification

## Summary
Update the WebUI application's input file generation to produce JSON files that conform to the WorkflowInterpreter's expected input format. The current implementation has discrepancies in structure, field naming, and value types that need to be corrected.

## Background
The WorkflowInterpreter expects a specific JSON structure with nested dictionaries organized by functional category. The WebUI currently generates form data that doesn't match this specification, leading to integration issues.

## Required JSON Structure

### Top-Level Structure
```json
{
  "description": "Human-readable description of the configuration",
  "test_id": "unique_identifier_for_this_configuration",
  "notes": "Optional additional notes",
  "inputs": {
    "basic_settings": { ... },
    "generation_parameters": { ... },
    "model_selection": { ... },
    "advanced_features": { ... }
  }
}
```

## Detailed Field Specifications

### 1. Basic Settings (`inputs.basic_settings`)
```json
{
  "input_image": "filename.jpeg",           // String: filename only (not full path)
  "positive_prompt": "text prompt",         // String
  "negative_prompt": "text prompt",         // String
  "seed": 701609645127340                   // Integer or Float (flexible)
}
```

**Field Rules:**
- `input_image`: Optional (null if not provided). Must be filename only, no path components.
- `seed`: Accept both int and float, but prefer integer for large values
- Prompts: String values, can be empty strings

### 2. Generation Parameters (`inputs.generation_parameters`)
```json
{
  "size_x": 768,                           // Integer: width in pixels
  "size_y": 1024,                          // Integer: height in pixels  
  "duration": 5.0,                         // Float: video duration in seconds
  "steps": 20,                             // Integer: inference steps
  "cfg": 3.0,                              // Float: classifier-free guidance scale
  "frame_rate": 16.0,                      // Float: frames per second
  "speed": 7.0,                            // Float: motion speed multiplier
  "upscale_ratio": 2.0                     // Float: upscaling ratio
}
```

**Field Rules:**
- `size_x`, `size_y`, `steps`: Must be integers
- `duration`, `cfg`, `frame_rate`, `speed`, `upscale_ratio`: Must be floats
- All fields required

### 3. Model Selection (`inputs.model_selection`)
```json
{
  "main_model": {
    "high_noise": "path/to/high_noise_model.safetensors",
    "low_noise": "path/to/low_noise_model.safetensors"
  },
  "loras": [
    {
      "high_noise": "path/to/lora_high.safetensors",
      "low_noise": "path/to/lora_low.safetensors",
      "strength": 1.0                      // Float: 0.0 to 1.0
    }
  ],
  "clip_model": "path/to/clip_model.safetensors",
  "vae_model": "path/to/vae_model.safetensors",
  "upscale_model": "path/to/upscale_model.pth"
}
```

**Field Rules:**
- `loras`: Array of LoRA objects. Can be empty array `[]` if no LoRAs.
- Each LoRA must have `high_noise`, `low_noise`, and `strength` fields
- All model paths are strings (relative or absolute paths accepted)

### 4. Advanced Features (`inputs.advanced_features`)

#### 4.1 Output Enhancement (`inputs.advanced_features.output_enhancement`)

**SIMPLIFIED: Three Independent Output Pipelines**

The system has **three separate output pipelines**. Each is controlled by a single toggle:

```json
{
  "save_last_frame": false,                // Boolean: Save final frame as image
  "save_original_output": true,            // Boolean: Save original video output
  "save_interpoled_output": false,         // Boolean: Standalone Interpolation (nodes 431 + 433)
  "save_upscaled_output": false,           // Boolean: Standalone Upscaler (nodes 385 + 419)
  "save_upint_output": true                // Boolean: Combined UPINT (nodes 442 + 437 + 443)
}
```

**Pipeline Details:**

1. **`save_interpoled_output`**: Standalone Interpolation Pipeline
   - Enables processing node 431 (RIFE interpolation)
   - Enables save node 433 (Save Interpoled)
   - Use when you want interpolated video as standalone output

2. **`save_upscaled_output`**: Standalone Upscaler Pipeline
   - Enables processing node 385 (Upscaler)
   - Enables save node 419 (Save Upscaled)
   - Use when you want upscaled video as standalone output

3. **`save_upint_output`**: UPINT Pipeline (Combined)
   - Enables processing nodes 442 (RIFE) + 437 (Upscaler)
   - Enables save node 443 (Save UPINT)
   - Use when you want combined upscale+interpolation output

**All three pipelines are completely independent** - you can enable any combination.

#### 4.2 Quality Enhancements (`inputs.advanced_features.quality_enhancements`)
```json
{
  "enable_video_enhancer": true,           // Boolean
  "enable_cfg_zero_star": true,            // Boolean
  "enable_speed_regulation": true,         // Boolean
  "enable_normalized_attention": true      // Boolean
}
```

#### 4.3 Performance/Memory (`inputs.advanced_features.performance_memory`)
```json
{
  "enable_magcache": true,                 // Boolean
  "enable_torch_compile": false,           // Boolean
  "enable_block_swap": true,               // Boolean
  "vram_reduction": 100                    // Integer: 0-100 (percentage)
}
```

#### 4.4 Automatic Prompting (`inputs.advanced_features.automatic_prompting`)
```json
{
  "enable_auto_prompt": true               // Boolean
}
```

## Complete Example: UPINT-Only Output

```json
{
  "description": "UPINT only output with 2 LoRAs - Disable standalone outputs, enable combined upscale+interpolation",
  "test_id": "upint_only_two_loras",
  "notes": "Demonstrates UPINT pipeline with multiple LoRAs and custom size",
  
  "inputs": {
    "basic_settings": {
      "input_image": "example_image.jpeg",
      "positive_prompt": "The young woman turns towards the camera",
      "negative_prompt": "blurry, static, low quality",
      "seed": 701609645127340
    },
    "generation_parameters": {
      "size_x": 768,
      "size_y": 1024,
      "duration": 5.0,
      "steps": 20,
      "cfg": 3.0,
      "frame_rate": 16.0,
      "speed": 7.0,
      "upscale_ratio": 2.0
    },
    "model_selection": {
      "main_model": {
        "high_noise": "wan2.2_i2v_high_noise_14B_fp16.safetensors",
        "low_noise": "wan2.2_i2v_low_noise_14B_fp16.safetensors"
      },
      "loras": [
        {
          "high_noise": "lora1_high.safetensors",
          "low_noise": "lora1_low.safetensors",
          "strength": 1.0
        },
        {
          "high_noise": "lora2_high.safetensors",
          "low_noise": "lora2_low.safetensors",
          "strength": 0.8
        }
      ],
      "clip_model": "umt5_xxl_fp16.safetensors",
      "vae_model": "wan_2.1_vae.safetensors",
      "upscale_model": "RealESRGAN_x4plus.pth"
    },
    "advanced_features": {
      "output_enhancement": {
        "save_last_frame": false,
        "save_original_output": true,
        "save_interpoled_output": false,
        "save_upscaled_output": false,
        "save_upint_output": true
      },
      "quality_enhancements": {
        "enable_video_enhancer": true,
        "enable_cfg_zero_star": true,
        "enable_speed_regulation": true,
        "enable_normalized_attention": true
      },
      "performance_memory": {
        "enable_magcache": true,
        "enable_torch_compile": false,
        "enable_block_swap": true,
        "vram_reduction": 100
      },
      "automatic_prompting": {
        "enable_auto_prompt": true
      }
    }
  }
}
```

## Common Mistakes to Avoid

### ❌ Incorrect Field Names
```json
{
  "interpolation": true,          // WRONG: Should be "enable_interpolation"
  "upscaler": true,               // WRONG: Should be "use_upscaler"
  "save_interpolation": true,     // WRONG: Should be "save_interpoled_output"
  "enable_upscaler": true         // WRONG: Should be "use_upscaler"
}
```

### ❌ Wrong Types
```json
{
  "duration": 5,                  // WRONG: Must be float (5.0)
  "steps": 20.0,                  // WRONG: Must be integer (20)
  "seed": "701609645127340",      // WRONG: Must be number, not string
  "enable_interpolation": "true"  // WRONG: Must be boolean, not string
}
```

### ❌ Wrong Structure
```json
{
  "size": "768x1024",             // WRONG: Must be separate size_x and size_y integers
  "loras": "lora1,lora2",         // WRONG: Must be array of objects
  "model": "high_noise_model"     // WRONG: Must be object with high_noise and low_noise
}
```

### ❌ Field Ordering Issues
```json
{
  "output_enhancement": {
    "save_interpoled_output": true,
    "enable_interpolation": true,
    "enable_upscale_interpolation": false  // WRONG: This disables nodes 442/437 AFTER they were enabled
  }
}
```
**Fix:** Move `enable_upscale_interpolation` to the FIRST position.

## Implementation Tasks

- [ ] Update form data collection to use correct field names
- [ ] Implement proper type conversions (int vs float)
- [ ] Restructure output to match nested dictionary format
- [ ] Ensure `enable_upscale_interpolation` is serialized first in output_enhancement
- [ ] Add validation for required fields
- [ ] Handle optional fields (null values) correctly
- [ ] Implement LoRA array structure with high/low noise pairs
- [ ] Test with WorkflowInterpreter to verify compatibility

## Testing Checklist

Test the generated JSON with these scenarios:

- [ ] Basic configuration (no LoRAs, default settings)
- [ ] Single LoRA configuration
- [ ] Multiple LoRAs (2+) configuration
- [ ] UPINT-only output (standalone pipelines disabled)
- [ ] Standalone interpolation only
- [ ] Standalone upscaler only
- [ ] All outputs enabled
- [ ] Custom size (non-default width/height)
- [ ] Custom seed values (very large integers)
- [ ] All boolean flags toggled
- [ ] Input image specified vs null

## Reference Files

- **Valid Example**: `/tests/comfyui/test_data/interpreter_inputs/39_upint_only_output_two_loras.json`
- **YAML Mapping**: `/IMG_to_VIDEO.webui.yml` (lines 100-145)
- **Test Suite**: `/tests/comfyui/test_interpreter_integration.py` (39 passing tests)

## Acceptance Criteria

✅ Generated JSON files pass validation with WorkflowInterpreter
✅ All field names match specification exactly
✅ All data types are correct (int vs float)
✅ Nested structure matches the four-section format
✅ Field ordering prevents action conflicts
✅ LoRA arrays are properly formatted
✅ Boolean values are true booleans, not strings

## Priority
**HIGH** - This blocks integration between the WebUI and the workflow interpreter system.

---
*Last Updated: 2025-12-30*
*Based on: WorkflowInterpreter Test Suite (39 tests passing)*
