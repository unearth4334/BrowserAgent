#!/usr/bin/env python3
"""
Example implementation of the Workflow Modification System.

This demonstrates how to programmatically modify ComfyUI workflows
using the elementary change actions defined in WORKFLOW_CHANGE_ACTIONS.md
"""

import json
import yaml
from pathlib import Path
from typing import Dict, List, Any


class WorkflowModifier:
    """Applies change actions to ComfyUI workflow JSON."""
    
    def __init__(self, workflow_path: str):
        """Load base workflow."""
        with open(workflow_path) as f:
            self.workflow = json.load(f)
        self.nodes = {node["id"]: node for node in self.workflow.get("nodes", [])}
    
    def find_node(self, node_id: int) -> Dict:
        """Find node by ID."""
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in workflow")
        return self.nodes[node_id]
    
    def apply_actions(self, actions: List[Dict]) -> Dict:
        """Apply a list of change actions."""
        for action in actions:
            self.apply_single_action(action)
        return self.workflow
    
    def apply_single_action(self, action: Dict):
        """Apply one change action based on type."""
        action_type = action["type"]
        
        if action_type == "modify_widget":
            self._apply_modify_widget(action)
        elif action_type == "toggle_node_mode":
            self._apply_toggle_mode(action)
        elif action_type == "add_lora_pair":
            self._apply_add_lora(action)
        elif action_type == "modify_vector_widget":
            self._apply_modify_vector(action)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def _apply_modify_widget(self, action: Dict):
        """Modify a single widget value."""
        node = self.find_node(action["node_id"])
        widget_idx = action["widget_index"]
        new_value = action["new_value"]
        
        # Handle mxSlider pattern: [value, value, step]
        if node["type"] in ["mxSlider", "ComfyUI-mxToolkit/mxSlider"]:
            # Set both indices 0 and 1 to the same value
            node["widgets_values"][0] = new_value
            node["widgets_values"][1] = new_value
        
        # Handle RandomNoise pattern: [seed, control]
        elif node["type"] == "RandomNoise":
            node["widgets_values"][widget_idx] = new_value
        
        else:
            # Generic single value modification
            node["widgets_values"][widget_idx] = new_value
    
    def _apply_toggle_mode(self, action: Dict):
        """Toggle node execution mode."""
        new_mode = action["new_mode"]
        
        for node_id in action["node_ids"]:
            node = self.find_node(node_id)
            node["mode"] = new_mode
    
    def _apply_add_lora(self, action: Dict):
        """Add a LoRA pair to high/low noise loaders."""
        high_node = self.find_node(action["high_node_id"])
        low_node = self.find_node(action["low_node_id"])
        
        lora_config = action["lora_config"]
        insert_pos = action.get("insert_position", 2)
        
        # Create high noise LoRA object
        high_lora = {
            "lora": lora_config["high_path"],
            "on": lora_config.get("enabled", True),
            "strength": lora_config.get("strength", 1.0),
            "strengthTwo": None
        }
        
        # Create low noise LoRA object
        low_lora = {
            "lora": lora_config["low_path"],
            "on": lora_config.get("enabled", True),
            "strength": lora_config.get("strength", 1.0),
            "strengthTwo": None
        }
        
        # Insert into widgets_values arrays
        high_node["widgets_values"].insert(insert_pos, high_lora)
        low_node["widgets_values"].insert(insert_pos, low_lora)
    
    def _apply_modify_vector(self, action: Dict):
        """Modify coordinated vector values (e.g., X/Y dimensions)."""
        node = self.find_node(action["node_id"])
        modifications = action["modifications"]
        
        # Handle mxSlider2D pattern: [x, x, y, y, isfloatX, isfloatY]
        if "x" in modifications:
            node["widgets_values"][0] = modifications["x"]
            node["widgets_values"][1] = modifications["x"]
        
        if "y" in modifications:
            node["widgets_values"][2] = modifications["y"]
            node["widgets_values"][3] = modifications["y"]


