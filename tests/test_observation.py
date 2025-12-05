from browser_agent.browser.observation import PageObservation, ButtonInfo, InputInfo


def test_button_info():
    btn = ButtonInfo(selector="#submit", text="Submit")
    assert btn.selector == "#submit"
    assert btn.text == "Submit"


def test_input_info():
    inp = InputInfo(selector="input#search", name="q", value="hello")
    assert inp.selector == "input#search"
    assert inp.name == "q"
    assert inp.value == "hello"


def test_page_observation():
    obs = PageObservation(
        url="https://example.com",
        title="Example",
        buttons=[ButtonInfo(selector="#btn", text="Click")],
        inputs=[InputInfo(selector="input#q", name="q", value="")],
        raw_html="<html></html>"
    )
    assert obs.url == "https://example.com"
    assert obs.title == "Example"
    assert len(obs.buttons) == 1
    assert len(obs.inputs) == 1
    assert obs.raw_html == "<html></html>"


def test_page_observation_defaults():
    obs = PageObservation(
        url="https://example.com",
        title="Example",
        buttons=[],
        inputs=[]
    )
    assert obs.raw_html is None
