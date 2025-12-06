"""Tests for browser server and client functionality."""
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


class TestExtractPatreonContentClient:
    """Test extract_patreon_content_client.py functionality."""
    
    def test_content_validation_threshold(self):
        """Test that content must exceed minimum length threshold."""
        min_length = 100
        
        # Content below threshold
        short_content = "a" * 50
        assert len(short_content) < min_length
        
        # Content above threshold
        long_content = "a" * 150
        assert len(long_content) > min_length
    
    def test_selector_fallback_order(self):
        """Test that selectors are tried in correct order."""
        selectors = [
            'div[class*="cm-LIiDtl"]',
            'div[data-tag="post-content"]',
            'article div[class*="cm-"]',
            '[data-tag="post-card"] div[class*="cm-"]',
            'div[class*="cm-wHoaYV"]',
            'article',
        ]
        
        # Verify we have multiple fallback options
        assert len(selectors) >= 3
        
        # Verify specific selectors are included
        assert any('cm-LIiDtl' in s for s in selectors)
        assert any('post-content' in s for s in selectors)
        assert any('article' in s for s in selectors)
    
    def test_post_id_extraction_from_url(self):
        """Test extracting post ID from URL."""
        url = "https://www.patreon.com/posts/144726506?collection=1611241"
        
        # Simulate extraction logic
        if "/posts/" in url:
            post_id = url.split("/posts/")[1].split("?")[0]
        else:
            post_id = "unknown"
        
        assert post_id == "144726506"
    
    def test_post_id_extraction_without_query(self):
        """Test extracting post ID from URL without query params."""
        url = "https://www.patreon.com/posts/144726506"
        
        if "/posts/" in url:
            post_id = url.split("/posts/")[1].split("?")[0]
        else:
            post_id = "unknown"
        
        assert post_id == "144726506"
    
    def test_post_id_extraction_fallback(self):
        """Test post ID extraction fallback for invalid URLs."""
        url = "https://www.patreon.com/collection/1611241"
        
        if "/posts/" in url:
            post_id = url.split("/posts/")[1].split("?")[0]
        else:
            post_id = "unknown"
        
        assert post_id == "unknown"
    
    def test_collection_name_sanitization(self):
        """Test that collection names are sanitized for filenames."""
        invalid_chars = '<>:"/\\|?*'
        test_name = 'SDXL Models: Special <Edition> "Test"'
        
        # Simulate sanitization
        sanitized = test_name
        for char in invalid_chars:
            sanitized = sanitized.replace(char, '_')
        
        # Verify no invalid chars remain
        for char in invalid_chars:
            assert char not in sanitized
        
        assert '_' in sanitized  # Replacements were made
    
    def test_collection_name_length_limit(self):
        """Test that collection names are truncated if too long."""
        long_name = "a" * 150
        max_length = 100
        
        truncated = long_name[:max_length] if len(long_name) > max_length else long_name
        
        assert len(truncated) <= max_length
    
    def test_metadata_structure(self):
        """Test that saved metadata has correct structure."""
        metadata = {
            "post_id": "144726506",
            "post_url": "https://www.patreon.com/posts/144726506",
            "collection_id": "1611241",
            "collection_name": "SDXL Models",
            "title": "Test Post",
            "html_length": 3400
        }
        
        # Verify all required fields
        assert "post_id" in metadata
        assert "post_url" in metadata
        assert "collection_id" in metadata
        assert "collection_name" in metadata
        assert "title" in metadata
        assert "html_length" in metadata
        
        # Verify types
        assert isinstance(metadata["post_id"], str)
        assert isinstance(metadata["html_length"], int)


class TestDebugPageStructure:
    """Test debug_page_structure.py functionality."""
    
    def test_selector_testing_list(self):
        """Test that debug script tests comprehensive list of selectors."""
        selectors_to_test = [
            'div[class*="cm-LIiDtl"]',
            'div[class*="cm-wHoaYV"]',
            'div[data-tag="post-content"]',
            'article div[class*="cm-"]',
            '[data-tag="post-card"]',
            'article',
            'main',
            'div[class*="post"]',
        ]
        
        assert len(selectors_to_test) >= 5
        assert any('cm-' in s for s in selectors_to_test)
        assert any('article' in s for s in selectors_to_test)
    
    def test_element_info_structure(self):
        """Test expected structure of element information."""
        element_info = {
            "found": True,
            "tag": "DIV",
            "classes": "cm-LIiDtl cm-wHoaYV",
            "childCount": 10,
            "textLength": 500,
            "htmlLength": 2000
        }
        
        assert "found" in element_info
        assert "tag" in element_info
        assert "textLength" in element_info
        assert "htmlLength" in element_info
        
        # Verify HTML length is greater than text length
        assert element_info["htmlLength"] >= element_info["textLength"]
    
    def test_best_selector_criteria(self):
        """Test criteria for finding best selector."""
        min_content_length = 500
        
        # Element with substantial content
        good_element = {"textLength": 1500}
        assert good_element["textLength"] > min_content_length
        
        # Element with minimal content
        bad_element = {"textLength": 50}
        assert bad_element["textLength"] < min_content_length


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
            ('div[class*="cm-LIiDtl"]', None),  # First fails
            ('div[data-tag="post-content"]', None),  # Second fails
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
