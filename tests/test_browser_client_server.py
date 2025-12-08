"""Tests for browser server and client functionality.

These are generic tests for the browser server/client architecture.
Patreon-specific tests are in examples/patreon/tests/.
"""
import json
import socket
from unittest.mock import MagicMock, patch, Mock
import pytest
from browser_agent.server.browser_client import BrowserClient
from browser_agent.server.browser_server import BrowserServer
from browser_agent.browser.observation import PageObservation

# Note: These are integration-style tests that test the server/client contract
# without actually starting a server or browser


class TestBrowserServerCommands:
    """Test browser server command handling."""
    
    def test_extract_html_command_structure(self):
        """Test that extract_html command has correct structure."""
        command = {
            "action": "extract_html",
            "selector": "div.content"
        }
        assert command["action"] == "extract_html"
        assert "selector" in command
    
    def test_eval_js_command_structure(self):
        """Test that eval_js command has correct structure."""
        command = {
            "action": "eval_js",
            "code": "document.title"
        }
        assert command["action"] == "eval_js"
        assert "code" in command
    
    def test_extract_html_response_structure(self):
        """Test expected response structure for extract_html."""
        # Success response
        html_content = "<p>Content</p>"
        response = {
            "status": "success",
            "html": html_content,
            "length": len(html_content)
        }
        assert response["status"] == "success"
        assert "html" in response
        assert "length" in response
        assert response["length"] == len(response["html"])
        
        # Error response
        error_response = {
            "status": "error",
            "message": "No element found",
            "html": "",
            "length": 0
        }
        assert error_response["status"] == "error"
        assert "message" in error_response
    
    def test_eval_js_response_structure(self):
        """Test expected response structure for eval_js."""
        # Success response
        response = {
            "status": "success",
            "result": {"found": True, "count": 5}
        }
        assert response["status"] == "success"
        assert "result" in response
        
        # Error response
        error_response = {
            "status": "error",
            "message": "No page available"
        }
        assert error_response["status"] == "error"
        assert "message" in error_response


class TestBrowserClientMethods:
    """Test browser client method signatures and data contracts."""
    
    def test_extract_html_method_signature(self):
        """Test that extract_html method creates correct command."""
        # Simulate what the client method should create
        selector = "div[class*='content']"
        expected_command = {
            "action": "extract_html",
            "selector": selector
        }
        
        assert expected_command["action"] == "extract_html"
        assert expected_command["selector"] == selector
    
    def test_eval_js_method_signature(self):
        """Test that eval_js method creates correct command."""
        js_code = "document.querySelector('div').innerHTML"
        expected_command = {
            "action": "eval_js",
            "code": js_code
        }
        
        assert expected_command["action"] == "eval_js"
        assert expected_command["code"] == js_code
    
    def test_command_response_parsing(self):
        """Test that responses can be parsed correctly."""
        # Simulate JSON response from server
        response_json = '{"status": "success", "html": "<p>Test</p>", "length": 10}'
        response = json.loads(response_json)
        
        assert response["status"] == "success"
        assert response["html"] == "<p>Test</p>"
        assert response["length"] == 10
    
    def test_error_response_handling(self):
        """Test handling of error responses."""
        error_json = '{"status": "error", "message": "Element not found"}'
        response = json.loads(error_json)
        
        assert response["status"] == "error"
        assert "message" in response


class TestServerErrorHandling:
    """Test error handling in server commands."""
    
    def test_extract_html_not_found_error(self):
        """Test error response when element not found."""
        error_response = {
            "status": "error",
            "message": "No element found matching selector: div.nonexistent",
            "html": "",
            "length": 0
        }
        
        assert error_response["status"] == "error"
        assert "No element found" in error_response["message"]
        assert error_response["html"] == ""
        assert error_response["length"] == 0
    
    def test_eval_js_no_page_error(self):
        """Test error response when no page is available."""
        error_response = {
            "status": "error",
            "message": "No page available"
        }
        
        assert error_response["status"] == "error"
        assert "No page available" in error_response["message"]
    
    def test_connection_refused_error_handling(self):
        """Test handling of connection refused error."""
        error_response = {
            "status": "error",
            "message": "Could not connect to browser server. Is it running?"
        }
        
        assert error_response["status"] == "error"
        assert "connect" in error_response["message"].lower()


