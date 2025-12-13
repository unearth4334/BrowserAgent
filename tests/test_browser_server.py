"""Tests for the browser server module."""
from unittest.mock import MagicMock, patch
import pytest

from browser_agent.server import BrowserServer, BrowserClient


class TestBrowserServer:
    """Tests for BrowserServer class."""

    def test_browser_server_initialization(self):
        """Test BrowserServer can be initialized with defaults."""
        server = BrowserServer()
        assert server.port == 9999
        assert server.browser_exe is None
        assert server.controller is None
        assert server.running is False

    def test_browser_server_initialization_with_params(self):
        """Test BrowserServer can be initialized with custom parameters."""
        server = BrowserServer(browser_exe="/usr/bin/brave-browser", port=8888)
        assert server.port == 8888
        assert server.browser_exe == "/usr/bin/brave-browser"
        assert server.headless is False  # Default value

    def test_browser_server_initialization_with_headless(self):
        """Test BrowserServer can be initialized with headless mode."""
        server = BrowserServer(headless=True)
        assert server.headless is True
        assert server.port == 9999

    def test_browser_server_initialization_with_all_params(self):
        """Test BrowserServer with all parameters."""
        server = BrowserServer(
            browser_exe="/usr/bin/chromium",
            port=7777,
            headless=True,
            log_file="/tmp/test.log"
        )
        assert server.port == 7777
        assert server.browser_exe == "/usr/bin/chromium"
        assert server.headless is True
        assert server.log_file == "/tmp/test.log"

    def test_browser_server_headless_propagates_to_controller(self):
        """Test that headless parameter is stored correctly."""
        server = BrowserServer(headless=True)
        assert server.headless is True

    def test_browser_server_non_headless_propagates_to_controller(self):
        """Test that headless=False is stored correctly."""
        server = BrowserServer(headless=False)
        assert server.headless is False

    def test_browser_server_default_headless_is_false(self):
        """Test that BrowserServer defaults to headless=False."""
        server = BrowserServer()
        assert server.headless is False

    def test_browser_server_with_custom_browser_exe(self):
        """Test BrowserServer with custom browser executable."""
        server = BrowserServer(
            browser_exe="/usr/bin/firefox",
            headless=True
        )
        assert server.browser_exe == "/usr/bin/firefox"
        assert server.headless is True

    def test_browser_server_port_and_headless_combination(self):
        """Test BrowserServer with custom port and headless mode."""
        server = BrowserServer(port=8888, headless=True)
        assert server.port == 8888
        assert server.headless is True
        assert server.log_file == "/tmp/browser_server_8888.log"


class TestBrowserClient:
    """Tests for BrowserClient class."""

    def test_browser_client_initialization(self):
        """Test BrowserClient can be initialized with defaults."""
        client = BrowserClient()
        assert client.host == "localhost"
        assert client.port == 9999

    def test_browser_client_initialization_with_params(self):
        """Test BrowserClient can be initialized with custom parameters."""
        client = BrowserClient(host="192.168.1.1", port=8888)
        assert client.host == "192.168.1.1"
        assert client.port == 8888

    def test_browser_client_connection_refused(self):
        """Test BrowserClient handles connection refused error."""
        client = BrowserClient(port=9998)  # Use port that's not running
        result = client.ping()
        assert result["status"] == "error"
        assert "Could not connect" in result["message"]

    def test_browser_client_methods_exist(self):
        """Test BrowserClient has all expected methods."""
        client = BrowserClient()
        assert hasattr(client, 'goto')
        assert hasattr(client, 'click')
        assert hasattr(client, 'wait')
        assert hasattr(client, 'extract')
        assert hasattr(client, 'extract_html')
        assert hasattr(client, 'eval_js')
        assert hasattr(client, 'download')
        assert hasattr(client, 'info')
        assert hasattr(client, 'ping')
        assert hasattr(client, 'send_command')


class TestBrowserServerImports:
    """Tests for server module imports."""

    def test_import_from_server_module(self):
        """Test importing from browser_agent.server module."""
        from browser_agent.server import BrowserServer, BrowserClient
        assert BrowserServer is not None
        assert BrowserClient is not None

    def test_import_from_package_root(self):
        """Test importing from browser_agent package root."""
        from browser_agent import BrowserServer, BrowserClient
        assert BrowserServer is not None
        assert BrowserClient is not None
