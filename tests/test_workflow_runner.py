"""Tests for the Canvas Workflow Runner."""
import json
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

from browser_agent.agent.workflow_runner import CanvasWorkflowRunner, WorkflowParameter
from browser_agent.browser.actions import Navigate, WaitForSelector, ExecuteJS, Click


def test_workflow_parameter_init():
    """Test WorkflowParameter initialization."""
    param = WorkflowParameter(node_id="3", field_name="seed", value=42)
    assert param.node_id == "3"
    assert param.field_name == "seed"
    assert param.value == 42


def test_canvas_workflow_runner_init():
    """Test CanvasWorkflowRunner initialization."""
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(
        browser=mock_browser,
        webui_url="http://localhost:8188",
        completion_check_interval=1.0,
        max_wait_time=300.0,
    )
    
    assert runner.browser == mock_browser
    assert runner.webui_url == "http://localhost:8188"
    assert runner.completion_check_interval == 1.0
    assert runner.max_wait_time == 300.0
    assert runner._workflow_data is None
    assert runner._parameters == []


def test_load_workflow_success(tmp_path):
    """Test loading a workflow from a JSON file."""
    # Create a temporary workflow file
    workflow_file = tmp_path / "test_workflow.json"
    workflow_data = {
        "1": {"class_type": "LoadImage", "inputs": {}},
        "2": {"class_type": "SaveImage", "inputs": {}},
    }
    workflow_file.write_text(json.dumps(workflow_data))
    
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    runner.load_workflow(workflow_file)
    
    assert runner._workflow_data == workflow_data


def test_load_workflow_file_not_found():
    """Test loading a workflow file that doesn't exist."""
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    with pytest.raises(FileNotFoundError):
        runner.load_workflow("/nonexistent/workflow.json")


def test_set_parameter():
    """Test setting a workflow parameter."""
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    runner.set_parameter("3", "seed", 42)
    runner.set_parameter("4", "steps", 20)
    
    assert len(runner._parameters) == 2
    assert runner._parameters[0].node_id == "3"
    assert runner._parameters[0].field_name == "seed"
    assert runner._parameters[0].value == 42
    assert runner._parameters[1].node_id == "4"
    assert runner._parameters[1].field_name == "steps"
    assert runner._parameters[1].value == 20


def test_run_without_workflow():
    """Test running without loading a workflow first."""
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    with pytest.raises(RuntimeError, match="No workflow loaded"):
        runner.run()


def test_run_with_workflow(tmp_path):
    """Test running a workflow."""
    # Create a temporary workflow file
    workflow_file = tmp_path / "test_workflow.json"
    workflow_data = {
        "1": {"class_type": "LoadImage", "inputs": {}},
        "2": {"class_type": "SaveImage", "inputs": {}},
    }
    workflow_file.write_text(json.dumps(workflow_data))
    
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    # Load workflow
    runner.load_workflow(workflow_file)
    
    # Set some parameters
    runner.set_parameter("1", "image", "test.png")
    
    # Mock the perform method to avoid actual browser interactions
    runner.run()
    
    # Verify that browser.perform was called
    assert mock_browser.perform.called
    
    # Check that Navigate was called
    calls = mock_browser.perform.call_args_list
    assert any(isinstance(call[0][0], Navigate) for call in calls)
    assert any(isinstance(call[0][0], WaitForSelector) for call in calls)
    assert any(isinstance(call[0][0], ExecuteJS) for call in calls)


def test_wait_for_completion_success():
    """Test waiting for workflow completion when it succeeds."""
    mock_browser = Mock()
    
    # Mock get_last_js_result to return completion status
    mock_browser.get_last_js_result.return_value = {"running": 0, "pending": 0}
    
    runner = CanvasWorkflowRunner(
        browser=mock_browser,
        webui_url="http://localhost:8188",
        completion_check_interval=0.1,
        max_wait_time=5.0,
    )
    
    result = runner.wait_for_completion()
    
    assert result is True


def test_wait_for_completion_timeout():
    """Test waiting for workflow completion when it times out."""
    mock_browser = Mock()
    
    # Mock get_last_js_result to return never-completing status
    mock_browser.get_last_js_result.return_value = {"running": 1, "pending": 0}
    
    runner = CanvasWorkflowRunner(
        browser=mock_browser,
        webui_url="http://localhost:8188",
        completion_check_interval=0.1,
        max_wait_time=0.3,  # Short timeout for testing
    )
    
    result = runner.wait_for_completion()
    
    assert result is False


def test_apply_parameter():
    """Test applying a parameter via JavaScript."""
    mock_browser = Mock()
    runner = CanvasWorkflowRunner(browser=mock_browser, webui_url="http://localhost:8188")
    
    param = WorkflowParameter(node_id="3", field_name="seed", value=42)
    runner._apply_parameter(param)
    
    # Verify that ExecuteJS was called
    assert mock_browser.perform.called
    call = mock_browser.perform.call_args_list[0]
    assert isinstance(call[0][0], ExecuteJS)