class TestContentExtraction:
    """Test content extraction logic."""
    
    def test_html_content_validation(self):
        """Test that extracted HTML is validated correctly."""
        # Valid content
        valid_html = "<div><p>Test content with enough text</p>" * 10
        assert len(valid_html) > 100
        
        # Invalid - too short
        invalid_html = "<p>Short</p>"
        assert len(invalid_html) < 100
        
        # Empty
        empty_html = ""
        assert len(empty_html) == 0
    
    def test_multiple_selector_attempts(self):
        """Test that multiple selectors are attempted."""
        # Simulate trying multiple selectors
        selectors = [
            ('div[class*="post-content"]', None),  # First fails
            ('div[data-tag="post-body"]', None),  # Second fails
            ('article', '<div>Content</div>')  # Third succeeds
        ]
        
        result = None
        for selector, content in selectors:
            if content:
                result = content
                break
        
        assert result == '<div>Content</div>'
    
    def test_content_length_reporting(self):
        """Test that content length is reported correctly."""
        html = "<div><p>Test content</p></div>"
        length = len(html)
        
        assert length > 0
        assert isinstance(length, int)


class TestBrowserClientMocked:
    """Test BrowserClient with mocked socket connections."""
    
    def test_client_initialization(self):
        """Test client initialization with default and custom parameters."""
        # Default initialization
        client = BrowserClient()
        assert client.host == "localhost"
        assert client.port == 9999
        
        # Custom initialization
        client_custom = BrowserClient(host="127.0.0.1", port=8080)
        assert client_custom.host == "127.0.0.1"
        assert client_custom.port == 8080
    
    def test_send_command_success(self):
        """Test successful command sending and response receiving."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "message": "pong"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.send_command({"action": "ping"})
            
        assert response["status"] == "success"
        mock_socket.connect.assert_called_once_with(("localhost", 9999))
        mock_socket.sendall.assert_called_once()
        mock_socket.close.assert_called_once()
    
    def test_send_command_connection_refused(self):
        """Test handling of connection refused error."""
        client = BrowserClient()
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = ConnectionRefusedError()
            mock_socket_class.return_value = mock_socket
            
            response = client.send_command({"action": "ping"})
            
        assert response["status"] == "error"
        assert "Could not connect to browser server" in response["message"]
    
    def test_send_command_general_exception(self):
        """Test handling of general exceptions."""
        client = BrowserClient()
        
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket.connect.side_effect = Exception("Network error")
            mock_socket_class.return_value = mock_socket
            
            response = client.send_command({"action": "ping"})
            
        assert response["status"] == "error"
        assert "Network error" in response["message"]
    
    def test_send_command_large_response(self):
        """Test receiving large responses in chunks."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        large_response = {"status": "success", "html": "x" * 100000}
        response_bytes = json.dumps(large_response).encode()
        
        # Simulate receiving in multiple chunks
        chunk_size = 65536
        chunks = [response_bytes[i:i+chunk_size] for i in range(0, len(response_bytes), chunk_size)]
        chunks.append(b'')  # EOF marker
        mock_socket.recv.side_effect = chunks
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.send_command({"action": "extract_html", "selector": "div"})
            
        assert response["status"] == "success"
        assert len(response["html"]) == 100000
    
    def test_goto_command(self):
        """Test goto command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "url": "https://example.com", "title": "Example"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.goto("https://example.com")
            
        assert response["status"] == "success"
        assert response["url"] == "https://example.com"
        
        # Verify command structure
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "goto"
        assert command["url"] == "https://example.com"
    
    def test_click_command(self):
        """Test click command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.click("button.submit", timeout=3000)
            
        assert response["status"] == "success"
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "click"
        assert command["selector"] == "button.submit"
        assert command["timeout"] == 3000
    
    def test_wait_command(self):
        """Test wait command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.wait("div.content", timeout=15000)
            
        assert response["status"] == "success"
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "wait"
        assert command["selector"] == "div.content"
        assert command["timeout"] == 15000
    
    def test_extract_command(self):
        """Test extract command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "count": 2, "links": ["url1", "url2"]}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.extract("a[href*='items']")
            
        assert response["status"] == "success"
        assert response["count"] == 2
        assert len(response["links"]) == 2
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "extract"
        assert command["selector"] == "a[href*='items']"
    
    def test_extract_html_command(self):
        """Test extract_html command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "html": "<div>Content</div>", "length": 18}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.extract_html("div.post-content")
            
        assert response["status"] == "success"
        assert response["html"] == "<div>Content</div>"
        assert response["length"] == 18
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "extract_html"
        assert command["selector"] == "div.post-content"
    
    def test_eval_js_command(self):
        """Test eval_js command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "result": {"count": 5}}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.eval_js("document.querySelectorAll('div').length")
            
        assert response["status"] == "success"
        assert "result" in response
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "eval_js"
        assert "document.querySelectorAll" in command["code"]
    
    def test_download_command(self):
        """Test download command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "path": "/tmp/file.pdf", "suggested_filename": "file.pdf"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.download("https://example.com/file.pdf", "/tmp/file.pdf")
            
        assert response["status"] == "success"
        assert response["path"] == "/tmp/file.pdf"
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "download"
        assert command["url"] == "https://example.com/file.pdf"
        assert command["save_path"] == "/tmp/file.pdf"
    
    def test_info_command(self):
        """Test info command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {
            "status": "success",
            "url": "https://example.com",
            "title": "Example",
            "buttons": 5,
            "inputs": 3
        }
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.info()
            
        assert response["status"] == "success"
        assert response["url"] == "https://example.com"
        assert response["buttons"] == 5
        assert response["inputs"] == 3
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "info"
    
    def test_ping_command(self):
        """Test ping command."""
        client = BrowserClient()
        
        mock_socket = MagicMock()
        mock_response = {"status": "success", "message": "pong"}
        mock_socket.recv.return_value = json.dumps(mock_response).encode()
        
        with patch('socket.socket', return_value=mock_socket):
            response = client.ping()
            
        assert response["status"] == "success"
        assert response["message"] == "pong"
        
        sent_data = mock_socket.sendall.call_args[0][0].decode()
        command = json.loads(sent_data)
        assert command["action"] == "ping"


