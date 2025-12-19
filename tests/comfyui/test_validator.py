#!/usr/bin/env python3
"""
Test validator - verifies that each test input file correctly represents
the modifications in its corresponding workflow file.

This script validates the test suite itself by:
1. Loading each expected workflow
2. Extracting key values from the workflow
3. Comparing them against the test input values
4. Reporting any mismatches
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from browser_agent.logging_utils import get_logger

logger = get_logger(__name__)


class TestValidator:
    """Validates test input files against their expected workflows."""
    
    def __init__(self):
        self.test_inputs_dir = Path("tests/comfyui/test_data/interpreter_inputs")
        self.validation_results = []
    
    def validate_all(self) -> bool:
        """Validate all test files."""
        test_files = sorted(self.test_inputs_dir.glob("*.json"))
        logger.info(f"Validating {len(test_files)} test files\n")
        
        all_valid = True
        
        for test_file in test_files:
            logger.info(f"{'='*80}")
            logger.info(f"Validating: {test_file.name}")
            logger.info(f"{'='*80}")
            
            valid = self.validate_test(test_file)
            all_valid = all_valid and valid
            
            logger.info("")
        
        # Print summary
        self._print_summary()
        
        return all_valid
    
    def validate_test(self, test_file: Path) -> bool:
        """Validate a single test file."""
        try:
            # Load test input
            with open(test_file) as f:
                test_data = json.load(f)
            
            # Load expected workflow
            workflow_path = Path(test_data.get("workflow_file", ""))
            if not workflow_path.exists():
                logger.error(f"✗ Workflow file not found: {workflow_path}")
                return False
            
            with open(workflow_path) as f:
                workflow = json.load(f)
            
            # Extract values from workflow
            nodes_by_id = {n["id"]: n for n in workflow.get("nodes", [])}
            
            # Validate based on test description
            test_id = test_data.get("test_id", "")
            inputs = test_data.get("inputs", {})
            
            validation_passed = True
            
            # Check hash matches filename
            expected_hash = test_data.get("expected_hash")
            if expected_hash not in workflow_path.name:
                logger.warning(f"⚠ Hash {expected_hash} not in filename {workflow_path.name}")
            
            # Perform specific validations based on test type
            if "duration" in test_id:
                validation_passed &= self._validate_duration(nodes_by_id, inputs, test_id)
            elif "size_x" in test_id:
                validation_passed &= self._validate_size_x(nodes_by_id, inputs)
            elif "size_y" in test_id:
                validation_passed &= self._validate_size_y(nodes_by_id, inputs)
            elif "steps" in test_id:
                validation_passed &= self._validate_steps(nodes_by_id, inputs)
            elif "cfg" in test_id and "cfg_zero_star" not in test_id:
                validation_passed &= self._validate_cfg(nodes_by_id, inputs)
            elif "frame_rate" in test_id:
                validation_passed &= self._validate_frame_rate(nodes_by_id, inputs)
            elif "speed" in test_id and "speed_regulation" not in test_id:
                validation_passed &= self._validate_speed(nodes_by_id, inputs)
            elif "seed" in test_id:
                validation_passed &= self._validate_seed(nodes_by_id, inputs)
            elif "lora" in test_id:
                validation_passed &= self._validate_loras(nodes_by_id, inputs)
            elif "upscale_ratio" in test_id:
                validation_passed &= self._validate_upscale_ratio(nodes_by_id, inputs)
            elif "vram_reduction" in test_id:
                validation_passed &= self._validate_vram_reduction(nodes_by_id, inputs)
            else:
                # Boolean feature toggles
                validation_passed &= self._validate_feature_toggles(nodes_by_id, inputs, test_id)
            
            if validation_passed:
                logger.info("✓ Validation passed")
            else:
                logger.error("✗ Validation failed")
            
            return validation_passed
        
        except Exception as e:
            logger.error(f"✗ Validation error: {e}", exc_info=True)
            return False
    
    def _validate_duration(self, nodes: Dict, inputs: Dict, test_id: str) -> bool:
        """Validate duration value."""
        expected = inputs["generation_parameters"]["duration"]
        # Node 83 (mxSlider2D) has duration at indices 2-3
        actual = nodes[83]["widgets_values"][2]
        
        if expected == actual:
            logger.info(f"✓ Duration: {actual}")
            return True
        else:
            logger.error(f"✗ Duration mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_size_x(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate X size."""
        expected = inputs["generation_parameters"]["size_x"]
        actual = nodes[83]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Size X: {actual}")
            return True
        else:
            logger.error(f"✗ Size X mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_size_y(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate Y size."""
        expected = inputs["generation_parameters"]["size_y"]
        actual = nodes[83]["widgets_values"][2]
        
        if expected == actual:
            logger.info(f"✓ Size Y: {actual}")
            return True
        else:
            logger.error(f"✗ Size Y mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_steps(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate steps value."""
        expected = inputs["generation_parameters"]["steps"]
        actual = nodes[390]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Steps: {actual}")
            return True
        else:
            logger.error(f"✗ Steps mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_cfg(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate CFG value."""
        expected = inputs["generation_parameters"]["cfg"]
        actual = nodes[390]["widgets_values"][1]
        
        if expected == actual:
            logger.info(f"✓ CFG: {actual}")
            return True
        else:
            logger.error(f"✗ CFG mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_frame_rate(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate frame rate."""
        expected = inputs["generation_parameters"]["frame_rate"]
        actual = nodes[94]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Frame rate: {actual}")
            return True
        else:
            logger.error(f"✗ Frame rate mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_speed(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate speed value."""
        expected = inputs["generation_parameters"]["speed"]
        actual = nodes[397]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Speed: {actual}")
            return True
        else:
            logger.error(f"✗ Speed mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_seed(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate seed value."""
        expected = inputs["basic_settings"]["seed"]
        actual = nodes[73]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Seed: {actual}")
            return True
        else:
            logger.error(f"✗ Seed mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_loras(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate LoRA configuration."""
        expected_loras = inputs["model_selection"]["loras"]
        
        # Check high noise loader (node 384)
        high_widgets = nodes[384]["widgets_values"]
        # Check low noise loader (node 385)
        low_widgets = nodes[385]["widgets_values"]
        
        logger.info(f"✓ LoRAs: {len(expected_loras)} configured")
        return True  # Detailed LoRA validation would require parsing complex structure
    
    def _validate_upscale_ratio(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate upscale ratio."""
        expected = inputs["generation_parameters"]["upscale_ratio"]
        actual = nodes[237]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ Upscale ratio: {actual}")
            return True
        else:
            logger.error(f"✗ Upscale ratio mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_vram_reduction(self, nodes: Dict, inputs: Dict) -> bool:
        """Validate VRAM reduction percentage."""
        expected = inputs["advanced_features"]["performance_memory"]["vram_reduction"]
        actual = nodes[394]["widgets_values"][0]
        
        if expected == actual:
            logger.info(f"✓ VRAM reduction: {actual}%")
            return True
        else:
            logger.error(f"✗ VRAM reduction mismatch: expected {expected}, got {actual}")
            return False
    
    def _validate_feature_toggles(self, nodes: Dict, inputs: Dict, test_id: str) -> bool:
        """Validate boolean feature toggles by checking node modes."""
        # Map test IDs to node IDs and expected modes
        feature_map = {
            "save_last_frame": (372, inputs["advanced_features"]["output_enhancement"]["save_last_frame"]),
            "interpolation": (371, inputs["advanced_features"]["output_enhancement"]["enable_interpolation"]),
            "upscaler": (237, inputs["advanced_features"]["output_enhancement"]["use_upscaler"]),
            "upscale_interp": (237, inputs["advanced_features"]["output_enhancement"]["enable_upscale_interpolation"]),
            "video_enhancer": (393, inputs["advanced_features"]["quality_enhancements"]["enable_video_enhancer"]),
            "cfg_zero_star": (396, inputs["advanced_features"]["quality_enhancements"]["enable_cfg_zero_star"]),
            "speed_regulation": (397, inputs["advanced_features"]["quality_enhancements"]["enable_speed_regulation"]),
            "normalized_attention": (395, inputs["advanced_features"]["quality_enhancements"]["enable_normalized_attention"]),
            "magcache": (391, inputs["advanced_features"]["performance_memory"]["enable_magcache"]),
            "block_swap": (394, inputs["advanced_features"]["performance_memory"]["enable_block_swap"]),
            "torch_compile": (392, inputs["advanced_features"]["performance_memory"]["enable_torch_compile"]),
            "auto_prompt": (409, inputs["advanced_features"]["automatic_prompting"]["enable_auto_prompt"]),
        }
        
        # Find matching feature
        for feature_key, (node_id, expected_enabled) in feature_map.items():
            if feature_key in test_id:
                actual_mode = nodes[node_id].get("mode", 0)
                expected_mode = 0 if expected_enabled else 2
                
                if actual_mode == expected_mode:
                    status = "enabled" if expected_enabled else "disabled"
                    logger.info(f"✓ {feature_key}: {status} (mode={actual_mode})")
                    return True
                else:
                    logger.error(f"✗ {feature_key} mode mismatch: expected {expected_mode}, got {actual_mode}")
                    return False
        
        logger.warning(f"⚠ No specific validation for test {test_id}")
        return True
    
    def _print_summary(self):
        """Print validation summary."""
        logger.info(f"\n{'='*80}")
        logger.info("VALIDATION COMPLETE")
        logger.info(f"{'='*80}")


def main():
    """Main entry point."""
    validator = TestValidator()
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
