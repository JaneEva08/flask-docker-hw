"""Автотесты API. Запуск: pip install -r requirements-dev.txt && pytest -q"""

import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


# --- основной путь ---------------------------------------------------------

def test_home_lists_endpoints(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "/info" in r.get_json()["endpoints"]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "healthy"


def test_info_has_container_fields(client):
    data = client.get("/info").get_json()
    for key in ("container", "python", "platform", "uptime_seconds"):
        assert key in data


@pytest.mark.parametrize(
    "url, expected",
    [
        ("/calc/10/4", 14),             # по умолчанию add
        ("/calc/10/4?op=sub", 6),
        ("/calc/10/4?op=mul", 40),
        ("/calc/10/4?op=div", 2.5),
        ("/calc/10/2?op=div", 5),       # целый результат без .0
        ("/calc/-5/3?op=add", -2),      # отрицательные (<int:> в Flask их не принимает)
        ("/calc/2.5/2?op=mul", 5),      # дробные
        ("/calc/0,1/0,2?op=add", 0.3),  # запятая как разделитель; 0.1+0.2 без хвоста
        ("/calc/10/3?op=DIV", 3.3333333333),  # регистр операции не важен
    ],
)
def test_calc(client, url, expected):
    r = client.get(url)
    assert r.status_code == 200
    assert r.get_json()["result"] == expected


# --- ошибочный ввод --------------------------------------------------------

@pytest.mark.parametrize(
    "url",
    [
        "/calc/10/0?op=div",   # деление на ноль
        "/calc/abc/5",         # не число
        "/calc/nan/5",         # nan формально парсится float(), но это не число
        "/calc/inf/5",
        "/calc/10/5?op=pow",   # неизвестная операция
    ],
)
def test_calc_bad_input_returns_400(client, url):
    r = client.get(url)
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_unknown_path_returns_json_404(client):
    r = client.get("/nope")
    assert r.status_code == 404
    assert "error" in r.get_json()


# --- безопасность ----------------------------------------------------------

def test_info_does_not_leak_environment(client, monkeypatch):
    """В уроке / отдавал dict(os.environ) — здесь проверяем, что секреты не утекают."""
    monkeypatch.setenv("SECRET_TOKEN", "super-secret-123")
    for url in ("/", "/info", "/health"):
        assert "super-secret-123" not in client.get(url).get_data(as_text=True)
