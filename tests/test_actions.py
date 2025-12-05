from browser_agent.browser.actions import (
    Navigate,
    Click,
    Type,
    WaitForSelector,
    WaitForUser,
    ExtractLinks,
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
