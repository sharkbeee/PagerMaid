import pytest
from pydantic import ValidationError

from pagermaid.config import Config
from pagermaid.web.settings import WebSettings


def test_web_settings_defaults():
    settings = WebSettings()

    assert settings.enabled is False
    assert settings.login_enabled is False
    assert settings.secret_key == "secret_key"
    assert settings.host == "127.0.0.1"
    assert settings.port == 3333
    assert settings.allowed_origins == ["*"]
    assert settings.enable_shell is False
    assert settings.enable_eval is False


def test_web_settings_allowed_origins_accepts_list():
    settings = WebSettings(allowed_origins=["https://example.com", "http://test"])

    assert settings.allowed_origins == ["https://example.com", "http://test"]


def test_web_settings_allowed_origins_normalizes_comma_separated_string():
    settings = WebSettings(
        allowed_origins="https://example.com, http://test,  ,http://localhost"
    )

    assert settings.allowed_origins == [
        "https://example.com",
        "http://test",
        "http://localhost",
    ]


@pytest.mark.parametrize("port", [0, 65536])
def test_web_settings_rejects_invalid_port(port: int):
    with pytest.raises(ValidationError):
        WebSettings(port=port)


def test_web_settings_does_not_load_environment_directly(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    monkeypatch.setenv("PORT", "9999")

    settings = WebSettings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 3333


def test_web_settings_from_legacy_config_matches_config():
    settings = WebSettings.from_legacy_config()

    assert settings.enabled == bool(Config.WEB_ENABLE)
    assert settings.login_enabled == bool(Config.WEB_LOGIN)
    assert settings.secret_key == Config.WEB_SECRET_KEY
    assert settings.host == Config.WEB_HOST
    assert settings.port == Config.WEB_PORT
    assert settings.allowed_origins == list(Config.WEB_ORIGINS)
