# API Endpoint Diagnostic Report

**Date**: 2026-01-25  
**Issue**: `/fetch-image` endpoint returns 500 error for video preview URLs  
**Repository**: `grok/auto_download_favourites/keyboard_api.py` (lines 388-459)

## Problem Summary

The improved `/fetch-image` endpoint successfully returns actual images for public URLs but fails with **500 errors** for authenticated video preview URLs from `assets.grok.com`.

### Test Results (100 tiles tested)

| Status | Count | Image URLs | Example |
|--------|-------|-----------|---------|
| ✅ **Success** | ~90 | `imagine-public.x.ai` | Public image tiles |
| ❌ **Failed (500)** | ~10 | `assets.grok.com` | Video preview thumbnails |

### Direct HTTP vs API Comparison

| Method | Public Images | Video Previews |
|--------|--------------|----------------|
| **Direct HTTP** | ✅ 200 OK | ❌ 403 Forbidden (expected) |
| **API Endpoint** | ✅ 200 OK | ❌ 500 Error (unexpected) |

## Root Cause Analysis

### Current Implementation

```python
# grok/auto_download_favourites/keyboard_api.py:388-459
@app.route("/fetch-image", methods=["POST"])
def fetch_image():
    # ...
    try:
        # ❌ PROBLEM: Uses requests.get() without browser session
        response = requests.get(image_url, timeout=10, stream=True)
        response.raise_for_status()  # This throws when status != 200
        # ...
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download image: {str(e)}"}), 500
```

### Why It Fails

1. **No Browser Session**: `requests.get()` makes a standalone HTTP request without browser cookies/auth
2. **403 → 500 Conversion**: When `assets.grok.com` returns 403 (auth required), `raise_for_status()` throws an exception
3. **Generic Error**: The exception is caught and returned as a generic 500 error, hiding the real 403 status

### Why Public Images Work

- `imagine-public.x.ai` URLs are **publicly accessible** (no auth required)
- Regular HTTP requests succeed with 200 OK
- Images are downloaded, encoded, and returned successfully

## Test Evidence

### Successful Image Tile (Tile #2)

```
📡 Fetching via API: https://imagine-public.x.ai/cdn-cgi/image/width=500...
   ✅ Format: JPEG, Size: (500, 744), Mode: RGB
   📊 Data size: 49,312 bytes (48.2 KB)
   📦 Content-Type: image/jpeg, API Format: jpg

🌐 Fetching directly: https://imagine-public.x.ai/cdn-cgi/image/width=500...
   ✅ Format: JPEG, Size: (500, 744), Mode: RGB
   📊 Data size: 49,312 bytes (48.2 KB)

   🔑 API hash:    8710c8c43ae1
   🔑 Direct hash: 8710c8c43ae1
   ✅ MATCH: API and direct fetch produce identical images
```

### Failed Video Tile (Tile #1, #9, #11, etc.)

```
📍 TILE #1 - VIDEO
   URL: https://assets.grok.com/users/2ddebc11-faf0-4ade-850b-d8668ed1dbfd/generated/d85...

📡 Fetching via API: https://assets.grok.com/users/...
   ❌ API returned status 500

🌐 Fetching directly: https://assets.grok.com/users/...
   ❌ HTTP returned status 403
   ❌ Both methods failed!
```

## Proposed Solutions

### Solution 1: Use Browser Session (Recommended)

The Flask app runs inside the same container as the browser. Access the browser's authenticated session to fetch images.

**Implementation Options**:

#### Option A: Use Selenium/Playwright to fetch via browser

```python
# Use the existing browser instance to fetch authenticated URLs
def fetch_image_via_browser(url):
    """Fetch image using browser's authenticated session."""
    from selenium import webdriver
    
    # Connect to existing browser on localhost
    # Fetch URL through browser
    # Extract image data from response
    pass
```

#### Option B: Extract and forward browser cookies

```python
def fetch_image():
    # ...
    # Get browser cookies from Chrome profile
    cookies = get_browser_cookies()
    
    # Use cookies in request
    response = requests.get(
        image_url, 
        timeout=10, 
        stream=True,
        cookies=cookies,
        headers={'User-Agent': 'Mozilla/5.0 ...'}
    )
```

#### Option C: Use Chrome DevTools Protocol (CDP)

```python
# Connect to Chrome via CDP and intercept network responses
# Fetch images through the browser's network stack
```

### Solution 2: Better Error Reporting

Even if auth isn't fixed immediately, improve error messages:

```python
@app.route("/fetch-image", methods=["POST"])
def fetch_image():
    # ...
    try:
        response = requests.get(image_url, timeout=10, stream=True)
        
        # ✅ Check status before raising
        if response.status_code == 403:
            return jsonify({
                "status": "error",
                "error": "Authentication required",
                "detail": "URL requires browser session authentication",
                "status_code": 403,
                "url": image_url
            }), 403
        
        response.raise_for_status()
        # ... rest of success path
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to download image: {str(e)}",
            "url": image_url
        }), 500
```

### Solution 3: Fallback Strategy

```python
def fetch_image():
    # Try direct fetch first
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            # Success - return image
            pass
    except:
        pass
    
    # If failed, try browser-based fetch for authenticated URLs
    if 'assets.grok.com' in image_url:
        return fetch_via_browser(image_url)
    
    return jsonify({"error": "Failed to fetch"}), 500
```

## Recommended Implementation Path

1. **Phase 1: Improve error reporting** (5 minutes)
   - Return proper 403 status instead of 500
   - Include detailed error messages
   - Test to confirm better diagnostics

2. **Phase 2: Add browser session support** (30-60 minutes)
   - Research Chrome DevTools Protocol or Selenium integration
   - Implement browser-based fetch for authenticated URLs
   - Add `use_browser_session` parameter to endpoint

3. **Phase 3: Add fallback logic** (15 minutes)
   - Try direct fetch first (fast for public URLs)
   - Fall back to browser fetch for auth URLs
   - Cache successful auth patterns

## Testing Checklist

- [ ] Public images still work (`imagine-public.x.ai`)
- [ ] Video previews return 403 (not 500) with clear error
- [ ] Browser-based fetch works for `assets.grok.com`
- [ ] Performance acceptable (< 5s per image)
- [ ] Error messages include URL and status code
- [ ] Metadata still returned (format, content_type, size_bytes)

## Files to Modify

- `grok/auto_download_favourites/keyboard_api.py` (lines 388-459)
- Add tests in `grok/tests/test_image_upload.py` or new test file

## Additional Context

### Browser Setup
- Browser: Chrome in Docker container
- Display: Xvfb on :99
- VNC: noVNC on port 6080
- API: Flask on port 5000

### URL Patterns
- **Public**: `https://imagine-public.x.ai/cdn-cgi/image/width=500...`
- **Authenticated**: `https://assets.grok.com/users/{uuid}/generated/{id}...`

### Current Benefits of Improved Endpoint
✅ Returns original image format (not screenshots)  
✅ Preserves original file size (~9x smaller than screenshots)  
✅ Includes metadata (format, content_type, size_bytes)  
✅ Works perfectly for public URLs  
❌ **Needs fix**: Doesn't work for authenticated video previews