class ActionGenerator:
    """Generate change actions from UI inputs and node mappings."""
    
    def __init__(self, node_mapping: Dict):
        """Initialize with node mapping configuration."""
        self.node_mapping = node_mapping
    
    def generate(self, ui_inputs: Dict) -> List[Dict]:
        """Convert UI inputs to change actions."""
        actions = []
        
        for input_id, value in ui_inputs.items():
            mapping = self.node_mapping.get(input_id)
            if not mapping:
                continue
            
            action_type = mapping["action_type"]
            
            if action_type == "modify_widget":
                actions.append(self._make_modify_widget(input_id, value, mapping))
            
            elif action_type == "modify_vector_widget":
                actions.append(self._make_modify_vector(input_id, value, mapping))
            
            elif action_type == "toggle_node_mode":
                actions.append(self._make_toggle_mode(input_id, value, mapping))
            
            elif action_type == "add_lora_pair":
                # Handle list of LoRAs
                if isinstance(value, list):
                    for idx, lora in enumerate(value):
                        actions.append(self._make_add_lora(lora, mapping, idx + 2))
        
        return actions
    
    def _make_modify_widget(self, input_id: str, value: Any, mapping: Dict) -> Dict:
        """Create modify_widget action."""
        return {
            "type": "modify_widget",
            "node_id": mapping["node_id"],
            "widget_index": mapping["widget_indices"][0],
            "new_value": value,
            "description": f"Set {input_id} to {value}"
        }
    
    def _make_modify_vector(self, input_id: str, value: Any, mapping: Dict) -> Dict:
        """Create modify_vector_widget action."""
        return {
            "type": "modify_vector_widget",
            "node_id": mapping["node_id"],
            "modifications": {mapping["vector_key"]: value},
            "description": f"Set {input_id} to {value}"
        }
    
    def _make_toggle_mode(self, input_id: str, value: bool, mapping: Dict) -> Dict:
        """Create toggle_node_mode action."""
        mode = mapping["enabled_mode"] if value else mapping["disabled_mode"]
        return {
            "type": "toggle_node_mode",
            "node_ids": mapping["node_ids"],
            "new_mode": mode,
            "description": f"{'Enable' if value else 'Disable'} {input_id}"
        }
    
    def _make_add_lora(self, lora: Dict, mapping: Dict, position: int) -> Dict:
        """Create add_lora_pair action."""
        return {
            "type": "add_lora_pair",
            "high_node_id": mapping["high_node_id"],
            "low_node_id": mapping["low_node_id"],
            "lora_config": lora,
            "insert_position": position,
            "description": f"Add LoRA pair: {lora.get('high_path', 'unknown')}"
        }


def main():
    """Example usage of the workflow modification system."""
    
    # 1. Load configuration
    config_path = "IMG_to_VIDEO.webui.yml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print(f"Loaded configuration: {config['name']}")
    print(f"Base workflow: {config['workflow_file']}")
    print(f"Base hash: {config['base_hash']}")
    print()
    
    # 2. Simulate user inputs from UI
    ui_inputs = {
        "duration": 8.0,
        "size_x": 1024,
        "size_y": 1024,
        "steps": 30,
        "cfg": 5.0,
        "enable_interpolation": False,
        "use_upscaler": True,
        "upscale_ratio": 1.5,
        "loras": [
            {
                "high_path": "NSFW-22-H-e8.safetensors",
                "low_path": "NSFW-22-L-e8.safetensors",
                "strength": 1.0,
                "enabled": True
            }
        ]
    }
    
    print("User Inputs:")
    for key, value in ui_inputs.items():
        if key != "loras":
            print(f"  {key}: {value}")
    print(f"  loras: {len(ui_inputs.get('loras', []))} LoRA pair(s)")
    print()
    
    # 3. Generate change actions
    generator = ActionGenerator(config["node_mapping"])
    actions = generator.generate(ui_inputs)
    
    print(f"Generated {len(actions)} change actions:")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action['type']}: {action.get('description', 'No description')}")
    print()
    
    # 4. Apply actions to workflow
    modifier = WorkflowModifier(config["workflow_file"])
    modified_workflow = modifier.apply_actions(actions)
    
    # 5. Save modified workflow
    output_path = "output_workflow.json"
    with open(output_path, "w") as f:
        json.dump(modified_workflow, f, indent=2)
    
    print(f"✓ Modified workflow saved to: {output_path}")
    print()
    
    # 6. Calculate hash for version tracking
    import hashlib
    with open(output_path, "rb") as f:
        workflow_hash = hashlib.sha256(f.read()).hexdigest()[:8]
    
    print(f"Workflow hash: {workflow_hash}")
    print()
    
    # 7. Print summary
    print("Modification Summary:")
    print(f"  Base workflow: {config['base_hash']}")
    print(f"  New workflow: {workflow_hash}")
    print(f"  Changes applied: {len(actions)}")
    print()
    print("Changes:")
    for action in actions:
        print(f"  - {action.get('description', action['type'])}")


if __name__ == "__main__":
    main()
