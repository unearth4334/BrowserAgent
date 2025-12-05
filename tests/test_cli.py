from unittest.mock import Mock, MagicMock, patch
from browser_agent.cli import simple_search, patreon_collection, interactive
from browser_agent.agent.core import TaskResult
from browser_agent.browser.observation import PageObservation, ButtonInfo, InputInfo
import pytest


def test_simple_search_function_success():
    """Test simple search function execution."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('builtins.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://duckduckgo.com/?q=test",
            title="test at DuckDuckGo",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Task completed",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        # Call the function directly
        simple_search(query="test", headless=True, browser_exe=None)
        
        mock_controller.stop.assert_called_once()
        MockAgent.assert_called_once()


def test_simple_search_function_failure():
    """Test failed simple search execution."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('builtins.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_result = TaskResult(
            success=False,
            reason="Max steps exceeded",
            final_observation=None
        )
        mock_agent.run_task.return_value = mock_result
        
        simple_search(query="test", headless=True, browser_exe=None)
        
        mock_controller.stop.assert_called_once()


def test_simple_search_function_with_custom_exe():
    """Test simple search with custom browser executable."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('builtins.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_result = TaskResult(success=True, reason="Done", final_observation=None)
        mock_agent.run_task.return_value = mock_result
        
        simple_search(query="test", headless=False, browser_exe="/usr/bin/brave")
        
        # Verify controller was created with custom executable path
        MockController.assert_called_once()
        call_kwargs = MockController.call_args[1]
        assert call_kwargs['executable_path'] == "/usr/bin/brave"
        assert call_kwargs['headless'] is False


def test_simple_search_function_ensures_stop_on_exception():
    """Test that browser is stopped even if exception occurs."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_agent.run_task.side_effect = Exception("Test error")
        
        with pytest.raises(Exception, match="Test error"):
            simple_search(query="test", headless=True, browser_exe=None)
        
        # Controller stop should still be called
        mock_controller.stop.assert_called_once()


def test_simple_search_function_with_observation_output():
    """Test that observation details are printed on success."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://example.com/results",
            title="Results Page",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Task completed",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        # Capture output by patching rich.print
        with patch('browser_agent.cli.print') as mock_print:
            simple_search(query="query", headless=True, browser_exe=None)
            
            # Verify that URL and title were printed
            call_args_str = ' '.join([str(call) for call in mock_print.call_args_list])
            assert "https://example.com/results" in call_args_str
            assert "Results Page" in call_args_str


def test_patreon_collection_function_success():
    """Test patreon collection extraction success."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('browser_agent.cli.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        mock_controller.get_extracted_links.return_value = [
            "https://www.patreon.com/posts/post1",
            "https://www.patreon.com/posts/post2",
        ]
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://www.patreon.com/collection/1611241",
            title="Collection",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Links extracted",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        patreon_collection(collection_id="1611241", headless=True, browser_exe=None)
        
        mock_controller.stop.assert_called_once()
        mock_controller.get_extracted_links.assert_called()


def test_patreon_collection_function_with_fallback():
    """Test patreon collection with fallback link extraction."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('browser_agent.cli.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        # First call returns empty, second returns fallback links
        mock_controller.get_extracted_links.side_effect = [
            [],  # Initial extraction
            ["https://www.patreon.com/posts/fallback1"],  # Fallback extraction
        ]
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://www.patreon.com/collection/1611241",
            title="Collection",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Task completed",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        patreon_collection(collection_id="1611241", headless=True, browser_exe=None)
        
        # Should have tried fallback extraction
        assert mock_controller.perform.called
        mock_controller.stop.assert_called_once()


def test_patreon_collection_function_failure():
    """Test patreon collection extraction failure."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('browser_agent.cli.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_result = TaskResult(
            success=False,
            reason="Authentication timeout",
            final_observation=None
        )
        mock_agent.run_task.return_value = mock_result
        
        patreon_collection(collection_id="1611241", headless=True, browser_exe=None)
        
        mock_controller.stop.assert_called_once()


def test_interactive_function_with_url():
    """Test interactive mode with initial URL."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.InteractiveBrowserSession') as MockSession, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        interactive(url="https://example.com", headless=False, browser_exe="/usr/bin/brave")
        
        # Controller should be started and navigate performed
        mock_controller.start.assert_called_once()
        mock_controller.perform.assert_called_once()
        mock_session.start.assert_called_once()


def test_interactive_function_without_url():
    """Test interactive mode without initial URL."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.InteractiveBrowserSession') as MockSession, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        MockController.return_value = mock_controller
        
        mock_session = MagicMock()
        MockSession.return_value = mock_session
        
        interactive(url=None, headless=True, browser_exe=None)
        
        # Controller should not be started separately
        mock_controller.start.assert_not_called()
        mock_session.start.assert_called_once()


def test_patreon_collection_with_many_fallback_links():
    """Test patreon collection with many fallback links (>20)."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('browser_agent.cli.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        # Generate 25 fallback links
        fallback_links = [f"https://www.patreon.com/posts/link{i}" for i in range(25)]
        mock_controller.get_extracted_links.side_effect = [
            [],  # Initial extraction
            fallback_links,  # Fallback extraction
        ]
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://www.patreon.com/collection/1611241",
            title="Collection",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Task completed",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        patreon_collection(collection_id="1611241", headless=True, browser_exe=None)
        
        # Should show message about "... and X more"
        mock_controller.stop.assert_called_once()


def test_patreon_collection_no_fallback_links():
    """Test patreon collection when even fallback extraction finds nothing."""
    with patch('browser_agent.cli.PlaywrightBrowserController') as MockController, \
         patch('browser_agent.cli.Agent') as MockAgent, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env, \
         patch('browser_agent.cli.print') as mock_print:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_env_settings.headless = True
        mock_from_env.return_value = mock_env_settings
        
        mock_controller = MagicMock()
        # Both extractions return empty
        mock_controller.get_extracted_links.side_effect = [[], []]
        MockController.return_value = mock_controller
        
        mock_agent = MagicMock()
        MockAgent.return_value = mock_agent
        
        mock_obs = PageObservation(
            url="https://www.patreon.com/collection/1611241",
            title="Collection",
            buttons=[],
            inputs=[]
        )
        mock_result = TaskResult(
            success=True,
            reason="Task completed",
            final_observation=mock_obs
        )
        mock_agent.run_task.return_value = mock_result
        
        patreon_collection(collection_id="1611241", headless=True, browser_exe=None)
        
        # Should show "No post links found at all" message
        mock_controller.stop.assert_called_once()