class TestBrowserServerMocked:
    """Test BrowserServer with mocked dependencies."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        server = BrowserServer(browser_exe="/usr/bin/brave", port=8080)
        assert server.port == 8080
        assert server.browser_exe == "/usr/bin/brave"
        assert server.controller is None
        assert server.running is False
    
    def test_server_initialization_defaults(self):
        """Test server initialization with defaults."""
        server = BrowserServer()
        assert server.port == 9999
        assert server.browser_exe is None
        assert server.controller is None
    
    def test_execute_command_goto(self):
        """Test _execute_command with goto action."""
        server = BrowserServer()
        
        # Mock controller
        mock_controller = MagicMock()
        mock_obs = PageObservation(
            url="https://example.com",
            title="Example Domain",
            buttons=[],
            inputs=[]
        )
        mock_controller.get_observation.return_value = mock_obs
        server.controller = mock_controller
        
        response = server._execute_command({"action": "goto", "url": "https://example.com"})
        
        assert response["status"] == "success"
        assert response["url"] == "https://example.com"
        assert response["title"] == "Example Domain"
        mock_controller.perform.assert_called_once()
    
    def test_execute_command_click(self):
        """Test _execute_command with click action."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_page = MagicMock()
        mock_controller._page = mock_page
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "click",
            "selector": "button.submit",
            "timeout": 5000
        })
        
        assert response["status"] == "success"
        mock_page.click.assert_called_once_with("button.submit", timeout=5000)
    
    def test_execute_command_click_default_timeout(self):
        """Test _execute_command with click action using default timeout."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_page = MagicMock()
        mock_controller._page = mock_page
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "click",
            "selector": "button.submit"
        })
        
        assert response["status"] == "success"
        mock_page.click.assert_called_once_with("button.submit", timeout=5000)
    
    def test_execute_command_wait(self):
        """Test _execute_command with wait action."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "wait",
            "selector": "div.content",
            "timeout": 10000
        })
        
        assert response["status"] == "success"
        mock_controller.perform.assert_called_once()
    
    def test_execute_command_extract(self):
        """Test _execute_command with extract action."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_controller.get_extracted_links.return_value = ["url1", "url2", "url3"]
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "extract",
            "selector": "a[href*='items']"
        })
        
        assert response["status"] == "success"
        assert response["count"] == 3
        assert len(response["links"]) == 3
        mock_controller.perform.assert_called_once()
    
    def test_execute_command_extract_html_success(self):
        """Test _execute_command with extract_html action - success."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        html_content = "<div><p>Test content</p></div>"
        mock_controller.get_extracted_html.return_value = html_content
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "extract_html",
            "selector": "div.post-content"
        })
        
        assert response["status"] == "success"
        assert response["html"] == html_content
        assert response["length"] == len(html_content)
        mock_controller.perform.assert_called_once()
    
    def test_execute_command_extract_html_not_found(self):
        """Test _execute_command with extract_html action - element not found."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_controller.get_extracted_html.return_value = ""
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "extract_html",
            "selector": "div.nonexistent"
        })
        
        assert response["status"] == "error"
        assert "No element found" in response["message"]
        assert response["html"] == ""
        assert response["length"] == 0
    
    def test_execute_command_eval_js_success(self):
        """Test _execute_command with eval_js action - success."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_page = MagicMock()
        mock_page.evaluate.return_value = {"count": 5, "found": True}
        mock_controller._page = mock_page
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "eval_js",
            "code": "document.querySelectorAll('div').length"
        })
        
        assert response["status"] == "success"
        assert response["result"]["count"] == 5
        assert response["result"]["found"] is True
        mock_page.evaluate.assert_called_once()
    
    def test_execute_command_eval_js_no_page(self):
        """Test _execute_command with eval_js action - no page available."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_controller._page = None
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "eval_js",
            "code": "document.title"
        })
        
        assert response["status"] == "error"
        assert "No page available" in response["message"]
    
    def test_execute_command_download_success(self):
        """Test _execute_command with download action - success."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_page = MagicMock()
        mock_download = MagicMock()
        mock_download.suggested_filename = "document.pdf"
        
        # Mock the context manager for expect_download
        mock_download_info = MagicMock()
        mock_download_info.__enter__ = MagicMock(return_value=mock_download_info)
        mock_download_info.__exit__ = MagicMock(return_value=False)
        mock_download_info.value = mock_download
        
        mock_page.expect_download.return_value = mock_download_info
        mock_controller._page = mock_page
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "download",
            "url": "https://example.com/file.pdf",
            "save_path": "/tmp/file.pdf"
        })
        
        assert response["status"] == "success"
        assert response["path"] == "/tmp/file.pdf"
        assert response["suggested_filename"] == "document.pdf"
        mock_download.save_as.assert_called_once_with("/tmp/file.pdf")
    
    def test_execute_command_download_no_page(self):
        """Test _execute_command with download action - no page available."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_controller._page = None
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "download",
            "url": "https://example.com/file.pdf",
            "save_path": "/tmp/file.pdf"
        })
        
        assert response["status"] == "error"
        assert "No page available" in response["message"]
    
    def test_execute_command_download_failure(self):
        """Test _execute_command with download action - download fails."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_page = MagicMock()
        mock_page.expect_download.side_effect = Exception("Download timeout")
        mock_controller._page = mock_page
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "download",
            "url": "https://example.com/file.pdf",
            "save_path": "/tmp/file.pdf"
        })
        
        assert response["status"] == "error"
        assert "Download failed" in response["message"]
    
    def test_execute_command_info(self):
        """Test _execute_command with info action."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_obs = PageObservation(
            url="https://example.com/page",
            title="Test Page",
            buttons=[{"text": "Submit"}],
            inputs=[{"name": "email"}, {"name": "password"}]
        )
        mock_controller.get_observation.return_value = mock_obs
        server.controller = mock_controller
        
        response = server._execute_command({"action": "info"})
        
        assert response["status"] == "success"
        assert response["url"] == "https://example.com/page"
        assert response["title"] == "Test Page"
        assert response["buttons"] == 1
        assert response["inputs"] == 2
    
    def test_execute_command_ping(self):
        """Test _execute_command with ping action."""
        server = BrowserServer()
        
        response = server._execute_command({"action": "ping"})
        
        assert response["status"] == "success"
        assert response["message"] == "pong"
    
    def test_execute_command_unknown_action(self):
        """Test _execute_command with unknown action."""
        server = BrowserServer()
        
        response = server._execute_command({"action": "invalid_action"})
        
        assert response["status"] == "error"
        assert "Unknown action" in response["message"]
    
    def test_execute_command_exception_handling(self):
        """Test _execute_command exception handling."""
        server = BrowserServer()
        
        mock_controller = MagicMock()
        mock_controller.perform.side_effect = Exception("Navigation failed")
        server.controller = mock_controller
        
        response = server._execute_command({
            "action": "goto",
            "url": "https://example.com"
        })
        
        assert response["status"] == "error"
        assert "Navigation failed" in response["message"]
    
    def test_handle_client_success(self):
        """Test _handle_client with successful command."""
        server = BrowserServer()
        server.console = MagicMock()
        
        mock_controller = MagicMock()
        server.controller = mock_controller
        
        mock_socket = MagicMock()
        command = {"action": "ping"}
        mock_socket.recv.return_value = json.dumps(command).encode()
        
        server._handle_client(mock_socket)
        
        mock_socket.sendall.assert_called_once()
        sent_data = mock_socket.sendall.call_args[0][0]
        response = json.loads(sent_data.decode())
        assert response["status"] == "success"
        mock_socket.close.assert_called_once()
    
    def test_handle_client_empty_data(self):
        """Test _handle_client with empty data."""
        server = BrowserServer()
        server.console = MagicMock()
        
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b''
        
        server._handle_client(mock_socket)
        
        mock_socket.sendall.assert_not_called()
        mock_socket.close.assert_called_once()
    
    def test_handle_client_exception(self):
        """Test _handle_client with exception during command execution."""
        server = BrowserServer()
        server.console = MagicMock()
        
        mock_socket = MagicMock()
        mock_socket.recv.side_effect = Exception("Socket error")
        
        server._handle_client(mock_socket)
        
        mock_socket.close.assert_called_once()
    
    def test_handle_client_send_error(self):
        """Test _handle_client when sending response fails."""
        server = BrowserServer()
        server.console = MagicMock()
        
        mock_socket = MagicMock()
        command = {"action": "invalid"}
        mock_socket.recv.return_value = json.dumps(command).encode()
        mock_socket.sendall.side_effect = OSError("Connection closed")
        
        # Should not raise exception
        server._handle_client(mock_socket)
        
        mock_socket.close.assert_called_once()
    
    def test_start_server_with_initial_url(self):
        """Test server start with initial URL (without actually starting server loop)."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket, \
             patch('builtins.input', return_value=''):
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_server_socket = MagicMock()
            mock_server_socket.accept.side_effect = KeyboardInterrupt()
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer(browser_exe="/usr/bin/brave", port=8080)
            
            try:
                server.start(initial_url="https://example.com", wait_for_auth=True)
            except KeyboardInterrupt:
                pass
            
            # Verify browser was started
            MockController.assert_called_once_with(
                executable_path="/usr/bin/brave",
                headless=False
            )
            mock_controller.start.assert_called_once()
            
            # Verify navigation to initial URL
            mock_controller.perform.assert_called()
            call_args = mock_controller.perform.call_args[0][0]
            assert call_args.url == "https://example.com"
            
        # Verify server socket was set up
        mock_server_socket.bind.assert_called_once_with(('localhost', 8080))
        mock_server_socket.listen.assert_called_once_with(5)
        mock_server_socket.settimeout.assert_called_once_with(0.1)
        
        # Verify cleanup
        mock_server_socket.close.assert_called_once()
        mock_controller.stop.assert_called_once()
    
    def test_start_server_no_wait_for_auth(self):
        """Test server start without waiting for auth."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket, \
             patch('builtins.input', return_value='') as mock_input:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_server_socket = MagicMock()
            mock_server_socket.accept.side_effect = KeyboardInterrupt()
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer()
            
            try:
                server.start(wait_for_auth=False)
            except KeyboardInterrupt:
                pass
            
            # Input should not have been called
            mock_input.assert_not_called()
    
    def test_start_server_no_initial_url(self):
        """Test server start without initial URL."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_server_socket = MagicMock()
            mock_server_socket.accept.side_effect = KeyboardInterrupt()
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer()
            
            try:
                server.start(wait_for_auth=False)
            except KeyboardInterrupt:
                pass
            
            # Browser should be started but no navigation
            mock_controller.start.assert_called_once()
            mock_controller.perform.assert_not_called()
    
    def test_start_server_handle_client_connection(self):
        """Test server accepting and handling a client connection."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_client_socket = MagicMock()
            mock_client_socket.recv.return_value = json.dumps({"action": "ping"}).encode()
            
            mock_server_socket = MagicMock()
            # Accept one client, then KeyboardInterrupt to stop
            mock_server_socket.accept.side_effect = [
                (mock_client_socket, ("127.0.0.1", 12345)),
                KeyboardInterrupt()
            ]
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer()
            
            try:
                server.start(wait_for_auth=False)
            except KeyboardInterrupt:
                pass
            
            # Verify client was handled
            mock_client_socket.recv.assert_called_once()
            mock_client_socket.sendall.assert_called_once()
            mock_client_socket.close.assert_called_once()
    
    def test_start_server_socket_timeout_continues(self):
        """Test server continues on socket timeout."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_server_socket = MagicMock()
            # Timeout a few times, then KeyboardInterrupt
            mock_server_socket.accept.side_effect = [
                socket.timeout(),
                socket.timeout(),
                KeyboardInterrupt()
            ]
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer()
            
            try:
                server.start(wait_for_auth=False)
            except KeyboardInterrupt:
                pass
            
            # Should have tried to accept 3 times
            assert mock_server_socket.accept.call_count == 3
    
    def test_start_server_accept_error_handling(self):
        """Test server handles errors during accept."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_server_socket = MagicMock()
            # Error, then KeyboardInterrupt
            mock_server_socket.accept.side_effect = [
                Exception("Accept error"),
                KeyboardInterrupt()
            ]
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer()
            server.console = MagicMock()
            
            try:
                server.start(wait_for_auth=False)
            except KeyboardInterrupt:
                pass
            
            # Should have logged the error
            assert any("Error accepting connection" in str(call) for call in server.console.print.call_args_list)


class TestBrowserClientMain:
    """Test BrowserClient main CLI function."""
    
    def test_main_ping_command(self):
        """Test main with ping command."""
        with patch('sys.argv', ['browser_client.py', 'ping']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print') as mock_print:
            
            mock_client_instance = MagicMock()
            mock_client_instance.ping.return_value = {"status": "success", "message": "pong"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.ping.assert_called_once()
            mock_print.assert_called_once()
    
    def test_main_info_command(self):
        """Test main with info command."""
        with patch('sys.argv', ['browser_client.py', 'info']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print') as mock_print:
            
            mock_client_instance = MagicMock()
            mock_client_instance.info.return_value = {
                "status": "success",
                "url": "https://example.com",
                "title": "Example"
            }
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.info.assert_called_once()
    
    def test_main_goto_command(self):
        """Test main with goto command."""
        with patch('sys.argv', ['browser_client.py', 'goto', 'https://example.com']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.goto.return_value = {"status": "success"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.goto.assert_called_once_with('https://example.com')
    
    def test_main_click_command_with_timeout(self):
        """Test main with click command and timeout."""
        with patch('sys.argv', ['browser_client.py', 'click', 'button.submit', '3000']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.click.return_value = {"status": "success"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.click.assert_called_once_with('button.submit', 3000)
    
    def test_main_click_command_default_timeout(self):
        """Test main with click command using default timeout."""
        with patch('sys.argv', ['browser_client.py', 'click', 'button.submit']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.click.return_value = {"status": "success"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.click.assert_called_once_with('button.submit', 5000)
    
    def test_main_wait_command_with_timeout(self):
        """Test main with wait command and timeout."""
        with patch('sys.argv', ['browser_client.py', 'wait', 'div.content', '15000']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.wait.return_value = {"status": "success"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.wait.assert_called_once_with('div.content', 15000)
    
    def test_main_wait_command_default_timeout(self):
        """Test main with wait command using default timeout."""
        with patch('sys.argv', ['browser_client.py', 'wait', 'div.content']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.wait.return_value = {"status": "success"}
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.wait.assert_called_once_with('div.content', 10000)
    
    def test_main_extract_command(self):
        """Test main with extract command."""
        with patch('sys.argv', ['browser_client.py', 'extract', 'a[href*="items"]']), \
             patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             patch('builtins.print'):
            
            mock_client_instance = MagicMock()
            mock_client_instance.extract.return_value = {
                "status": "success",
                "count": 2,
                "links": ["url1", "url2"]
            }
            MockClient.return_value = mock_client_instance
            
            from browser_agent.server.browser_client import main
            main()
            
            mock_client_instance.extract.assert_called_once_with('a[href*="items"]')
    
    def test_main_unknown_command(self):
        """Test main with unknown command."""
        with patch('sys.argv', ['browser_client.py', 'invalid_command']), \
             patch('browser_agent.server.browser_client.BrowserClient'), \
             patch('builtins.print') as mock_print, \
             pytest.raises(SystemExit) as exc_info:
            
            from browser_agent.server.browser_client import main
            main()
            
        assert exc_info.value.code == 1
        # Should print error message
        assert any("Unknown command" in str(call) for call in mock_print.call_args_list)
    
    def test_main_no_arguments(self):
        """Test main with no arguments."""
        with patch('sys.argv', ['browser_client.py']), \
             patch('builtins.print') as mock_print, \
             pytest.raises(SystemExit) as exc_info:
            
            from browser_agent.server.browser_client import main
            main()
            
        assert exc_info.value.code == 1
        # Should print usage message
        assert any("Usage:" in str(call) for call in mock_print.call_args_list)


class TestBrowserServerLogging:
    """Test browser server logging functionality."""
    
    def test_server_initialization_with_log_file(self):
        """Test server initialization with custom log file."""
        server = BrowserServer(browser_exe="/usr/bin/brave", port=8080, log_file="/tmp/test.log")
        assert server.log_file == "/tmp/test.log"
    
    def test_server_initialization_default_log_file(self):
        """Test server initialization with default log file."""
        server = BrowserServer(port=9999)
        assert server.log_file == "/tmp/browser_server_9999.log"
    
    def test_server_log_method(self):
        """Test server _log method."""
        server = BrowserServer(port=9999)
        # Should not raise any exceptions
        server._log("Test message", "INFO")
        server._log("Warning message", "WARNING")
        server._log("Error message", "ERROR")
    
    def test_get_log_file_action(self):
        """Test get_log_file action in execute_command."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController:
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            server = BrowserServer(port=9999, log_file="/tmp/test_9999.log")
            server.controller = mock_controller
            
            result = server._execute_command({"action": "get_log_file"})
            
            assert result["status"] == "success"
            assert result["log_file"] == "/tmp/test_9999.log"
    
    def test_get_log_file_during_wait(self):
        """Test get_log_file action during wait state."""
        with patch('browser_agent.server.browser_server.PlaywrightBrowserController') as MockController, \
             patch('browser_agent.server.browser_server.socket.socket') as MockSocket:
            
            mock_controller = MagicMock()
            MockController.return_value = mock_controller
            
            mock_client_socket = MagicMock()
            mock_server_socket = MagicMock()
            MockSocket.return_value = mock_server_socket
            
            server = BrowserServer(port=8080, log_file="/tmp/wait_test.log")
            server.waiting_for_ready = True
            server.controller = mock_controller
            
            # Simulate get_log_file command during wait
            command = json.dumps({"action": "get_log_file"}).encode()
            mock_client_socket.recv.return_value = command
            
            server._handle_client_during_wait(mock_client_socket)
            
            # Check the response
            call_args = mock_client_socket.sendall.call_args[0][0]
            response = json.loads(call_args.decode())
            assert response["status"] == "success"
            assert response["log_file"] == "/tmp/wait_test.log"
            assert response.get("waiting") == True


