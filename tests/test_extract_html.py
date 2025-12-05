"""Tests for ExtractHTML action and related functionality."""
from unittest.mock import Mock, MagicMock, patch
import pytest

from browser_agent.browser.actions import ExtractHTML
from browser_agent.browser.playwright_driver import PlaywrightBrowserController


def test_extract_html_action_creation():
    """Test creating ExtractHTML action."""
    action = ExtractHTML(selector='div[class*="content"]')
    assert action.selector == 'div[class*="content"]'


def test_extract_html_action_different_selectors():
    """Test ExtractHTML with various selector types."""
    action1 = ExtractHTML(selector='#main-content')
    action2 = ExtractHTML(selector='.post-description')
    action3 = ExtractHTML(selector='article > div')
    
    assert action1.selector == '#main-content'
    assert action2.selector == '.post-description'
    assert action3.selector == 'article > div'


def test_playwright_controller_extract_html_initialization():
    """Test that controller initializes with empty extracted HTML."""
    controller = PlaywrightBrowserController()
    assert controller._extracted_html == ""


def test_playwright_controller_perform_extract_html():
    """Test performing extract HTML action."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_element = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Setup element with HTML content
        mock_element.inner_html.return_value = '<p>Test content</p>'
        mock_page.query_selector.return_value = mock_element
        
        controller.start()
        action = ExtractHTML(selector='div.content')
        controller.perform(action)
        
        # Verify selector was called
        mock_page.query_selector.assert_called_once_with('div.content')
        mock_element.inner_html.assert_called_once()
        
        # Verify HTML was stored
        assert controller._extracted_html == '<p>Test content</p>'


def test_playwright_controller_extract_html_no_element():
    """Test extracting HTML when element is not found."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # No element found
        mock_page.query_selector.return_value = None
        
        controller.start()
        action = ExtractHTML(selector='div.nonexistent')
        controller.perform(action)
        
        # Verify empty string is stored
        assert controller._extracted_html == ""


def test_playwright_controller_get_extracted_html():
    """Test getting extracted HTML."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_element = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        mock_element.inner_html.return_value = '<div><h1>Title</h1><p>Content</p></div>'
        mock_page.query_selector.return_value = mock_element
        
        controller.start()
        action = ExtractHTML(selector='article')
        controller.perform(action)
        
        html = controller.get_extracted_html()
        assert html == '<div><h1>Title</h1><p>Content</p></div>'


def test_playwright_controller_get_extracted_html_empty():
    """Test getting extracted HTML when none extracted."""
    controller = PlaywrightBrowserController()
    html = controller.get_extracted_html()
    assert html == ""


def test_playwright_controller_extract_html_complex_content():
    """Test extracting complex HTML with nested elements."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_element = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        complex_html = '''
        <div class="post-content">
            <p><strong>Title</strong></p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <blockquote>
                <p>Quote text</p>
            </blockquote>
            <a href="https://example.com">Link</a>
        </div>
        '''
        mock_element.inner_html.return_value = complex_html
        mock_page.query_selector.return_value = mock_element
        
        controller.start()
        action = ExtractHTML(selector='div.post-content')
        controller.perform(action)
        
        html = controller.get_extracted_html()
        assert '<strong>Title</strong>' in html
        assert '<ul>' in html
        assert '<blockquote>' in html
        assert 'https://example.com' in html


def test_playwright_controller_extract_html_overwrites_previous():
    """Test that extracting HTML overwrites previous extraction."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        controller.start()
        
        # First extraction
        mock_element1 = MagicMock()
        mock_element1.inner_html.return_value = '<p>First content</p>'
        mock_page.query_selector.return_value = mock_element1
        
        controller.perform(ExtractHTML(selector='div.first'))
        assert controller._extracted_html == '<p>First content</p>'
        
        # Second extraction should overwrite
        mock_element2 = MagicMock()
        mock_element2.inner_html.return_value = '<p>Second content</p>'
        mock_page.query_selector.return_value = mock_element2
        
        controller.perform(ExtractHTML(selector='div.second'))
        assert controller._extracted_html == '<p>Second content</p>'


def test_extract_html_with_special_characters():
    """Test extracting HTML with special characters and entities."""
    controller = PlaywrightBrowserController()
    
    with patch('browser_agent.browser.playwright_driver.sync_playwright') as mock_pw:
        mock_playwright = MagicMock()
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_element = MagicMock()
        
        mock_pw.return_value.start.return_value = mock_playwright
        mock_playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        html_with_entities = '<p>Test &lt;script&gt; &amp; &quot;quotes&quot;</p>'
        mock_element.inner_html.return_value = html_with_entities
        mock_page.query_selector.return_value = mock_element
        
        controller.start()
        controller.perform(ExtractHTML(selector='div'))
        
        html = controller.get_extracted_html()
        assert '&lt;' in html
        assert '&amp;' in html
        assert '&quot;' in html
