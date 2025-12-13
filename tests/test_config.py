from browser_agent.config import Settings


def test_settings_default():
    settings = Settings()
    assert settings.browser_executable_path is None
    assert settings.headless is True
    assert settings.browser_type == "chromium"
    assert settings.launch_timeout == 15000
    assert settings.navigation_timeout == 30000
    assert settings.default_wait == "load"
    assert settings.extra_launch_args == []


def test_settings_from_env_with_custom_values(monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_BROWSER_EXE", "/usr/bin/brave")
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "false")
    monkeypatch.setenv("BROWSER_AGENT_BROWSER_TYPE", "firefox")
    monkeypatch.setenv("BROWSER_AGENT_LAUNCH_TIMEOUT", "20000")
    monkeypatch.setenv("BROWSER_AGENT_NAVIGATION_TIMEOUT", "45000")
    monkeypatch.setenv("BROWSER_AGENT_DEFAULT_WAIT", "networkidle")
    monkeypatch.setenv("BROWSER_AGENT_EXTRA_ARGS", "--no-sandbox,--disable-gpu")
    
    settings = Settings.from_env()
    assert settings.browser_executable_path == "/usr/bin/brave"
    assert settings.headless is False
    assert settings.browser_type == "firefox"
    assert settings.launch_timeout == 20000
    assert settings.navigation_timeout == 45000
    assert settings.default_wait == "networkidle"
    assert settings.extra_launch_args == ["--no-sandbox", "--disable-gpu"]


def test_settings_from_env_with_no_value(monkeypatch):
    monkeypatch.delenv("BROWSER_AGENT_BROWSER_EXE", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_HEADLESS", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_BROWSER_TYPE", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_LAUNCH_TIMEOUT", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_NAVIGATION_TIMEOUT", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_DEFAULT_WAIT", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_EXTRA_ARGS", raising=False)
    
    settings = Settings.from_env()
    assert settings.browser_executable_path is None
    assert settings.headless is True
    assert settings.browser_type == "chromium"
    assert settings.launch_timeout == 15000
    assert settings.navigation_timeout == 30000
    assert settings.default_wait == "load"
    assert settings.extra_launch_args == []


def test_settings_from_env_headless_variations(monkeypatch):
    # Test "0" means not headless
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "0")
    assert Settings.from_env().headless is False
    
    # Test "no" means not headless
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "no")
    assert Settings.from_env().headless is False
    
    # Test "1" means headless
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "1")
    assert Settings.from_env().headless is True
    
    # Test "true" means headless
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "true")
    assert Settings.from_env().headless is True
