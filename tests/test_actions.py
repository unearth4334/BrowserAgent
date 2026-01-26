from browser_agent.browser.actions import (
    Navigate,
    Click,
    Type,
    WaitForSelector,
    WaitForUser,
    ExtractLinks,
    ExtractHTML,
    ExecuteJS,
    UploadFile,
    SelectOption,
    SetSlider,
    Scroll,
)


def test_action_dataclasses_init():
    n = Navigate(url="https://example.com")
    c = Click(selector="#btn")
    t = Type(selector="#input", text="hello", press_enter=True)
    w = WaitForSelector(selector="#ready", timeout_ms=1234)

    assert n.url == "https://example.com"
    assert c.selector == "#btn"
    assert t.text == "hello"
    assert t.press_enter is True
    assert w.timeout_ms == 1234


def test_wait_for_user_action():
    wfu = WaitForUser(message="Please authenticate...")
    assert wfu.message == "Please authenticate..."
    
    # Test default message
    wfu_default = WaitForUser()
    assert wfu_default.message == "Press Enter to continue..."


def test_extract_links_action():
    el = ExtractLinks(pattern='a[href*="/posts/"]')
    assert el.pattern == 'a[href*="/posts/"]'


def test_extract_html_action():
    """Test ExtractHTML action initialization."""
    eh = ExtractHTML(selector='div[class*="content"]')
    assert eh.selector == 'div[class*="content"]'
    
    # Test with different selectors
    eh2 = ExtractHTML(selector='#main-content')
    assert eh2.selector == '#main-content'


def test_execute_js_action():
    """Test ExecuteJS action initialization."""
    ejs = ExecuteJS(code="return document.title;")
    assert ejs.code == "return document.title;"


def test_upload_file_action():
    """Test UploadFile action initialization."""
    uf = UploadFile(selector="input[type=file]", file_path="/tmp/test.png")
    assert uf.selector == "input[type=file]"
    assert uf.file_path == "/tmp/test.png"


def test_select_option_action():
    """Test SelectOption action initialization."""
    so = SelectOption(selector="select#country", value="US")
    assert so.selector == "select#country"
    assert so.value == "US"


def test_set_slider_action():
    """Test SetSlider action initialization."""
    ss = SetSlider(selector="input[type=range]", value=50.5)
    assert ss.selector == "input[type=range]"
    assert ss.value == 50.5


def test_scroll_action():
    """Test Scroll action initialization."""
    # Test pixel-based scrolling
    scroll_down = Scroll(pixels=1000, direction="down")
    assert scroll_down.pixels == 1000
    assert scroll_down.direction == "down"
    assert scroll_down.selector is None
    
    # Test scrolling up
    scroll_up = Scroll(pixels=500, direction="up")
    assert scroll_up.pixels == 500
    assert scroll_up.direction == "up"
    
    # Test element-based scrolling
    scroll_to_elem = Scroll(selector="#target-element")
    assert scroll_to_elem.selector == "#target-element"
    assert scroll_to_elem.pixels is None
    
    # Test horizontal scrolling
    scroll_right = Scroll(pixels=300, direction="right")
    assert scroll_right.direction == "right"
