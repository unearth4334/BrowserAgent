"""
Integration tests for workflow interpreter.

Tests all 26 workflow variations by running the interpreter and verifying
that each modification was correctly applied to the output workflow.
"""

import json
import pytest
from pathlib import Path

from browser_agent.comfyui.workflow_interpreter import WorkflowInterpreter


class TestInterpreterIntegration:
    """Integration tests for workflow interpreter with all 26 test cases."""
    
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
        assert "high" in high_lora["lora"].lower(), f"High LoRA path should contain 'high': {high_lora['lora']}"
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
        
        # Verify upscale nodes 385, 437, 419 (processing + save) are enabled (mode 0)
        for node_id in [385, 437, 419]:
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