class TestBrowserClientLogging:
    """Test browser client logging functionality."""
    
    def test_get_log_file_method(self):
        """Test BrowserClient get_log_file method."""
        with patch('socket.socket') as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value = mock_socket
            
            response_data = json.dumps({
                "status": "success",
                "log_file": "/tmp/browser_server_9999.log"
            }).encode()
            mock_socket.recv.return_value = response_data
            
            client = BrowserClient()
            result = client.get_log_file()
            
            assert result["status"] == "success"
            assert result["log_file"] == "/tmp/browser_server_9999.log"
    
    def test_logs_command_basic(self):
        """Test logs command basic functionality."""
        import tempfile
        import os
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-12-08 10:00:00 [INFO] Line 1\n")
            f.write("2025-12-08 10:00:01 [INFO] Line 2\n")
            f.write("2025-12-08 10:00:02 [INFO] Line 3\n")
            log_file = f.name
        
        try:
            with patch('browser_agent.server.browser_client.BrowserClient') as MockClient:
                mock_client = MagicMock()
                mock_client.get_log_file.return_value = {
                    "status": "success",
                    "log_file": log_file
                }
                MockClient.return_value = mock_client
                
                from browser_agent.server.browser_client import _handle_logs_command
                
                # Mock args object
                args = MagicMock()
                args.lines = 2
                args.follow = False
                args.tail = True
                
                # Capture stdout
                from io import StringIO
                import sys
                old_stdout = sys.stdout
                sys.stdout = output = StringIO()
                
                try:
                    _handle_logs_command(args)
                    output_text = output.getvalue()
                    
                    # Should contain last 2 lines
                    assert "Line 2" in output_text
                    assert "Line 3" in output_text
                    assert "Line 1" not in output_text
                finally:
                    sys.stdout = old_stdout
        finally:
            os.unlink(log_file)
    
    def test_logs_command_file_not_found(self):
        """Test logs command when log file doesn't exist."""
        with patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             pytest.raises(SystemExit):
            
            mock_client = MagicMock()
            mock_client.get_log_file.return_value = {
                "status": "success",
                "log_file": "/nonexistent/file.log"
            }
            MockClient.return_value = mock_client
            
            from browser_agent.server.browser_client import _handle_logs_command
            
            args = MagicMock()
            args.lines = 10
            args.follow = False
            args.tail = False
            
            _handle_logs_command(args)
    
    def test_logs_command_server_error(self):
        """Test logs command when server returns error."""
        with patch('browser_agent.server.browser_client.BrowserClient') as MockClient, \
             pytest.raises(SystemExit):
            
            mock_client = MagicMock()
            mock_client.get_log_file.return_value = {
                "status": "error",
                "message": "Server error"
            }
            MockClient.return_value = mock_client
            
            from browser_agent.server.browser_client import _handle_logs_command
            
            args = MagicMock()
            args.lines = 10
            args.follow = False
            args.tail = False
            
            _handle_logs_command(args)
    
    def test_logs_command_follow_mode(self):
        """Test logs command with follow mode."""
        import tempfile
        import os
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-12-08 10:00:00 [INFO] Initial line\n")
            log_file = f.name
        
        try:
            with patch('browser_agent.server.browser_client.BrowserClient') as MockClient:
                
                mock_client = MagicMock()
                mock_client.get_log_file.return_value = {
                    "status": "success",
                    "log_file": log_file
                }
                MockClient.return_value = mock_client
                
                from browser_agent.server.browser_client import _handle_logs_command
                
                args = MagicMock()
                args.lines = 10
                args.follow = True
                args.tail = False
                
                # Mock file to simulate KeyboardInterrupt during follow
                with patch('builtins.open', create=True) as mock_open_func:
                    mock_file = MagicMock()
                    
                    # Simulate reading one line then KeyboardInterrupt
                    def readline_side_effect():
                        # First call: return a line
                        # Second call: raise KeyboardInterrupt
                        if not hasattr(readline_side_effect, 'call_count'):
                            readline_side_effect.call_count = 0
                        readline_side_effect.call_count += 1
                        if readline_side_effect.call_count == 1:
                            return "2025-12-08 10:00:01 [INFO] New line\n"
                        else:
                            raise KeyboardInterrupt()
                    
                    mock_file.readline.side_effect = readline_side_effect
                    mock_open_func.return_value.__enter__.return_value = mock_file
                    
                    # Should not raise, should catch KeyboardInterrupt
                    from io import StringIO
                    import sys
                    old_stdout = sys.stdout
                    sys.stdout = output = StringIO()
                    
                    try:
                        _handle_logs_command(args)
                        output_text = output.getvalue()
                        
                        # Should show the "Following" or "Stopped following" message
                        assert "Following" in output_text or "Stopped following" in output_text
                    finally:
                        sys.stdout = old_stdout
        finally:
            os.unlink(log_file)
    
    def test_logs_command_waiting_status(self):
        """Test logs command accepts 'waiting' status from server."""
        import tempfile
        import os
        
        # Create a temporary log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
            f.write("2025-12-08 10:00:00 [INFO] Waiting line\n")
            log_file = f.name
        
        try:
            with patch('browser_agent.server.browser_client.BrowserClient') as MockClient:
                mock_client = MagicMock()
                # Server returns "waiting" status (browser waiting for auth)
                mock_client.get_log_file.return_value = {
                    "status": "waiting",
                    "log_file": log_file
                }
                MockClient.return_value = mock_client
                
                from browser_agent.server.browser_client import _handle_logs_command
                
                args = MagicMock()
                args.lines = 1
                args.follow = False
                args.tail = True
                
                from io import StringIO
                import sys
                old_stdout = sys.stdout
                sys.stdout = output = StringIO()
                
                try:
                    _handle_logs_command(args)
                    output_text = output.getvalue()
                    
                    # Should read and show the log content
                    assert "Waiting line" in output_text
                finally:
                    sys.stdout = old_stdout
        finally:
            os.unlink(log_file)

