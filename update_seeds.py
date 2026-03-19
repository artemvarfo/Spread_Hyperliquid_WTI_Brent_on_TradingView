"""
HL → Pine Seeds updater
========================
Тянет свечи с Hyperliquid (BRENTOIL, CL) и пушит CSV в GitHub.
TradingView читает репо и отдаёт символы как SEED_<USER>_<REPO>:BRENTOIL

Зависимости:
    pip install requests PyGithub

Переменные окружения (или вписать прямо):
    GITHUB_TOKEN   — Personal Access Token (scope: repo)
    GITHUB_REPO    — например: myusername/tv-seeds
"""

import os
import csv
import io
import time
import requests
from github import Github

# ── Конфиг ─────────────────────────────────────────────────────────────────────
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
GITHUB_REPO  = os.environ.get("GITHUB_REPO",  "YOUR_USERNAME/tv-seeds")
INTERVAL     = "1"       # свечи в минутах (1m — минимум для Pine Seeds)
LOOKBACK_MS  = 20 * 24 * 60 * 60 * 1000   # 7 дней истории при первом запуске
HL_URL       = "https://api.hyperliquid.xyz/info"

SYMBOLS = {
    "BRENTOIL": "xyz:BRENTOIL",
    "CL":       "xyz:CL",
}
# ──────────────────────────────────────────────────────────────────────────────

def fetch_candles(hl_coin: str, interval: str, start_ms: int, end_ms: int) -> list[dict]:
    resp = requests.post(HL_URL, json={
        "type": "candleSnapshot",
        "req": {
            "coin":      hl_coin,
            "interval":  f"{interval}m",
            "startTime": start_ms,
            "endTime":   end_ms,
        }
    }, timeout=15)
    resp.raise_for_status()
    raw = resp.json()
    return [
        {
            "time":   c["t"] // 1000,          # Unix секунды
            "open":   float(c["o"]),
            "high":   float(c["h"]),
            "low":    float(c["l"]),
            "close":  float(c["c"]),
            "volume": float(c["v"]),
        }
        for c in raw
    ]


def candles_to_csv(candles: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["time","open","high","low","close","volume"])
    writer.writeheader()
    writer.writerows(candles)
    return buf.getvalue()


def get_existing_last_time(repo, path: str) -> int | None:
    """Читает последнюю строку CSV из репо, возвращает timestamp последней свечи."""
    try:
        content = repo.get_contents(path)
        text = content.decoded_content.decode()
        lines = [l for l in text.strip().splitlines() if l and not l.startswith("time")]
        if not lines:
            return None
        last = lines[-1].split(",")
        return int(last[0])
    except Exception:
        return None


def merge_candles(existing_csv: str | None, new_candles: list[dict]) -> str:
    """Сливает старые и новые свечи, дедуплицирует по time."""
    old: dict[int, dict] = {}
    if existing_csv:
        reader = csv.DictReader(io.StringIO(existing_csv))
        for row in reader:
            t = int(row["time"])
            old[t] = {k: float(v) if k != "time" else int(v) for k, v in row.items()}

    for c in new_candles:
        old[c["time"]] = c

    merged = sorted(old.values(), key=lambda x: x["time"])
    return candles_to_csv(merged)


def update_symbol(repo, symbol_name: str, hl_coin: str):
    path = f"data/{symbol_name}.csv"
    now_ms = int(time.time() * 1000)

    # Определяем, с какого времени тянуть
    last_time = get_existing_last_time(repo, path)
    if last_time:
        start_ms = last_time * 1000 - 5 * 60 * 1000   # -5 мин на перекрытие
    else:
        start_ms = now_ms - LOOKBACK_MS

    print(f"  Fetching {symbol_name} ({hl_coin}) ...", end=" ")
    candles = fetch_candles(hl_coin, INTERVAL, start_ms, now_ms)
    print(f"{len(candles)} candles")

    if not candles:
        print(f"  No new candles for {symbol_name}, skipping.")
        return

    # Получаем текущее содержимое файла (если есть)
    try:
        existing_file = repo.get_contents(path)
        existing_csv  = existing_file.decoded_content.decode()
        existing_sha  = existing_file.sha
    except Exception:
        existing_csv  = None
        existing_sha  = None

    new_csv = merge_candles(existing_csv, candles)

    if existing_sha:
        repo.update_file(path, f"update {symbol_name}", new_csv, existing_sha)
    else:
        repo.create_file(path, f"init {symbol_name}", new_csv)

    print(f"  ✓ {symbol_name} pushed to GitHub")


def main():
    print(f"[{time.strftime('%H:%M:%S')}] Starting Pine Seeds update...")
    g    = Github(GITHUB_TOKEN)
    repo = g.get_repo(GITHUB_REPO)

    for symbol_name, hl_coin in SYMBOLS.items():
        try:
            update_symbol(repo, symbol_name, hl_coin)
        except Exception as e:
            print(f"  ✗ Error updating {symbol_name}: {e}")

    print("Done.\n")


if __name__ == "__main__":
    main()
