from browser_agent.browser.actions import Navigate, Click, Type, WaitForSelector


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
