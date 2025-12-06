from unittest.mock import MagicMock, patch, mock_open
from browser_agent.interactive_session import InteractiveBrowserSession
from browser_agent.browser.observation import PageObservation, ButtonInfo, InputInfo
from browser_agent.browser.actions import Navigate, Click, Type, WaitForSelector, ExtractLinks
import json
import pytest


@pytest.fixture
def mock_controller():
    """Create a mock browser controller."""
    controller = MagicMock()
    controller._page = MagicMock()
    
    # Default observation
    obs = PageObservation(
        url="https://example.com",
        title="Example Page",
        buttons=[
            ButtonInfo(selector="button#submit", text="Submit"),
            ButtonInfo(selector="button.cancel", text="Cancel"),
        ],
        inputs=[
            InputInfo(selector="input#username", name="username", value=""),
            InputInfo(selector="input#password", name="password", value=""),
        ]
    )
    controller.get_observation.return_value = obs
    controller.get_extracted_links.return_value = []
    
    return controller


@pytest.fixture
def session(mock_controller):
    """Create an interactive session with mock controller."""
    return InteractiveBrowserSession(mock_controller)


def test_interactive_session_initialization(mock_controller):
    """Test session initialization."""
    session = InteractiveBrowserSession(mock_controller)
    assert session.controller == mock_controller
    assert session.extracted_links == []
    assert session.running is False


def test_handle_command_help(session):
    """Test help command."""
    with patch.object(session, '_show_help') as mock_help:
        session._handle_command("help")
        mock_help.assert_called_once()


def test_handle_command_quit(session):
    """Test quit command."""
    session.running = True
    session._handle_command("quit")
    assert session.running is False


def test_handle_command_exit(session):
    """Test exit command."""
    session.running = True
    session._handle_command("exit")
    assert session.running is False


def test_handle_command_goto(session, mock_controller):
    """Test goto command."""
    with patch.object(session, '_show_info') as mock_show_info:
        session._handle_command("goto https://example.com")
        
        mock_controller.perform.assert_called_once()
        call_args = mock_controller.perform.call_args[0][0]
        assert isinstance(call_args, Navigate)
        assert call_args.url == "https://example.com"
        mock_show_info.assert_called_once()


def test_handle_command_goto_without_url(session, mock_controller):
    """Test goto command without URL shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("goto")
        mock_controller.perform.assert_not_called()
        mock_print.assert_called_once()


def test_handle_command_extract(session, mock_controller):
    """Test extract command."""
    mock_controller.get_extracted_links.return_value = [
        "https://example.com/page1",
        "https://example.com/page2",
    ]
    
    with patch.object(session.console, 'print'):
        session._handle_command("extract a.link")
        
        mock_controller.perform.assert_called_once()
        call_args = mock_controller.perform.call_args[0][0]
        assert isinstance(call_args, ExtractLinks)
        assert call_args.pattern == "a.link"
        assert len(session.extracted_links) == 2


def test_handle_command_extract_many_links(session, mock_controller):
    """Test extract command with more than 10 links."""
    # Generate 15 links
    links = [f"https://example.com/page{i}" for i in range(15)]
    mock_controller.get_extracted_links.return_value = links
    
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("extract a.link")
        
        # Should show "... and X more" message
        assert len(session.extracted_links) == 15
        # Verify console was used to print
        assert mock_print.called


def test_handle_command_extract_without_selector(session, mock_controller):
    """Test extract command without selector shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("extract")
        mock_controller.perform.assert_not_called()
        mock_print.assert_called_once()


def test_handle_command_click(session, mock_controller):
    """Test click command."""
    with patch.object(session, '_show_info') as mock_show_info:
        session._handle_command("click button#submit")
        
        mock_controller.perform.assert_called_once()
        call_args = mock_controller.perform.call_args[0][0]
        assert isinstance(call_args, Click)
        assert call_args.selector == "button#submit"
        mock_show_info.assert_called_once()


def test_handle_command_click_without_selector(session, mock_controller):
    """Test click command without selector shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("click")
        mock_controller.perform.assert_not_called()


def test_handle_command_type(session, mock_controller):
    """Test type command."""
    session._handle_command("type input#username testuser")
    
    mock_controller.perform.assert_called_once()
    call_args = mock_controller.perform.call_args[0][0]
    assert isinstance(call_args, Type)
    assert call_args.selector == "input#username"
    assert call_args.text == "testuser"


def test_handle_command_type_without_text(session, mock_controller):
    """Test type command without text shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("type input#username")
        mock_controller.perform.assert_not_called()


def test_handle_command_wait(session, mock_controller):
    """Test wait command."""
    session._handle_command("wait div.content")
    
    mock_controller.perform.assert_called_once()
    call_args = mock_controller.perform.call_args[0][0]
    assert isinstance(call_args, WaitForSelector)
    assert call_args.selector == "div.content"
    assert call_args.timeout_ms == 10000


