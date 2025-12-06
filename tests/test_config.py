from browser_agent.config import Settings


def test_settings_default():
    settings = Settings()
    assert settings.browser_executable_path is None
    assert settings.headless is True


def test_settings_from_env_with_custom_values(monkeypatch):
    monkeypatch.setenv("BROWSER_AGENT_BROWSER_EXE", "/usr/bin/brave")
    monkeypatch.setenv("BROWSER_AGENT_HEADLESS", "false")
    
    settings = Settings.from_env()
    assert settings.browser_executable_path == "/usr/bin/brave"
    assert settings.headless is False


def test_settings_from_env_with_no_value(monkeypatch):
    monkeypatch.delenv("BROWSER_AGENT_BROWSER_EXE", raising=False)
    monkeypatch.delenv("BROWSER_AGENT_HEADLESS", raising=False)
    
    settings = Settings.from_env()
    assert settings.browser_executable_path is None
    assert settings.headless is True


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
