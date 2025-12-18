"""Unit tests for ComfyUI workflow actions."""

import pytest
from pathlib import Path
import json
import sys

# Add fixtures to path
sys.path.insert(0, str(Path(__file__).parent / "fixtures"))

from browser_agent.comfyui.actions.workflow import (
    LoadWorkflowAction,
    QueueWorkflowAction,
    GetPromptIDAction,
)
from browser_agent.comfyui.exceptions import WorkflowLoadError, QueueError
from mock_browser import MockBrowserClient


# Fixtures

@pytest.fixture
def mock_client():
    """Provide a fresh mock browser client for each test."""
    client = MockBrowserClient()
    yield client
    client.reset()


@pytest.fixture
def sample_workflow_path():
    """Provide path to sample workflow JSON."""
    return Path(__file__).parent / "fixtures" / "sample_workflow.json"


@pytest.fixture
def sample_workflow_dict(sample_workflow_path):
    """Provide sample workflow as dict."""
    with open(sample_workflow_path) as f:
        return json.load(f)


# LoadWorkflowAction Tests

class TestLoadWorkflowAction:
    """Tests for LoadWorkflowAction."""
    
    def test_load_from_file_path(self, mock_client, sample_workflow_path):
        """Test loading workflow from file path."""
        action = LoadWorkflowAction(workflow_source=sample_workflow_path)
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["node_count"] == 5
        assert result["method"] == "ui_native"
        assert mock_client.workflow_loaded is True
    
    def test_load_from_dict(self, mock_client, sample_workflow_dict):
        """Test loading workflow from dict."""
        action = LoadWorkflowAction(workflow_source=sample_workflow_dict)
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["node_count"] == 5
        assert mock_client.workflow_loaded is True
    
    def test_load_nonexistent_file(self, mock_client):
        """Test loading from nonexistent file raises error."""
        action = LoadWorkflowAction(workflow_source=Path("/nonexistent/file.json"))
        
        with pytest.raises(WorkflowLoadError, match="not found"):
            action.execute(mock_client)
    
    def test_load_invalid_json(self, mock_client, tmp_path):
        """Test loading invalid JSON raises error."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {")
        
        action = LoadWorkflowAction(workflow_source=bad_file)
        
        with pytest.raises(WorkflowLoadError, match="Invalid JSON"):
            action.execute(mock_client)
    
    def test_chunking_large_workflow(self, mock_client, sample_workflow_dict):
        """Test that large workflows are properly chunked."""
        # Create a large workflow by duplicating nodes
        large_workflow = sample_workflow_dict.copy()
        large_workflow["nodes"] = sample_workflow_dict["nodes"] * 100  # 500 nodes
        
        action = LoadWorkflowAction(
            workflow_source=large_workflow,
            chunk_size=1000  # Small chunks to force splitting
        )
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["chunks"] > 1  # Should be split into multiple chunks
        assert mock_client.workflow_loaded is True
    
    def test_load_ui_native_method(self, mock_client, sample_workflow_dict):
        """Test UI native loading method specifically."""
        action = LoadWorkflowAction(
            workflow_source=sample_workflow_dict,
            method="ui_native"
        )
        result = action.execute(mock_client)
        
        assert result["method"] == "ui_native"
        assert mock_client.workflow_loaded is True
        
        # Verify localStorage was used
        assert any("localStorage.setItem" in call for call in mock_client.eval_js_calls)
        assert any("app.loadGraphData" in call for call in mock_client.eval_js_calls)
    
    def test_load_api_method_not_implemented(self, mock_client, sample_workflow_dict):
        """Test that API method raises NotImplementedError."""
        action = LoadWorkflowAction(
            workflow_source=sample_workflow_dict,
            method="api"
        )
        
        with pytest.raises(NotImplementedError):
            action.execute(mock_client)
    
    def test_load_hybrid_method_not_implemented(self, mock_client, sample_workflow_dict):
        """Test that hybrid method raises NotImplementedError."""
        action = LoadWorkflowAction(
            workflow_source=sample_workflow_dict,
            method="hybrid"
        )
        
        with pytest.raises(NotImplementedError):
            action.execute(mock_client)
    
    def test_javascript_execution_error(self, mock_client, sample_workflow_dict):
        """Test handling of JavaScript execution errors."""
        mock_client.error_on_eval = True
        
        action = LoadWorkflowAction(workflow_source=sample_workflow_dict)
        
        with pytest.raises(WorkflowLoadError, match="Failed to store chunk"):
            action.execute(mock_client)


# QueueWorkflowAction Tests

class TestQueueWorkflowAction:
    """Tests for QueueWorkflowAction."""
    
    def test_queue_ui_click_success(self, mock_client):
        """Test successful workflow queuing via UI click."""
        action = QueueWorkflowAction(method="ui_click")
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["clicked"] is True
        assert result["method"] == "ui_click"
        assert mock_client.queue_clicked is True
    
    def test_queue_button_not_found(self, mock_client):
        """Test error when Queue Prompt button not found."""
        mock_client.error_on_queue_button = True
        
        action = QueueWorkflowAction(method="ui_click")
        
        with pytest.raises(QueueError, match="not found"):
            action.execute(mock_client)
    
    def test_queue_http_api_not_implemented(self, mock_client):
        """Test that HTTP API method raises NotImplementedError."""
        action = QueueWorkflowAction(method="http_api")
        
        with pytest.raises(NotImplementedError):
            action.execute(mock_client)
    
    def test_queue_with_custom_wait(self, mock_client):
        """Test queuing with custom wait time."""
        action = QueueWorkflowAction(method="ui_click", wait_after_click=2.0)
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert action.wait_after_click == 2.0
    
    def test_queue_checks_button_before_clicking(self, mock_client):
        """Test that action checks for button existence before clicking."""
        action = QueueWorkflowAction(method="ui_click")
        action.execute(mock_client)
        
        # Should have made at least 2 eval_js calls:
        # 1. Check if button exists
        # 2. Click the button
        assert len(mock_client.eval_js_calls) >= 2
        
        # First call should check for button
        assert "Queue Prompt" in mock_client.eval_js_calls[0]
        assert "found" in mock_client.eval_js_calls[0]
        
        # Second call should click button
        assert "click()" in mock_client.eval_js_calls[1]


# GetPromptIDAction Tests

class TestGetPromptIDAction:
    """Tests for GetPromptIDAction."""
    
    def test_get_prompt_id_success(self, mock_client):
        """Test successful prompt ID retrieval."""
        # First queue a workflow to generate a prompt ID
        mock_client.queued_prompts.append("test-prompt-0001")
        
        action = GetPromptIDAction(timeout=5.0)
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["prompt_id"] == "test-prompt-0001"
        assert result["location"] == "pending"
    
    def test_get_prompt_id_timeout(self, mock_client):
        """Test timeout when no prompt ID available."""
        # Don't queue anything - should timeout
        action = GetPromptIDAction(timeout=1.0, check_interval=0.2)
        result = action.execute(mock_client)
        
        assert result["success"] is False
        assert result["prompt_id"] is None
        assert "Timeout" in result["reason"]
    
    def test_get_prompt_id_with_queue_length(self, mock_client):
        """Test that queue length is returned."""
        mock_client.queued_prompts.extend([
            "prompt-0001",
            "prompt-0002",
            "prompt-0003"
        ])
        
        action = GetPromptIDAction()
        result = action.execute(mock_client)
        
        assert result["success"] is True
        assert result["queue_length"] == 3
        assert result["prompt_id"] == "prompt-0003"  # Most recent
    
    def test_get_prompt_id_custom_check_interval(self, mock_client):
        """Test custom check interval."""
        action = GetPromptIDAction(timeout=5.0, check_interval=1.0)
        
        assert action.check_interval == 1.0
        assert action.timeout == 5.0


# Integration-style Tests

class TestWorkflowActionSequence:
    """Test sequences of actions working together."""
    
    def test_load_and_queue_workflow(self, mock_client, sample_workflow_path):
        """Test complete workflow: load, then queue."""
        # Load workflow
        load_action = LoadWorkflowAction(workflow_source=sample_workflow_path)
        load_result = load_action.execute(mock_client)
        
        assert load_result["success"] is True
        assert mock_client.workflow_loaded is True
        
        # Queue workflow
        queue_action = QueueWorkflowAction(method="ui_click")
        queue_result = queue_action.execute(mock_client)
        
        assert queue_result["success"] is True
        assert mock_client.queue_clicked is True
        
        # Get prompt ID
        get_id_action = GetPromptIDAction()
        id_result = get_id_action.execute(mock_client)
        
        assert id_result["success"] is True
        assert id_result["prompt_id"] is not None
    
    def test_multiple_workflow_queuing(self, mock_client, sample_workflow_dict):
        """Test queuing multiple workflows in sequence."""
        for i in range(3):
            # Load
            load_action = LoadWorkflowAction(workflow_source=sample_workflow_dict)
            load_action.execute(mock_client)
            
            # Queue
            queue_action = QueueWorkflowAction()
            queue_action.execute(mock_client)
        
        # Should have 3 prompts queued
        assert len(mock_client.queued_prompts) == 3
        
        # Get latest prompt ID
        get_id_action = GetPromptIDAction()
        result = get_id_action.execute(mock_client)
        
        assert result["queue_length"] == 3
