from unittest.mock import Mock, MagicMock, patch
from browser_agent.browser.playwright_driver import PlaywrightBrowserController
from browser_agent.browser.actions import (
    Navigate,
    Click,
    Type,
    WaitForSelector,
    WaitForUser,
    ExtractLinks,
)
import pytest


def test_playwright_controller_initialization():
    controller = PlaywrightBrowserController()
    assert controller.executable_path is None
    assert controller.headless is True
    assert controller._playwright is None
    assert controller._browser is None
    assert controller._page is None


def test_playwright_controller_with_custom_params():
    controller = PlaywrightBrowserController(
        executable_path="/usr/bin/brave",
        headless=False
    )
    assert controller.executable_path == "/usr/bin/brave"
    assert controller.headless is False


def test_playwright_controller_start():
    """Test starting the browser."""
    controller = PlaywrightBrowserController(headless=True)
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        assert controller._playwright is not None
        assert controller._browser is not None
        assert controller._page is not None
        
        # Check that launch was called with headless=True, timeout, and default args for headless chromium
        call_args = mock_playwright.chromium.launch.call_args
        assert call_args.kwargs["headless"] is True
        assert call_args.kwargs["timeout"] == 15000
        assert "--no-sandbox" in call_args.kwargs["args"]
        mock_browser.new_page.assert_called_once()
        mock_page.set_default_timeout.assert_called_once_with(30000)
        mock_page.set_default_navigation_timeout.assert_called_once_with(30000)


def test_playwright_controller_start_with_executable_path():
    """Test starting the browser with custom executable path."""
    controller = PlaywrightBrowserController(
        executable_path="/usr/bin/brave",
        headless=False
    )
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        # Check that launch was called with correct parameters
        call_args = mock_playwright.chromium.launch.call_args
        assert call_args.kwargs["headless"] is False
        assert call_args.kwargs["executable_path"] == "/usr/bin/brave"
        assert call_args.kwargs["timeout"] == 15000


def test_playwright_controller_start_already_started():
    """Test that starting twice doesn't create a new browser."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        controller.start()  # Second start should be no-op
        
        # Should only be called once
        mock_playwright.chromium.launch.assert_called_once()


def test_playwright_controller_stop():
    """Test stopping the browser."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    mock_browser = MagicMock()
    mock_playwright = MagicMock()
    
    controller._page = mock_page
    controller._browser = mock_browser
    controller._playwright = mock_playwright
    
    controller.stop()
    
    mock_page.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()
    
    assert controller._page is None
    assert controller._browser is None
    assert controller._playwright is None


def test_playwright_controller_get_observation():
    """Test getting observation from the page."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    mock_page.url = "https://example.com"
    mock_page.title.return_value = "Example Domain"
    
    # Mock button elements
    mock_button = MagicMock()
    mock_button.inner_text.return_value = "Submit"
    mock_button.evaluate.return_value = "button#submit"
    
    # Mock input elements
    mock_input = MagicMock()
    mock_input.evaluate.return_value = "input#search"
    mock_input.get_attribute.side_effect = lambda x: "q" if x == "name" else "test"
    
    mock_page.query_selector_all.side_effect = [
        [mock_button],  # buttons
        [mock_input]    # inputs
    ]
    
    controller._page = mock_page
    
    obs = controller.get_observation()
    
    assert obs.url == "https://example.com"
    assert obs.title == "Example Domain"
    assert len(obs.buttons) == 1
    assert obs.buttons[0].selector == "button#submit"
    assert obs.buttons[0].text == "Submit"
    assert len(obs.inputs) == 1
    assert obs.inputs[0].selector == "input#search"


def test_playwright_controller_get_observation_not_started():
    """Test that get_observation fails if browser not started."""
    controller = PlaywrightBrowserController()
    
    with pytest.raises(AssertionError, match="Browser not started"):
        controller.get_observation()


def test_playwright_controller_perform_navigate():
    """Test performing navigate action."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    action = Navigate(url="https://example.com")
    controller.perform(action)
    
    mock_page.goto.assert_called_once_with("https://example.com", wait_until="load")


def test_playwright_controller_perform_click():
    """Test performing click action."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    action = Click(selector="#button")
    controller.perform(action)
    
    mock_page.click.assert_called_once_with("#button")


def test_playwright_controller_perform_type():
    """Test performing type action without enter."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    action = Type(selector="#input", text="hello", press_enter=False)
    controller.perform(action)
    
    mock_page.fill.assert_called_once_with("#input", "hello")
    mock_page.press.assert_not_called()


def test_playwright_controller_perform_type_with_enter():
    """Test performing type action with enter."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    action = Type(selector="#input", text="hello", press_enter=True)
    controller.perform(action)
    
    mock_page.fill.assert_called_once_with("#input", "hello")
    mock_page.press.assert_called_once_with("#input", "Enter")


def test_playwright_controller_perform_wait_for_selector():
    """Test performing wait for selector action."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    action = WaitForSelector(selector="#element", timeout_ms=3000)
    controller.perform(action)
    
    mock_page.wait_for_selector.assert_called_once_with("#element", timeout=3000)


