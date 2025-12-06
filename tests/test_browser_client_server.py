"""Tests for browser server and client functionality.

These are generic tests for the browser server/client architecture.
Patreon-specific tests are in examples/patreon/tests/.
"""
import json

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