def test_handle_command_wait_with_timeout(session, mock_controller):
    """Test wait command with custom timeout."""
    session._handle_command("wait div.content 5000")
    
    mock_controller.perform.assert_called_once()
    call_args = mock_controller.perform.call_args[0][0]
    assert isinstance(call_args, WaitForSelector)
    assert call_args.selector == "div.content"
    assert call_args.timeout_ms == 5000


def test_handle_command_wait_without_selector(session, mock_controller):
    """Test wait command without selector shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("wait")
        mock_controller.perform.assert_not_called()


def test_handle_command_info(session):
    """Test info command."""
    with patch.object(session, '_show_info') as mock_show_info:
        session._handle_command("info")
        mock_show_info.assert_called_once()


def test_handle_command_links(session):
    """Test links command."""
    with patch.object(session, '_show_links') as mock_show_links:
        session._handle_command("links")
        mock_show_links.assert_called_once()


def test_handle_command_save(session):
    """Test save command."""
    with patch.object(session, '_save_links') as mock_save_links:
        session._handle_command("save output.json")
        mock_save_links.assert_called_once_with("output.json")


def test_handle_command_save_without_filename(session):
    """Test save command without filename shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("save")
        # Should show usage message
        assert mock_print.called


def test_handle_command_html(session):
    """Test html command."""
    with patch.object(session, '_show_html') as mock_show_html:
        session._handle_command("html")
        mock_show_html.assert_called_once()


def test_handle_command_eval(session):
    """Test eval command."""
    with patch.object(session, '_eval_js') as mock_eval_js:
        session._handle_command("eval document.title")
        mock_eval_js.assert_called_once_with("document.title")


