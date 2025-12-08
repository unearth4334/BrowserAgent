from unittest.mock import MagicMock, patch
from browser_agent.cli import simple_search, interactive
from browser_agent.agent.core import TaskResult
from browser_agent.browser.observation import PageObservation
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


def test_server_command_with_defaults():
    """Test server command with default settings."""
    with patch('browser_agent.cli.BrowserServer') as MockServer, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = None
        mock_from_env.return_value = mock_env_settings
        
        mock_server = MagicMock()
        MockServer.return_value = mock_server
        
        from browser_agent.cli import server
        server(port=9999, url="https://example.com", no_wait=False, browser_exe=None)
        
        MockServer.assert_called_once_with(browser_exe=None, port=9999)
        mock_server.start.assert_called_once_with(initial_url="https://example.com", wait_for_auth=True)


def test_server_command_with_browser_exe():
    """Test server command with custom browser executable."""
    with patch('browser_agent.cli.BrowserServer') as MockServer, \
         patch('browser_agent.cli.Settings.from_env') as mock_from_env:
        
        mock_env_settings = MagicMock()
        mock_env_settings.browser_executable_path = "/usr/bin/brave-browser"
        mock_from_env.return_value = mock_env_settings
        
        mock_server = MagicMock()
        MockServer.return_value = mock_server
        
        from browser_agent.cli import server
        server(port=8080, url="https://example.com", no_wait=True, browser_exe="/usr/bin/firefox")
        
        # Should use explicit browser_exe, not env settings
        MockServer.assert_called_once_with(browser_exe="/usr/bin/firefox", port=8080)
        mock_server.start.assert_called_once_with(initial_url="https://example.com", wait_for_auth=False)
