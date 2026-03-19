# HL → TradingView via Pine Seeds

Получаем котировки Hyperliquid (BRENTOIL, CL) в TradingView через механизм **Pine Seeds**.
После настройки символ доступен в TV как обычный тикер, можно строить формулы со спредом.

---

## Шаг 1 — Создать GitHub репозиторий

1. Зайди на https://github.com/new
2. Название: **tv-seeds** (любое)
3. Видимость: **Public** ← обязательно
4. Нажми **Create repository**
5. Запомни: `YOUR_USERNAME/tv-seeds`

---

## Шаг 2 — Положить файлы в репо

Загрузи в корень репо эти три файла:
- `update_seeds.py`
- `.github/workflows/update.yml`

Создай папку `data/` (положи туда любой пустой файл `.gitkeep`).

**Через веб-интерфейс GitHub:**
- "Add file" → "Create new file" → назови `.github/workflows/update.yml`, вставь содержимое
- Повтори для `update_seeds.py`
- "Add file" → "Create new file" → `data/.gitkeep` (пустой файл)

---

## Шаг 3 — Создать GitHub Personal Access Token

1. https://github.com/settings/tokens → **Generate new token (classic)**
2. Название: `pine-seeds`
3. Поставь галку **repo** (полный доступ к репозиториям)
4. Нажми **Generate token**
5. **Скопируй токен** — он показывается один раз

---

## Шаг 4 — Добавить токен в Secrets репозитория

1. Открой репо → **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. Name: `GH_PAT`
4. Secret: вставь токен из шага 3
5. **Add secret**

---

## Шаг 5 — Запустить вручную первый раз

1. Во вкладке **Actions** найди workflow **Update Pine Seeds**
2. Нажми **Run workflow** → **Run workflow**
3. Через ~30 секунд в папке `data/` появятся:
   - `BRENTOIL.csv`
   - `CL.csv`

После этого workflow будет запускаться автоматически каждые 5 минут.

---

## Шаг 6 — Подключить репо к TradingView

1. Открой https://www.tradingview.com
2. Перейди: **Profile** → **Pine Seeds** (или через меню редактора)
   - Прямая ссылка: https://www.tradingview.com/pine-seeds/
3. Нажми **Add data source**
4. Вставь URL своего репо: `https://github.com/YOUR_USERNAME/tv-seeds`
5. TradingView проверит структуру и подключит

---

## Шаг 7 — Найти символ на графике

В поиске тикера введи:
```
SEED_YOURUSERNAME_TVSEEDS:BRENTOIL
```
(имя пользователя и репо без дефисов, заглавными буквами)

---

## Шаг 8 — Формула спреда в Pine Script

Открой Pine Editor и вставь скрипт из файла `spread_indicator.pine`.

Меняй `YOUR_USERNAME` и `TV_SEEDS` на свои. Сохрани и добавь на график.

Дальше можно вычитать любой другой символ TV:
```pine
brent_tv = request.security("ICEEUR:COIL1!", timeframe.period, close)
diff = brent_hl - brent_tv
```

---

## Структура CSV (Pine Seeds формат)

```
time,open,high,low,close,volume
1700000000,82.5,82.9,82.3,82.7,1250
1700000060,82.7,83.1,82.6,83.0,980
```
`time` — Unix timestamp в **секундах**.

---

## Частые вопросы

**Данные обновляются раз в 5 минут — это ограничение GitHub Actions.**
Для более частого обновления нужно держать `update_seeds.py` запущенным локально через cron:
```bash
# macOS/Linux: crontab -e
* * * * * cd /path/to/pine_seeds && python update_seeds.py
```

**Ошибка "Repository not found" в TV?**
Репо должно быть **Public**.

**Символ не отображается в поиске TV?**
Подожди 10–15 минут после первого пуша — TV индексирует с задержкой.