def test_playwright_controller_perform_not_started():
    """Test that perform fails if browser not started."""
    controller = PlaywrightBrowserController()
    
    action = Navigate(url="https://example.com")
    
    with pytest.raises(AssertionError, match="Browser not started"):
        controller.perform(action)


def test_playwright_controller_get_observation_with_exception_in_button():
    """Test that button text extraction handles exceptions."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    mock_page.url = "https://example.com"
    mock_page.title.return_value = "Example"
    
    # Mock button that raises exception
    mock_button = MagicMock()
    mock_button.inner_text.side_effect = Exception("Cannot get text")
    mock_button.evaluate.return_value = "button"
    
    mock_page.query_selector_all.side_effect = [
        [mock_button],  # buttons
        []              # inputs
    ]
    
    controller._page = mock_page
    
    obs = controller.get_observation()
    
    # Should have button with empty text
    assert len(obs.buttons) == 1
    assert obs.buttons[0].text == ""


def test_playwright_controller_perform_wait_for_user(monkeypatch):
    """Test performing wait for user action."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    controller._page = mock_page
    
    # Mock input() to simulate user pressing Enter
    mock_input = Mock(return_value="")
    monkeypatch.setattr('builtins.input', mock_input)
    
    action = WaitForUser(message="Press Enter...")
    controller.perform(action)
    
    mock_input.assert_called_once_with("Press Enter...")


def test_playwright_controller_perform_extract_links():
    """Test performing extract links action."""
    controller = PlaywrightBrowserController()
    
    mock_page = MagicMock()
    mock_element1 = MagicMock()
    mock_element1.get_attribute.return_value = "https://example.com/post/1"
    mock_element2 = MagicMock()
    mock_element2.get_attribute.return_value = "https://example.com/post/2"
    mock_element3 = MagicMock()
    mock_element3.get_attribute.return_value = None  # No href
    
    mock_page.query_selector_all.return_value = [mock_element1, mock_element2, mock_element3]
    controller._page = mock_page
    
    action = ExtractLinks(pattern='a[href*="/post/"]')
    controller.perform(action)
    
    mock_page.query_selector_all.assert_called_once_with('a[href*="/post/"]')
    
    links = controller.get_extracted_links()
    assert len(links) == 2
    assert "https://example.com/post/1" in links
    assert "https://example.com/post/2" in links


def test_playwright_controller_get_extracted_links_empty():
    """Test getting extracted links when none extracted."""
    controller = PlaywrightBrowserController()
    
    links = controller.get_extracted_links()
    assert links == []


def test_playwright_controller_get_extracted_links_returns_copy():
    """Test that get_extracted_links returns a copy."""
    controller = PlaywrightBrowserController()
    controller._extracted_links = ["link1", "link2"]
    
    links1 = controller.get_extracted_links()
    links2 = controller.get_extracted_links()
    
    # Should be equal but not the same object
    assert links1 == links2
    assert links1 is not links2


def test_playwright_controller_headless_with_default_args():
    """Test that headless mode includes default security args."""
    controller = PlaywrightBrowserController(headless=True)
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        call_args = mock_playwright.chromium.launch.call_args
        args = call_args.kwargs.get("args", [])
        
        # Check that default headless args are included
        assert "--no-sandbox" in args
        assert "--disable-setuid-sandbox" in args
        assert "--disable-dev-shm-usage" in args


def test_playwright_controller_non_headless_no_default_args():
    """Test that non-headless mode doesn't include default security args."""
    controller = PlaywrightBrowserController(headless=False)
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        call_args = mock_playwright.chromium.launch.call_args
        args = call_args.kwargs.get("args", [])
        
        # Non-headless should have empty args by default
        assert args == []


def test_playwright_controller_firefox_headless():
    """Test launching Firefox in headless mode."""
    controller = PlaywrightBrowserController(browser_type="firefox", headless=True)
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.firefox.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        # Verify firefox was launched
        mock_playwright.firefox.launch.assert_called_once()
        call_args = mock_playwright.firefox.launch.call_args
        assert call_args.kwargs["headless"] is True


def test_playwright_controller_webkit_headless():
    """Test launching WebKit in headless mode."""
    controller = PlaywrightBrowserController(browser_type="webkit", headless=True)
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.webkit.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        # Verify webkit was launched
        mock_playwright.webkit.launch.assert_called_once()
        call_args = mock_playwright.webkit.launch.call_args
        assert call_args.kwargs["headless"] is True


def test_playwright_controller_extra_launch_args_with_headless():
    """Test that extra launch args replace default headless args."""
    controller = PlaywrightBrowserController(
        headless=True,
        extra_launch_args=["--disable-gpu", "--window-size=1920,1080"]
    )
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        call_args = mock_playwright.chromium.launch.call_args
        args = call_args.kwargs.get("args", [])
        
        # When extra_launch_args is provided, it replaces the default args
        assert "--disable-gpu" in args
        assert "--window-size=1920,1080" in args
        assert len(args) == 2  # Only the custom args


def test_playwright_controller_headless_parameter():
    """Test that headless parameter is correctly stored."""
    # Test with headless=True
    controller_headless = PlaywrightBrowserController(headless=True)
    assert controller_headless.headless is True
    
    # Test with headless=False
    controller_not_headless = PlaywrightBrowserController(headless=False)
    assert controller_not_headless.headless is False
