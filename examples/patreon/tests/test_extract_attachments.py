"""Tests for Patreon attachment extraction and downloading."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# Add examples/patreon to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


# Mock the browser_client module
class MockBrowserClient:
    """Mock browser client for testing."""
    
    def __init__(self):
        self.responses = {}
        self.downloads = {}
    
    def eval_js(self, code: str) -> dict:
        """Mock JavaScript evaluation."""
        return self.responses.get("eval_js", {"status": "success", "result": []})
    
    def download(self, url: str, save_path: str) -> dict:
        """Mock file download."""
        if url in self.downloads:
            return self.downloads[url]
        return {"status": "success", "path": save_path}
    
    def ping(self) -> dict:
        return {"status": "success"}


@pytest.fixture
def mock_client():
    """Create a mock browser client."""
    return MockBrowserClient()


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_attachments():
    """Sample attachment data."""
    return [
        {
            "url": "https://www.patreon.com/file?h=123&m=456",
            "filename": "model_v1.safetensors"
        },
        {
            "url": "https://www.patreon.com/file?h=123&m=789",
            "filename": "images.zip"
        },
        {
            "url": "https://www.patreon.com/file?h=123&m=101",
            "filename": "config.json"
        }
    ]


def test_extract_attachments_success(mock_client, sample_attachments):
    """Test successful attachment extraction."""
    # Import here to use mocked module
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import extract_attachments
    
    # Mock the JavaScript evaluation to return attachments
    mock_client.responses["eval_js"] = {
        "status": "success",
        "result": sample_attachments
    }
    
    result = extract_attachments(mock_client)
    
    assert len(result) == 3
    assert result[0]["filename"] == "model_v1.safetensors"
    assert result[1]["filename"] == "images.zip"
    assert result[2]["filename"] == "config.json"


def test_extract_attachments_empty(mock_client):
    """Test extraction when no attachments are found."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import extract_attachments
    
    mock_client.responses["eval_js"] = {
        "status": "success",
        "result": []
    }
    
    result = extract_attachments(mock_client)
    
    assert result == []


def test_extract_attachments_deduplication(mock_client):
    """Test that duplicate attachments are removed."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import extract_attachments
    
    # Return duplicate attachments (same URL)
    duplicates = [
        {"url": "https://example.com/file1", "filename": "file1.zip"},
        {"url": "https://example.com/file2", "filename": "file2.zip"},
        {"url": "https://example.com/file1", "filename": "file1.zip"},  # Duplicate
        {"url": "https://example.com/file3", "filename": "file3.zip"},
        {"url": "https://example.com/file2", "filename": "file2.zip"},  # Duplicate
    ]
    
    mock_client.responses["eval_js"] = {
        "status": "success",
        "result": duplicates
    }
    
    result = extract_attachments(mock_client)
    
    # Should only have 3 unique attachments
    assert len(result) == 3
    urls = [att["url"] for att in result]
    assert urls == ["https://example.com/file1", "https://example.com/file2", "https://example.com/file3"]


def test_extract_attachments_error(mock_client):
    """Test attachment extraction when JavaScript fails."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import extract_attachments
    
    mock_client.responses["eval_js"] = {
        "status": "error",
        "message": "JavaScript evaluation failed"
    }
    
    result = extract_attachments(mock_client)
    
    assert result == []


def test_download_attachments_success(mock_client, temp_output_dir, sample_attachments):
    """Test successful attachment downloading."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import download_attachments
    
    # Mock successful downloads
    for att in sample_attachments:
        mock_client.downloads[att["url"]] = {"status": "success", "path": "dummy"}
    
    # Create mock files that will "exist" after download
    attachments_dir = temp_output_dir / "attachments"
    call_count = {'count': 0}
    
    def mock_exists(self):
        # Directory should exist, files should exist after first check
        if self.name == "attachments" or call_count['count'] > 0:
            return True
        call_count['count'] += 1
        return False
    
    mock_stat_result = Mock()
    mock_stat_result.st_size = 1024 * 1024  # 1 MB
    
    with patch.object(Path, 'exists', mock_exists):
        with patch.object(Path, 'stat', return_value=mock_stat_result):
            result = download_attachments(mock_client, sample_attachments, temp_output_dir)
    
    assert len(result) == 3


def test_download_attachments_empty(mock_client, temp_output_dir):
    """Test downloading with no attachments."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import download_attachments
    
    result = download_attachments(mock_client, [], temp_output_dir)
    
    assert result == {}


def test_download_attachments_skip_existing(mock_client, temp_output_dir, sample_attachments):
    """Test that existing files are skipped."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import download_attachments
    
    # Create attachments directory with existing file
    attachments_dir = temp_output_dir / "attachments"
    attachments_dir.mkdir()
    existing_file = attachments_dir / "model_v1.safetensors"
    existing_file.write_text("existing data")
    
    result = download_attachments(mock_client, sample_attachments, temp_output_dir)
    
    # First file should be skipped (already exists)
    assert sample_attachments[0]["url"] in result
    assert str(existing_file) == result[sample_attachments[0]["url"]]


def test_download_attachments_partial_failure(mock_client, temp_output_dir, sample_attachments):
    """Test downloading when some downloads fail."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import download_attachments
    
    # First download succeeds, second fails, third succeeds
    mock_client.downloads[sample_attachments[0]["url"]] = {"status": "success"}
    mock_client.downloads[sample_attachments[1]["url"]] = {
        "status": "error",
        "message": "Download failed"
    }
    mock_client.downloads[sample_attachments[2]["url"]] = {"status": "success"}
    
    def mock_exists(self):
        # Directory exists, only successful downloads exist as files
        if self.name == "attachments":
            return True
        filename = self.name
        return filename in ["model_v1.safetensors", "config.json"]
    
    mock_stat_result = Mock()
    mock_stat_result.st_size = 1024 * 1024
    
    with patch.object(Path, 'exists', mock_exists):
        with patch.object(Path, 'stat', return_value=mock_stat_result):
            result = download_attachments(mock_client, sample_attachments, temp_output_dir)
    
    # Should have 2 successful downloads
    assert len(result) == 2
    assert sample_attachments[0]["url"] in result
    assert sample_attachments[1]["url"] not in result  # Failed
    assert sample_attachments[2]["url"] in result


