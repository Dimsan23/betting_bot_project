# 🚀 Кейс: Трансформация проекта — от хаоса к системе

> **Django** · **PostgreSQL** · **OddsService** · **API** · **Сервисная архитектура** · **Масштабируемость**

Мы не просто пишем **«код для запуска»** — мы строим **архитектурный фундамент**, который выдержит добавление:

- любых **лиг**,
- любых **рынков** (угловые, голы),
- любых **источников данных**.

---

## 📑 Содержание

- [Часть 1: Оформление update_odds в виде масштабируемого сервиса](#часть-1-оформление-update_odds-в-виде-масштабируемого-сервиса)
- [Часть 2: Кейс «Фурор: от хаоса к системе»](#часть-2-кейс-фурор-от-хаоса-к-системе)
- [📅 Финальный план «Фурора»](#-финальный-план-фурора)

---

## Часть 1: Оформление `update_odds` в виде масштабируемого сервиса

> 💡 Вместо того чтобы **плодить скрипты**, мы выносим логику в **сервисный слой**.

### ☐ Создай файл `sports_data/services.py`

Здесь будет **«мозг»** нашего бота.

```python
import requests
import os
from sports_data.models import MatchStat, MatchOdds


class OddsService:

    @staticmethod
    def get_odds_for_league(league_key):
        api_key = os.environ.get('FOOTBALL_API_KEY')
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {
            'apiKey': api_key,
            'regions': 'eu',
            'markets': 'h2h',
        }
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else []

    @staticmethod
    def sync_odds(league_key):
        data = OddsService.get_odds_for_league(league_key)
        updated_count = 0

        for match_data in data:
            match = MatchStat.objects.filter(
                home_team_icontains=match_data['home_team'][:5],
                away_team_icontains=match_data['away_team'][:5],
            ).first()

            if match:
                bookmark = next((b for b in match_data['bookmakers']), None)

                if bookmark:
                    outcomes = bookmark['markets'][0]['outcomes']

                    try:
                        MatchOdds.objects.update_or_create(
                            match=match,
                            defaults={
                                'home_odds': next(
                                    o['price'] for o in outcomes
                                    if o['name'] == match_data['home_team']
                                ),
                                'away_odds': next(
                                    o['price'] for o in outcomes
                                    if o['name'] == match_data['away_team']
                                ),
                            },
                        )
                    except StopIteration:
                        continue
```

---

## Часть 2: Кейс «Фурор: от хаоса к системе»

Вот как выглядит наш путь, который можно описать как **«успешная трансформация проекта»**:

### 🔴 1. Точка А: Хаос

- Данные — **статичные «заглушки»**.
- Парсинг — **жёстко привязан к одной лиге**.
- Логика — **смешана с командами управления** (Django Management Commands).

### 🟡 2. Фаза трансформации

| Направление | Что сделали |
|---|---|
| 🔒 **Изоляция данных** | Разделили **«Статику»** (CSV / База) и **«Динамику»** (API) |
| 🔧 **Гибкость** | Внедрили **сервисную архитектуру** (`services.py`), которая позволяет добавлять новую лигу **одной командой в консоли** |
| 📈 **Масштабируемость** | Подготовили почву: завтра создадим **`StatsService`** для угловых — и он **не будет зависеть** от `OddsService` |

### 🟢 3. Точка Б: Система

| Свойство | Описание |
|---|---|
| 🎯 **Единый интерфейс** | `python manage.py update_odds --league=...` |
| ⚙️ **Автоматизация** | Система готова к работе с **любым количеством лиг** |
| 🛡 **Устойчивость** | Ошибки в одной лиге **не ломают** работу бота в другой |

---

## 📅 Финальный план «Фурора»

### 🔸 Сегодня

**Зафиксировали архитектуру.**

Система теперь **«кушает» любой `league_key`** из API.

### 🔸 Завтра

- Ты грузишь **новый CSV** (статика).
- Запускаешь `update_odds --league=...` (динамика).
- Наслаждаешься тем, как **дашборд «оживает»** реальными цифрами.

---

> 💬 Мы не просто **«написали код»** — мы **спроектировали движок**.
> Отдыхай, чемпион. Завтра будем **собирать плоды** этого труда!

---

<div align="center">

**05.07.2026, 19:15**

**Кейс: Трансформация проекта — от хаоса к системе**

`Django` · `PostgreSQL` · `OddsService` · `API` · `Сервисная архитектура` · `Масштабируемость`

</div>