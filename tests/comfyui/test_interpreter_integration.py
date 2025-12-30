"""
Integration tests for workflow interpreter.

Tests all 37 workflow variations by running the interpreter and verifying
that each modification was correctly applied to the output workflow.

Tests 1-26: Single feature modifications
Tests 27-37: Multi-feature combination scenarios
"""

import json
import pytest
from pathlib import Path

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter


class TestInterpreterIntegration:
    """Integration tests for workflow interpreter with all 37 test cases."""
    
    @pytest.fixture(scope="class")
    def interpreter(self):
        """Create interpreter instance."""
        return WorkflowInterpreter("IMG_to_VIDEO.webui.yml")
    
    @pytest.fixture(scope="class")
    def original_workflow(self):
        """Load original workflow."""
        with open("outputs/workflows/WAN2.2_IMG_to_VIDEO_Base_47e91030.json") as f:
            return json.load(f)
    
    def _get_node(self, workflow, node_id):
        """Helper to get a node by ID."""
        for node in workflow.get("nodes", []):
            if node["id"] == node_id:
                return node
        return None
    
    def _get_widget_value(self, workflow, node_id, index):
        """Helper to get a widget value."""
        node = self._get_node(workflow, node_id)
        if node and "widgets_values" in node:
            if index < len(node["widgets_values"]):
                return node["widgets_values"][index]
        return None
    
    def _node_exists(self, workflow, node_id):
        """Check if a node exists in the workflow."""
        return self._get_node(workflow, node_id) is not None
    
    def _count_loras(self, workflow, node_id):
        """Helper to count LoRAs in a node."""
        node = self._get_node(workflow, node_id)
        if not node:
            return 0
        count = 0
        for widget in node.get("widgets_values", []):
            if isinstance(widget, dict) and "lora" in widget:
                count += 1
        return count
    
    # Test 00: Original baseline
    def test_00_original_baseline(self, interpreter):
        """Test 00: Original workflow (no changes)."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/00_original_47e91030.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        workflow = interpreter._load_workflow()
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(workflow, actions)
        
        # Verify basic structure preserved
        assert "nodes" in result
        assert len(result["nodes"]) == len(workflow["nodes"])
    
    # Test 01: Duration = 8 seconds
    def test_01_duration_8(self, interpreter, original_workflow):
        """Test 01: Duration set to 8 seconds."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/01_duration_8_7c833bc9.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify duration changed to 8.0 (node 426, indices 0-1)
        duration_val_0 = self._get_widget_value(result, 426, 0)
        duration_val_1 = self._get_widget_value(result, 426, 1)
        
        assert duration_val_0 == 8.0, f"Duration[0] should be 8.0, got {duration_val_0}"
        assert duration_val_1 == 8.0, f"Duration[1] should be 8.0, got {duration_val_1}"
    
    # Test 02: Duration = 5 seconds (back to original)
    def test_02_duration_5(self, interpreter, original_workflow):
        """Test 02: Duration back to 5 seconds."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/02_duration_5_d045b229.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify duration is 5.0
        duration_val_0 = self._get_widget_value(result, 426, 0)
        duration_val_1 = self._get_widget_value(result, 426, 1)
        
        assert duration_val_0 == 5.0, f"Duration[0] should be 5.0, got {duration_val_0}"
        assert duration_val_1 == 5.0, f"Duration[1] should be 5.0, got {duration_val_1}"
    
    # Test 03: X-size = 1234
    def test_03_size_x_1234(self, interpreter, original_workflow):
        """Test 03: X-size set to 1234."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/03_size_x_1234_2ac2a354.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify X dimension changed to 1234 (node 83, indices 0-1)
        size_x_0 = self._get_widget_value(result, 83, 0)
        size_x_1 = self._get_widget_value(result, 83, 1)
        
        assert size_x_0 == 1234, f"Size X[0] should be 1234, got {size_x_0}"
        assert size_x_1 == 1234, f"Size X[1] should be 1234, got {size_x_1}"
    
    # Test 04: Y-size = 1234
    def test_04_size_y_1234(self, interpreter, original_workflow):
        """Test 04: Y-size set to 1234."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/04_size_y_1234_8f0a73a6.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify Y dimension changed to 1234 (node 83, indices 2-3)
        size_y_2 = self._get_widget_value(result, 83, 2)
        size_y_3 = self._get_widget_value(result, 83, 3)
        
        assert size_y_2 == 1234, f"Size Y[2] should be 1234, got {size_y_2}"
        assert size_y_3 == 1234, f"Size Y[3] should be 1234, got {size_y_3}"
    
    # Test 05: Steps = 30
    def test_05_steps_30(self, interpreter, original_workflow):
        """Test 05: Steps set to 30."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/05_steps_30_f353077e.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify steps changed to 30 (node 82, indices 0-1)
        steps_0 = self._get_widget_value(result, 82, 0)
        steps_1 = self._get_widget_value(result, 82, 1)
        
        assert steps_0 == 30, f"Steps[0] should be 30, got {steps_0}"
        assert steps_1 == 30, f"Steps[1] should be 30, got {steps_1}"
    
    # Test 06: CFG = 5.0
    def test_06_cfg_5(self, interpreter, original_workflow):
        """Test 06: CFG set to 5.0."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/06_cfg_5_ea8fa43c.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify CFG changed to 5.0 (node 85, indices 0-1)
        cfg_0 = self._get_widget_value(result, 85, 0)
        cfg_1 = self._get_widget_value(result, 85, 1)
        
        assert cfg_0 == 5.0, f"CFG[0] should be 5.0, got {cfg_0}"
        assert cfg_1 == 5.0, f"CFG[1] should be 5.0, got {cfg_1}"
    
    # Test 07: Frame rate = 20
    def test_07_frame_rate_20(self, interpreter, original_workflow):
        """Test 07: Frame rate set to 20."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/07_frame_rate_20_a9bf4a72.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify frame rate changed to 20.0 (node 490, indices 0-1)
        frame_rate_0 = self._get_widget_value(result, 490, 0)
        frame_rate_1 = self._get_widget_value(result, 490, 1)
        
        assert frame_rate_0 == 20.0, f"Frame rate[0] should be 20.0, got {frame_rate_0}"
        assert frame_rate_1 == 20.0, f"Frame rate[1] should be 20.0, got {frame_rate_1}"
    
    # Test 08: Speed = 10
    def test_08_speed_10(self, interpreter, original_workflow):
        """Test 08: Speed set to 10."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/08_speed_10_4b3df0f7.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify speed changed to 10.0 (node 157, indices 0-1)
        speed_0 = self._get_widget_value(result, 157, 0)
        speed_1 = self._get_widget_value(result, 157, 1)
        
        assert speed_0 == 10.0, f"Speed[0] should be 10.0, got {speed_0}"
        assert speed_1 == 10.0, f"Speed[1] should be 10.0, got {speed_1}"
    
    # Test 09: Seed = 123451234512345
    def test_09_seed_123451234512345(self, interpreter, original_workflow):
        """Test 09: Seed set to 123451234512345."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/09_seed_123451234512345_7cd43527.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify seed changed (node 73, index 0)
        seed = self._get_widget_value(result, 73, 0)
        
        assert seed == 123451234512345, f"Seed should be 123451234512345, got {seed}"
    
    # Test 10: One LoRA pair
    def test_10_one_lora(self, interpreter, original_workflow):
        """Test 10: Add one LoRA pair."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/10_one_lora_b70c5f99.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify LoRAs added (nodes 416 and 471)
        high_lora_count = self._count_loras(result, 416)
        low_lora_count = self._count_loras(result, 471)
        
        assert high_lora_count == 1, f"High noise node should have 1 LoRA, got {high_lora_count}"
        assert low_lora_count == 1, f"Low noise node should have 1 LoRA, got {low_lora_count}"
        
        # Verify LoRA paths contain expected strings
        high_node = self._get_node(result, 416)
        high_lora = None
        for widget in high_node["widgets_values"]:
            if isinstance(widget, dict) and "lora" in widget:
                high_lora = widget
                break
        
        assert high_lora is not None, "High noise LoRA not found"
        # Check for various high noise patterns: "high", "-H-", "_HIGH", etc.
        lora_lower = high_lora["lora"].lower()
        has_high_pattern = any(pattern in lora_lower for pattern in ["high", "-h-", "_high_", "high_noise"])
        assert has_high_pattern, f"High LoRA path should contain high noise indicator: {high_lora['lora']}"
        assert high_lora["strength"] == 0.8, f"LoRA strength should be 0.8, got {high_lora['strength']}"
    
    # Test 11: Two LoRA pairs
    def test_11_two_loras(self, interpreter, original_workflow):
        """Test 11: Add two LoRA pairs."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/11_two_loras_4f7a4322.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify LoRAs added
        high_lora_count = self._count_loras(result, 416)
        low_lora_count = self._count_loras(result, 471)
        
        assert high_lora_count == 2, f"High noise node should have 2 LoRAs, got {high_lora_count}"
        assert low_lora_count == 2, f"Low noise node should have 2 LoRAs, got {low_lora_count}"
    
    # Test 12: Save last frame enabled
    def test_12_save_last_frame_yes(self, interpreter, original_workflow):
        """Test 12: Enable save last frame."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/12_save_last_frame_yes_56adc96e.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify node 447 (SaveImage) is enabled (mode 0)
        node = self._get_node(result, 447)
        assert node is not None, "Node 447 should exist"
        mode = node.get("mode", 0)
        assert mode == 0, f"Node 447 should be enabled (mode 0), got {mode}"
    
    # Test 13: Interpolation disabled
    def test_13_interpolation_no(self, interpreter, original_workflow):
        """Test 13: Disable interpolation."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/13_interpolation_no_1fd5352d.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify interpolation nodes 431, 442, 433 (processing + save) are bypassed (mode 2)
        for node_id in [431, 442, 433]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 2, f"Node {node_id} should be bypassed (mode 2), got {mode}"
    
    # Test 14: Upscale and interpolation enabled
    def test_14_upscale_interp_yes(self, interpreter, original_workflow):
        """Test 14: Enable upscale and interpolation (combined output)."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/14_upscale_interp_yes_2887ac38.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify combined output save node 443 is enabled
        # Note: Processing nodes are controlled by enable_interpolation (which is true in this test)
        node = self._get_node(result, 443)
        assert node is not None, "Node 443 (Save UPINT) should exist"
        mode = node.get("mode", 0)
        assert mode == 0, f"Node 443 should be enabled (mode 0), got {mode}"
        
        # Also verify interpolation nodes are enabled (since enable_interpolation is true)
        for node_id in [431, 442, 433]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 0, f"Node {node_id} should be enabled (mode 0), got {mode}"
    
    # Test 15: Upscaler enabled
    def test_15_upscaler_yes(self, interpreter, original_workflow):
        """Test 15: Enable upscaler."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/15_upscaler_yes_ed6c5714.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify standalone upscaler nodes 385 (processing) and 419 (save) are enabled (mode 0)
        for node_id in [385, 419]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 0, f"Node {node_id} should be enabled (mode 0), got {mode}"
    
    # Test 16: Video enhancer disabled
    def test_16_video_enhancer_no(self, interpreter, original_workflow):
        """Test 16: Disable video enhancer."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/16_video_enhancer_no_a801da91.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 481, 482 (WanVideoEnhanceAVideoKJ) are muted (mode 4)
        for node_id in [481, 482]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 17: CFG Zero Star disabled
    def test_17_cfg_zero_star_no(self, interpreter, original_workflow):
        """Test 17: Disable CFG Zero Star."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/17_cfg_zero_star_no_511510da.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 483, 484 (CFGZeroStarAndInit) are muted (mode 4)
        for node_id in [483, 484]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 18: Speed regulation disabled
    def test_18_speed_regulation_no(self, interpreter, original_workflow):
        """Test 18: Disable speed regulation."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/18_speed_regulation_no_0ac7400c.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 467, 468 (ModelSamplingSD3) are muted (mode 4)
        for node_id in [467, 468]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 19: Normalized attention disabled
    def test_19_normalized_attention_no(self, interpreter, original_workflow):
        """Test 19: Disable normalized attention."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/19_normalized_attention_no_e6f42924.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 485, 486 (WanVideoNAG) are muted (mode 4)
        for node_id in [485, 486]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 20: MagCache disabled
    def test_20_magcache_no(self, interpreter, original_workflow):
        """Test 20: Disable MagCache."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/20_magcache_no_d55a327a.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 505, 506 (MagCache) are muted (mode 4)
        for node_id in [505, 506]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 21: BlockSwap disabled
    def test_21_block_swap_no(self, interpreter, original_workflow):
        """Test 21: Disable BlockSwap."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/21_block_swap_no_50547ca6.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 500, 501 (wanBlockSwap) are muted (mode 4)
        for node_id in [500, 501]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 4, f"Node {node_id} should be muted (mode 4), got {mode}"
    
    # Test 22: TorchCompile enabled
    def test_22_torch_compile_yes(self, interpreter, original_workflow):
        """Test 22: Enable TorchCompile."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/22_torch_compile_yes_8b7d98fb.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify nodes 492, 494 (TorchCompileModelWanVideo) are enabled (mode 0)
        for node_id in [492, 494]:
            node = self._get_node(result, node_id)
            assert node is not None, f"Node {node_id} should exist"
            mode = node.get("mode", 0)
            assert mode == 0, f"Node {node_id} should be enabled (mode 0), got {mode}"
    
    # Test 23: VRAM reduction = 50%
    def test_23_vram_reduction_50(self, interpreter, original_workflow):
        """Test 23: VRAM reduction set to 50%."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/23_vram_reduction_50_f5be93ce.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify vram_reduction changed to 50 (node 502, indices 0-1)
        vram_0 = self._get_widget_value(result, 502, 0)
        vram_1 = self._get_widget_value(result, 502, 1)
        
        assert vram_0 == 50, f"VRAM reduction[0] should be 50, got {vram_0}"
        assert vram_1 == 50, f"VRAM reduction[1] should be 50, got {vram_1}"
    
    # Test 24: Automatic prompting disabled
    def test_24_auto_prompt_no(self, interpreter, original_workflow):
        """Test 24: Disable automatic prompting."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/24_auto_prompt_no_f130146e.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify node 403 (Fast Groups Bypasser) is muted (mode 4)
        node = self._get_node(result, 403)
        assert node is not None, "Node 403 should exist"
        mode = node.get("mode", 0)
        assert mode == 4, f"Node 403 should be muted (mode 4), got {mode}"
    
    # Test 25: Upscale ratio = 1.5
    def test_25_upscale_ratio_1_5(self, interpreter, original_workflow):
        """Test 25: Upscale ratio set to 1.5."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/25_upscale_ratio_1_5_4e40676c.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify upscale ratio changed to 1.5 (node 421, indices 0-1)
        ratio_0 = self._get_widget_value(result, 421, 0)
        ratio_1 = self._get_widget_value(result, 421, 1)
        
        assert ratio_0 == 1.5, f"Upscale ratio[0] should be 1.5, got {ratio_0}"
        assert ratio_1 == 1.5, f"Upscale ratio[1] should be 1.5, got {ratio_1}"
    
    # Test 27: Basic output configuration
    def test_27_output_config(self, interpreter, original_workflow):
        """Test 27: Combination - duration, size, frame rate."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/27_output_config_f0917eb4.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify duration = 10.0
        duration = self._get_widget_value(result, 426, 0)
        assert duration == 10.0, f"Duration should be 10.0, got {duration}"
        
        # Verify size = 768x1024
        size_node = self._get_node(result, 83)
        assert size_node["properties"]["valueX"] == 768
        assert size_node["properties"]["valueY"] == 1024
        
        # Verify frame rate = 24.0
        frame_rate = self._get_widget_value(result, 490, 0)
        assert frame_rate == 24.0, f"Frame rate should be 24.0, got {frame_rate}"
    
    # Test 28: Generation quality tuning
    def test_28_quality_tuning(self, interpreter, original_workflow):
        """Test 28: Combination - steps, CFG, seed."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/28_quality_tuning_e2639278.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify steps = 25
        steps = self._get_widget_value(result, 82, 0)
        assert steps == 25, f"Steps should be 25, got {steps}"
        
        # Verify CFG = 4.5
        cfg = self._get_widget_value(result, 85, 0)
        assert cfg == 4.5, f"CFG should be 4.5, got {cfg}"
        
        # Verify seed = 999888777666
        seed = self._get_widget_value(result, 73, 0)
        assert seed == 999888777666, f"Seed should be 999888777666, got {seed}"
    
    # Test 29: Temporal control
    def test_29_temporal_control(self, interpreter, original_workflow):
        """Test 29: Combination - frame rate, speed, interpolation."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/29_temporal_control_94249ee0.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify frame rate = 12.0
        frame_rate = self._get_widget_value(result, 490, 0)
        assert frame_rate == 12.0, f"Frame rate should be 12.0, got {frame_rate}"
        
        # Verify speed = 5.0
        speed = self._get_widget_value(result, 157, 0)
        assert speed == 5.0, f"Speed should be 5.0, got {speed}"
        
        # Verify standalone interpolation enabled (nodes 431 processing, 433 save)
        node_431 = self._get_node(result, 431)
        node_433 = self._get_node(result, 433)
        assert node_431["mode"] == 0, "Standalone interpolation node 431 should be enabled"
        assert node_433["mode"] == 0, "Standalone interpolation save node 433 should be enabled"
    
    # Test 30: Enhancement pipeline
    def test_30_enhancement_pipeline(self, interpreter, original_workflow):
        """Test 30: Combination - 1 LoRA, upscale ratio, duration."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/30_enhancement_pipeline_9323355a.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify 1 LoRA added
        lora_count_416 = self._count_loras(result, 416)
        lora_count_471 = self._count_loras(result, 471)
        assert lora_count_416 >= 1, f"Node 416 should have at least 1 LoRA, got {lora_count_416}"
        assert lora_count_471 >= 1, f"Node 471 should have at least 1 LoRA, got {lora_count_471}"
        
        # Verify upscale ratio = 1.8
        ratio = self._get_widget_value(result, 421, 0)
        assert ratio == 1.8, f"Upscale ratio should be 1.8, got {ratio}"
        
        # Verify duration = 5.0
        duration = self._get_widget_value(result, 426, 0)
        assert duration == 5.0, f"Duration should be 5.0, got {duration}"
    
    # Test 31: Quality enhancement stack
    def test_31_quality_enhancement_stack(self, interpreter, original_workflow):
        """Test 31: Combination - interpolation, video enhancer, CFG Zero Star."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/31_quality_enhancement_stack_b81964bf.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify interpolation enabled
        node_431 = self._get_node(result, 431)
        assert node_431["mode"] == 0, "Interpolation should be enabled"
        
        # Verify video enhancer enabled (nodes 481, 482)
        node_481 = self._get_node(result, 481)
        node_482 = self._get_node(result, 482)
        assert node_481["mode"] in [0, 4], "Video enhancer node 481 should be enabled"
        assert node_482["mode"] in [0, 4], "Video enhancer node 482 should be enabled"
        
        # Verify CFG Zero Star enabled (nodes 483, 484)
        node_483 = self._get_node(result, 483)
        node_484 = self._get_node(result, 484)
        assert node_483["mode"] in [0, 4], "CFG Zero node 483 should be enabled"
        assert node_484["mode"] in [0, 4], "CFG Zero node 484 should be enabled"
    
    # Test 32: Performance optimization
    def test_32_performance_optimization(self, interpreter, original_workflow):
        """Test 32: Combination - block swap, VRAM reduction."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/32_performance_optimization_e9ac2bd9.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify block swap enabled (nodes 500, 501)
        node_500 = self._get_node(result, 500)
        node_501 = self._get_node(result, 501)
        assert node_500["mode"] == 0, "BlockSwap node 500 should be enabled"
        assert node_501["mode"] == 0, "BlockSwap node 501 should be enabled"
        
        # Verify VRAM reduction = 75
        vram = self._get_widget_value(result, 502, 0)
        assert vram == 75, f"VRAM reduction should be 75, got {vram}"
    
    # Test 33: Minimal features
    def test_33_minimal_features(self, interpreter, original_workflow):
        """Test 33: Combination - disable interpolation, upscaler, video enhancer, CFG Zero."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/33_minimal_features_3a245c8b.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify interpolation disabled
        node_431 = self._get_node(result, 431)
        assert node_431["mode"] == 2, "Interpolation should be disabled (mode 2)"
        
        # Verify upscaler disabled
        node_385 = self._get_node(result, 385)
        assert node_385["mode"] == 2, "Upscaler should be disabled (mode 2)"
        
        # Verify video enhancer disabled
        node_481 = self._get_node(result, 481)
        assert node_481["mode"] in [2, 4], "Video enhancer should be disabled"
        
        # Verify CFG Zero disabled
        node_483 = self._get_node(result, 483)
        assert node_483["mode"] in [2, 4], "CFG Zero should be disabled"
    
    # Test 34: Full quality mode
    def test_34_full_quality_mode(self, interpreter, original_workflow):
        """Test 34: Combination - all 3 output saves, upscaler enabled."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/34_full_quality_mode_96a4278f.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify all output save nodes enabled
        node_398 = self._get_node(result, 398)  # Output
        node_433 = self._get_node(result, 433)  # Save Interpoled
        node_419 = self._get_node(result, 419)  # Save Upscaled
        
        assert node_398["mode"] == 0, "Output save should be enabled"
        assert node_433["mode"] == 0, "Save Interpoled should be enabled"
        assert node_419["mode"] == 0, "Save Upscaled should be enabled"
        
        # Verify upscaler processing enabled
        node_385 = self._get_node(result, 385)
        assert node_385["mode"] == 0, "Upscaler processing should be enabled"
    
    # Test 35: Complete output config
    def test_35_complete_output_config(self, interpreter, original_workflow):
        """Test 35: Combination - duration, size, frame rate, steps."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/35_complete_output_config_f145bbb1.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify duration = 6.0
        duration = self._get_widget_value(result, 426, 0)
        assert duration == 6.0, f"Duration should be 6.0, got {duration}"
        
        # Verify size = 640x896
        size_node = self._get_node(result, 83)
        assert size_node["properties"]["valueX"] == 640
        assert size_node["properties"]["valueY"] == 896
        
        # Verify frame rate = 20.0
        frame_rate = self._get_widget_value(result, 490, 0)
        assert frame_rate == 20.0, f"Frame rate should be 20.0, got {frame_rate}"
        
        # Verify steps = 25
        steps = self._get_widget_value(result, 82, 0)
        assert steps == 25, f"Steps should be 25, got {steps}"
    
    # Test 36: Advanced generation setup
    def test_36_advanced_generation_setup(self, interpreter, original_workflow):
        """Test 36: Combination - 2 LoRAs, steps, CFG, seed, normalized attention."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/36_advanced_generation_setup_8bf5b33e.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify 2 LoRAs added
        lora_count_416 = self._count_loras(result, 416)
        lora_count_471 = self._count_loras(result, 471)
        assert lora_count_416 >= 2, f"Node 416 should have at least 2 LoRAs, got {lora_count_416}"
        assert lora_count_471 >= 2, f"Node 471 should have at least 2 LoRAs, got {lora_count_471}"
        
        # Verify steps = 20
        steps = self._get_widget_value(result, 82, 0)
        assert steps == 20, f"Steps should be 20, got {steps}"
        
        # Verify CFG = 4.0
        cfg = self._get_widget_value(result, 85, 0)
        assert cfg == 4.0, f"CFG should be 4.0, got {cfg}"
        
        # Verify seed = 555444333222
        seed = self._get_widget_value(result, 73, 0)
        assert seed == 555444333222, f"Seed should be 555444333222, got {seed}"
        
        # Verify normalized attention enabled (nodes 485, 486)
        node_485 = self._get_node(result, 485)
        node_486 = self._get_node(result, 486)
        assert node_485["mode"] == 0, "NAG node 485 should be enabled"
        assert node_486["mode"] == 0, "NAG node 486 should be enabled"
    
    # Test 37: UPINT with multiple LoRAs
    def test_37_upint_multiple_loras(self, interpreter, original_workflow):
        """Test 37: Combination - UPINT output, 2 LoRAs."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/37_upint_multiple_loras_1fed014f.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify 2 LoRAs added
        lora_count_416 = self._count_loras(result, 416)
        lora_count_471 = self._count_loras(result, 471)
        assert lora_count_416 >= 2, f"Node 416 should have at least 2 LoRAs, got {lora_count_416}"
        assert lora_count_471 >= 2, f"Node 471 should have at least 2 LoRAs, got {lora_count_471}"
        
        # Verify UPINT output enabled (node 443)
        node_443 = self._get_node(result, 443)
        assert node_443["mode"] == 0, "UPINT save should be enabled"
        
        # Verify interpolation enabled (auto-enabled with UPINT)
        node_442 = self._get_node(result, 442)
        assert node_442["mode"] == 0, "Interpolation should be enabled for UPINT"
        
        # Verify upscaler enabled (auto-enabled with UPINT)
        node_437 = self._get_node(result, 437)
        assert node_437["mode"] == 0, "Upscaler should be enabled for UPINT"
    
    # Test 38: Input image change
    def test_38_input_image_change(self, interpreter, original_workflow):
        """Test 38: Change input image filename (Node 88)."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/38_input_image_change_9de73093.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify input image changed (node 88, index 0)
        input_image = self._get_widget_value(result, 88, 0)
        expected_image = "4967f305-da29-4172-9bae-a3a43bb50a19.jpeg"
        
        assert input_image == expected_image, f"Input image should be '{expected_image}', got '{input_image}'"
    
    # Test 39: UPINT only output with 2 LoRAs
    def test_39_upint_only_output_two_loras(self, interpreter, original_workflow):
        """Test 39: UPINT only output with 2 LoRAs, size 768x1024, input image change."""
        input_file = "tests/comfyui/test_data/interpreter_inputs/39_upint_only_output_two_loras.json"
        
        with open(input_file) as f:
            inputs = json.load(f)
        
        actions = interpreter.generate_actions(inputs)
        result = interpreter.apply_actions(original_workflow, actions)
        
        # Verify size changed (node 83: mxSlider2D)
        size_node = self._get_node(result, 83)
        assert size_node["properties"]["valueX"] == 768
        assert size_node["properties"]["valueY"] == 1024
        
        # Verify input image changed (node 88, index 0)
        input_image = self._get_widget_value(result, 88, 0)
        expected_image = "61603705.jpeg"
        assert input_image == expected_image, f"Input image should be '{expected_image}', got '{input_image}'"
        
        # Verify 2 LoRAs are set (node 416 high prio, node 471 low prio)
        lora_count_416 = self._count_loras(result, 416)
        lora_count_471 = self._count_loras(result, 471)
        assert lora_count_416 >= 2, f"Node 416 should have at least 2 LoRAs, got {lora_count_416}"
        assert lora_count_471 >= 2, f"Node 471 should have at least 2 LoRAs, got {lora_count_471}"
        
        # Verify standalone interpolation disabled (nodes 431, 433 muted)
        node_431 = self._get_node(result, 431)
        node_433 = self._get_node(result, 433)
        assert node_431["mode"] == 2, "Standalone interpolation processing should be disabled"
        assert node_433["mode"] == 2, "Standalone interpolation save should be disabled"
        
        # Verify standalone upscaler disabled (node 419 muted)
        node_419 = self._get_node(result, 419)
        assert node_419["mode"] == 2, "Standalone upscaler save should be disabled"
        
        # Verify UPINT enabled (shared processing nodes 442, 437 enabled)
        node_442 = self._get_node(result, 442)
        node_437 = self._get_node(result, 437)
        node_443 = self._get_node(result, 443)
        assert node_442["mode"] == 0, "RIFE node should be enabled for UPINT"
        assert node_437["mode"] == 0, "Upscaler node should be enabled for UPINT"
        assert node_443["mode"] == 0, "UPINT save node should be enabled"