def test_handle_command_eval_without_code(session):
    """Test eval command without code shows usage."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("eval")
        assert mock_print.called


def test_handle_command_buttons(session):
    """Test buttons command."""
    with patch.object(session, '_show_buttons') as mock_show_buttons:
        session._handle_command("buttons")
        mock_show_buttons.assert_called_once()


def test_handle_command_inputs(session):
    """Test inputs command."""
    with patch.object(session, '_show_inputs') as mock_show_inputs:
        session._handle_command("inputs")
        mock_show_inputs.assert_called_once()


def test_handle_command_unknown(session):
    """Test unknown command shows error."""
    with patch.object(session.console, 'print') as mock_print:
        session._handle_command("unknown_command")
        # Should print error about unknown command
        assert mock_print.call_count >= 1


def test_show_info(session, mock_controller):
    """Test _show_info displays page information."""
    with patch.object(session.console, 'print'):
        session._show_info()
        mock_controller.get_observation.assert_called()


def test_show_links_with_links(session):
    """Test _show_links with extracted links."""
    session.extracted_links = ["https://example.com/1", "https://example.com/2"]
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_links()
        assert mock_print.call_count >= 3  # Header + 2 links


def test_show_links_without_links(session):
    """Test _show_links without extracted links."""
    session.extracted_links = []
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_links()
        assert mock_print.call_count == 1  # Just the warning message


def test_save_links_success(session, mock_controller):
    """Test _save_links successfully saves to file."""
    session.extracted_links = ["https://example.com/1", "https://example.com/2"]
    
    mock_obs = PageObservation(
        url="https://example.com",
        title="Test",
        buttons=[],
        inputs=[]
    )
    mock_controller.get_observation.return_value = mock_obs
    
    m_open = mock_open()
    with patch('builtins.open', m_open), \
         patch.object(session.console, 'print'):
        session._save_links("test.json")
        
        m_open.assert_called_once_with("test.json", 'w')
        handle = m_open()
        
        # Verify json.dump was called with correct data
        written_data = ''.join([call.args[0] for call in handle.write.call_args_list])
        data = json.loads(written_data)
        assert data['url'] == "https://example.com"
        assert data['count'] == 2
        assert len(data['links']) == 2


def test_save_links_no_links(session):
    """Test _save_links with no links to save."""
    session.extracted_links = []
    
    with patch.object(session.console, 'print') as mock_print:
        session._save_links("test.json")
        # Should show warning
        assert mock_print.called


def test_save_links_error(session):
    """Test _save_links handles errors."""
    session.extracted_links = ["https://example.com/1"]
    
    with patch('builtins.open', side_effect=IOError("Permission denied")), \
         patch.object(session.console, 'print') as mock_print:
        session._save_links("test.json")
        # Should show error message
        assert any("Error" in str(call) for call in mock_print.call_args_list)


def test_show_html(session, mock_controller):
    """Test _show_html displays page HTML."""
    mock_controller._page.content.return_value = "<html><body>Test content</body></html>"
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_html()
        mock_controller._page.content.assert_called_once()
        assert mock_print.call_count >= 1


def test_show_html_long_content(session, mock_controller):
    """Test _show_html truncates long content."""
    long_html = "<html>" + "x" * 2000 + "</html>"
    mock_controller._page.content.return_value = long_html
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_html()
        # Should print truncated message
        assert mock_print.call_count >= 2  # Content + truncation message


def test_eval_js_success(session, mock_controller):
    """Test _eval_js executes JavaScript."""
    mock_controller._page.evaluate.return_value = "Example Page"
    
    with patch.object(session.console, 'print'):
        session._eval_js("document.title")
        mock_controller._page.evaluate.assert_called_once_with("document.title")


def test_eval_js_error(session, mock_controller):
    """Test _eval_js handles JavaScript errors."""
    mock_controller._page.evaluate.side_effect = Exception("JS Error")
    
    with patch.object(session.console, 'print') as mock_print:
        session._eval_js("invalid.code")
        # Should show error message
        assert any("error" in str(call).lower() for call in mock_print.call_args_list)


def test_show_buttons(session, mock_controller):
    """Test _show_buttons displays button information."""
    with patch.object(session.console, 'print'):
        session._show_buttons()
        mock_controller.get_observation.assert_called()


def test_show_buttons_many(session, mock_controller):
    """Test _show_buttons with more than 20 buttons."""
    buttons = [ButtonInfo(selector=f"button#{i}", text=f"Button {i}") for i in range(25)]
    obs = PageObservation(url="https://example.com", title="Test", buttons=buttons, inputs=[])
    mock_controller.get_observation.return_value = obs
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_buttons()
        # Should show message about "Showing first 20 of X buttons"
        assert mock_print.call_count >= 2


def test_show_buttons_no_buttons(session, mock_controller):
    """Test _show_buttons when no buttons exist."""
    obs = PageObservation(url="https://example.com", title="Test", buttons=[], inputs=[])
    mock_controller.get_observation.return_value = obs
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_buttons()
        assert mock_print.called


def test_show_inputs(session, mock_controller):
    """Test _show_inputs displays input information."""
    with patch.object(session.console, 'print'):
        session._show_inputs()
        mock_controller.get_observation.assert_called()


def test_show_inputs_many(session, mock_controller):
    """Test _show_inputs with more than 20 inputs."""
    inputs = [InputInfo(selector=f"input#{i}", name=f"field{i}", value="") for i in range(25)]
    obs = PageObservation(url="https://example.com", title="Test", buttons=[], inputs=inputs)
    mock_controller.get_observation.return_value = obs
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_inputs()
        # Should show message about "Showing first 20 of X inputs"
        assert mock_print.call_count >= 2


def test_show_inputs_no_inputs(session, mock_controller):
    """Test _show_inputs when no inputs exist."""
    obs = PageObservation(url="https://example.com", title="Test", buttons=[], inputs=[])
    mock_controller.get_observation.return_value = obs
    
    with patch.object(session.console, 'print') as mock_print:
        session._show_inputs()
        assert mock_print.called


def test_show_help(session):
    """Test _show_help displays command list."""
    with patch.object(session.console, 'print') as mock_print:
        session._show_help()
        # Should print a table
        assert mock_print.called


def test_start_and_stop(session, mock_controller):
    """Test session start and stop lifecycle."""
    # Mock the input to exit immediately
    with patch('builtins.input', side_effect=['quit']), \
         patch.object(session, '_show_info'), \
         patch.object(session.console, 'print'):
        session.start()
        
        mock_controller.start.assert_called_once()
        mock_controller.stop.assert_called_once()
        assert session.running is False


def test_start_with_empty_command(session, mock_controller):
    """Test session handles empty commands."""
    with patch('builtins.input', side_effect=['', 'quit']), \
         patch.object(session, '_show_info'), \
         patch.object(session.console, 'print'):
        session.start()
        
        # Should skip empty command and continue to quit
        mock_controller.stop.assert_called_once()


def test_start_handles_keyboard_interrupt(session, mock_controller):
    """Test session handles Ctrl+C gracefully."""
    with patch('builtins.input', side_effect=[KeyboardInterrupt(), 'quit']), \
         patch.object(session, '_show_info'), \
         patch.object(session.console, 'print'):
        session.start()
        
        mock_controller.stop.assert_called_once()


def test_start_handles_eof(session, mock_controller):
    """Test session handles EOF gracefully."""
    with patch('builtins.input', side_effect=EOFError()), \
         patch.object(session, '_show_info'), \
         patch.object(session.console, 'print'):
        session.start()
        
        mock_controller.stop.assert_called_once()


def test_start_handles_command_error(session, mock_controller):
    """Test session handles command errors gracefully."""
    with patch('builtins.input', side_effect=['goto https://bad', 'quit']), \
         patch.object(session, '_show_info'), \
         patch.object(session.console, 'print'):
        # Make perform raise an error
        mock_controller.perform.side_effect = Exception("Navigation failed")
        
        session.start()
        
        # Session should continue after error
        mock_controller.stop.assert_called_once()