def test_sanitize_filename():
    """Test filename sanitization."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import sanitize_filename
    
    # Test invalid characters
    assert sanitize_filename("file<name>.zip") == "file_name_.zip"
    assert sanitize_filename("path/to/file.txt") == "path_to_file.txt"
    assert sanitize_filename("file:name|test.dat") == "file_name_test.dat"
    
    # Test long filenames
    long_name = "a" * 150 + ".txt"
    result = sanitize_filename(long_name)
    assert len(result) <= 100
    
    # Test whitespace
    assert sanitize_filename("  spaces  .txt") == "spaces  .txt"


def test_save_post_content_with_attachments(temp_output_dir, sample_attachments):
    """Test saving post content including attachments."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import save_post_content
    
    post_id = "12345"
    post_name = "Test Post"
    post_url = "https://www.patreon.com/posts/12345"
    collection_id = "999"
    content = {
        "html": "<div>Test content</div>",
        "title": "Test Post | Patreon",
        "url": post_url
    }
    
    # Change to temp directory for testing
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_output_dir)
        
        # Create outputs directory
        (temp_output_dir / "outputs").mkdir()
        
        save_post_content(post_id, post_name, post_url, collection_id, content, sample_attachments)
        
        # Verify files were created
        post_dir = temp_output_dir / "outputs" / f"POST_{post_id}_Test Post"
        assert post_dir.exists()
        assert (post_dir / f"{post_id}-desc.html").exists()
        assert (post_dir / f"{post_id}-meta.json").exists()
        assert (post_dir / f"{post_id}-attachments.json").exists()
        
        # Verify metadata includes attachments
        with open(post_dir / f"{post_id}-meta.json") as f:
            metadata = json.load(f)
        assert "attachments" in metadata
        assert len(metadata["attachments"]) == 3
        
        # Verify attachments file
        with open(post_dir / f"{post_id}-attachments.json") as f:
            attachments_data = json.load(f)
        assert len(attachments_data) == 3
        assert attachments_data[0]["filename"] == "model_v1.safetensors"
        
    finally:
        os.chdir(original_cwd)


def test_save_post_content_no_attachments(temp_output_dir):
    """Test saving post content with no attachments."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import save_post_content
    
    post_id = "67890"
    post_name = "No Attachments Post"
    post_url = "https://www.patreon.com/posts/67890"
    collection_id = "888"
    content = {
        "html": "<div>Content without attachments</div>",
        "title": "No Attachments Post | Patreon",
        "url": post_url
    }
    
    original_cwd = Path.cwd()
    try:
        import os
        os.chdir(temp_output_dir)
        
        (temp_output_dir / "outputs").mkdir()
        
        save_post_content(post_id, post_name, post_url, collection_id, content, [])
        
        post_dir = temp_output_dir / "outputs" / f"POST_{post_id}_No Attachments Post"
        assert post_dir.exists()
        assert (post_dir / f"{post_id}-desc.html").exists()
        assert (post_dir / f"{post_id}-meta.json").exists()
        
        # Attachments file should not be created when list is empty
        assert not (post_dir / f"{post_id}-attachments.json").exists()
        
        # Metadata should have empty attachments list
        with open(post_dir / f"{post_id}-meta.json") as f:
            metadata = json.load(f)
        assert metadata["attachments"] == []
        
    finally:
        os.chdir(original_cwd)


def test_javascript_attachment_extraction():
    """Test the JavaScript code used for attachment extraction."""
    # This tests the structure of the JavaScript, not execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    import inspect
    from extract_patreon_content_client import extract_attachments
    
    # Get the source code
    source = inspect.getsource(extract_attachments)
    
    # Verify key elements are in the JavaScript
    assert "querySelectorAll" in source
    assert 'data-tag="post-attachment-link"' in source
    assert "return attachments" in source
    assert "(() => {" in source  # IIFE wrapper
    assert "})()" in source  # IIFE closing


def test_attachment_url_structure(sample_attachments):
    """Test that attachment URLs have expected structure."""
    for att in sample_attachments:
        assert "url" in att
        assert "filename" in att
        assert att["url"].startswith("https://")
        assert "/file?" in att["url"]
        assert len(att["filename"]) > 0


def test_download_creates_attachments_subfolder(mock_client, temp_output_dir, sample_attachments):
    """Test that download creates attachments subfolder."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from extract_patreon_content_client import download_attachments
    
    # Ensure attachments dir doesn't exist initially
    attachments_dir = temp_output_dir / "attachments"
    assert not attachments_dir.exists()
    
    download_attachments(mock_client, sample_attachments, temp_output_dir)
    
    # Should be created by the function
    assert attachments_dir.exists()
    assert attachments_dir.is_dir()
