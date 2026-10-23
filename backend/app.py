"""
Flask-приложение для ДЗ VPe02 «Docker для вайбкодера».

Эндпоинты:
  GET /                       — приветствие и список эндпоинтов
  GET /info                   — информация о контейнере (без переменных окружения!)
  GET /calc/<a>/<b>?op=...    — калькулятор: add, sub, mul, div (по умолчанию add)
  GET /health                 — проверка здоровья для Docker healthcheck

Отличия от примера из урока:
  - /info НЕ отдаёт os.environ: в реальном проекте там лежат токены и ключи;
  - /calc принимает отрицательные и дробные числа (конвертер <int:> в Flask
    отвечает 404 на «-5» и «2.5»), деление на ноль и мусор дают понятный 400.
"""

import math
import os
import platform
import socket
from datetime import datetime, timezone

from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # кириллица в ответах читается как текст, а не с...

STARTED_AT = datetime.now(timezone.utc)

OPERATIONS = {
    "add": ("+", lambda a, b: a + b),
    "sub": ("−", lambda a, b: a - b),
    "mul": ("×", lambda a, b: a * b),
    "div": ("÷", lambda a, b: a / b),
}


def parse_number(raw: str):
    """Строка → int или float. None, если это не конечное число."""
    try:
        value = float(raw.replace(",", "."))
    except ValueError:
        return None
    if not math.isfinite(value):  # отсекаем nan, inf
        return None
    return int(value) if value.is_integer() else value


def tidy(value):
    """5.0 → 5, 3.3333333333 → 3.3333333333 (без хвоста из ошибок округления)."""
    if isinstance(value, float):
        value = round(value, 10)
        if value.is_integer():
            return int(value)
    return value


@app.get("/")
def home():
    return jsonify(
        message="Приложение запущено в Docker-контейнере",
        endpoints={
            "/info": "информация о контейнере",
            "/calc/<a>/<b>?op=add|sub|mul|div": "калькулятор, по умолчанию add",
            "/health": "проверка здоровья",
        },
        example="/calc/10/4?op=div",
    )


@app.get("/info")
def info():
    uptime = datetime.now(timezone.utc) - STARTED_AT
    return jsonify(
        container=socket.gethostname(),  # в Docker это короткий ID контейнера
        python=platform.python_version(),
        platform=platform.platform(),
        app_env=os.environ.get("APP_ENV", "not set"),  # только одна безопасная переменная
        started_at=STARTED_AT.isoformat(timespec="seconds"),
        uptime_seconds=int(uptime.total_seconds()),
    )


@app.get("/calc/<a>/<b>")
def calc(a, b):
    op = request.args.get("op", "add").lower()
    if op not in OPERATIONS:
        return jsonify(error=f"Неизвестная операция «{op}»", allowed=list(OPERATIONS)), 400

    x, y = parse_number(a), parse_number(b)
    if x is None or y is None:
        return jsonify(error="a и b должны быть числами, например /calc/10/4 или /calc/-2.5/4"), 400
    if op == "div" and y == 0:
        return jsonify(error="Деление на ноль"), 400

    sign, func = OPERATIONS[op]
    result = tidy(func(x, y))
    return jsonify(a=x, b=y, op=op, expression=f"{x} {sign} {y} = {result}", result=result)


@app.get("/health")
def health():
    return jsonify(status="healthy", time=datetime.now(timezone.utc).isoformat(timespec="seconds"))


@app.errorhandler(404)
def not_found(_):
    return jsonify(error="Нет такого адреса", hint="Список эндпоинтов — на /"), 404


if __name__ == "__main__":
    # Только для локального запуска без Docker. В контейнере работает gunicorn.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
