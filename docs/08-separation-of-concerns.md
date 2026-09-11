# 🏛 Архитектурный кейс: Разделение ответственности в Sports Trading Bot

> **Django** · **PostgreSQL** · **StatsService** · **OddsService** · **Decoupling** · **Масштабируемость**

Для профессионального проекта **разделение ответственности** — это **закон**.

Сейчас у тебя две разные сущности:

- 📊 **«Статистика»** — исторические данные матчей из **API-Football**.
- 💰 **«Коэффициенты»** — текущие ставки из **The Odds API**.

Давай **«причешем»** твою архитектуру. Мы создадим `services.py`, где будут жить **два класса**:
- `StatsService` (бывший `FootballDataFetcher`),
- `OddsService`.

---

## 📑 Содержание

- [1. sports_data/services.py (Единый слой бизнес-логики)](#1-sports_dataservicespy-единый-слой-бизнес-логики)
- [2. sports_data/management/commands/update_odds.py (Чистый CLI)](#2-sports_datamanagementcommandsupdate_oddspy-чистый-cli)
- [3. Почему это профессионально](#3-почему-это-профессионально)
- [4. Как теперь работать](#4-как-теперь-работать)
- [5. Архитектурная карта данных](#5-архитектурная-карта-данных)
- [6. Почему твоя структура теперь «неубиваемая»](#6-почему-твоя-структура-теперь-неубиваемая)
- [7. Золотое правило «Статика + Динамика»](#7-золотое-правило-статика--динамика)
- [8. Твой профессиональный план действий](#8-твой-профессиональный-план-действий)

---

## 1. `sports_data/services.py` (Единый слой бизнес-логики)

Этот файл становится **«мозгом»** твоего приложения.

> 💡 **Никакого вывода в консоль — только чистая логика данных.**

```python
import requests
import os
from sports_data.models import MatchStat, MatchOdds


class StatsService:
    """Сервис для работы с исторической статистикой (API-Football)"""

    def __init__(self):
        self.api_key = os.environ.get('FOOTBALL_API_KEY_STATS')  # Свой ключ для статистики
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {'x-apisports-key': self.api_key}

    def sync_fixtures(self, league_obj):
        endpoint = f"{self.base_url}/fixtures"
        params = {
            'league': league_obj.api_id,
            'season': 2026,
            'status': 'FT',
        }
        response = requests.get(endpoint, headers=self.headers, params=params)

        if response.status_code != 200:
            return 0

        data = response.json().get('response', [])
        count = 0

        for f in data:
            _, created = MatchStat.objects.update_or_create(
                match_date=f['fixture']['date'],
                home_team=f['teams']['home']['name'],
                away_team=f['teams']['away']['name'],
                defaults={
                    'league': league_obj,
                    'home_goals': f['goals']['home'],
                    'away_goals': f['goals']['away'],
                },
            )
            if created:
                count += 1

        return count


class OddsService:
    """Сервис для работы с коэффициентами (The Odds API)"""

    @staticmethod
    def sync_odds(league_key):
        api_key = os.environ.get('FOOTBALL_API_KEY')
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {
            'apiKey': api_key,
            'regions': 'eu',
            'markets': 'h2h',
        }
        response = requests.get(url, params=params)

        if response.status_code != 200:
            return 0

        data = response.json()
        updated_count = 0

        for match_data in data:
            match = MatchStat.objects.filter(
                home_team_icontains=match_data['home_team'][:5],
                away_team_icontains=match_data['away_team'][:5],
            ).first()

            if match:
                bookmaker = next((b for b in match_data['bookmakers']), None)

                if bookmaker:
                    outcomes = bookmaker['markets'][0]['outcomes']

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
                                'draw_odds': next(
                                    (o['price'] for o in outcomes if o['name'] == 'Draw'),
                                    0.0,
                                ),
                            },
                        )
                        updated_count += 1

                    except (StopIteration, KeyError, IndexError):
                        continue

        return updated_count
```

---

## 2. `sports_data/management/commands/update_odds.py` (Чистый CLI)

Теперь команда управления **не содержит логики** — она лишь **вызывает нужный метод сервиса**.

```python
from django.core.management.base import BaseCommand
from sports_data.services import OddsService


class Command(BaseCommand):
    help = 'Обновление коэффициентов из The Odds API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--league',
            type=str,
            required=True,
            help='Ключ лиги (напр. soccer_usa_mls)',
        )

    def handle(self, *args, **kwargs):
        league = kwargs['league']
        self.stdout.write(f"Запуск синхронизации коэффициентов для {league}...")

        count = OddsService.sync_odds(league)

        self.stdout.write(
            self.style.SUCCESS(f"Готово! Обновлено матчей: {count}")
        )
```

---

## 3. Почему это профессионально

| Свойство | Что даёт |
|---|---|
| 📈 **Масштабируемость** | Захотел добавить угловые? Создаёшь метод `sync_corners` в `StatsService`. Твой `update_odds.py` при этом **вообще не меняется** |
| 🧪 **Тестируемость** | Теперь ты можешь написать **юнит-тесты** на `OddsService.sync_odds`, **не вызывая команды Django** |
| ♻️ **Переиспользование** | Если захочешь сделать **API-view**, чтобы «дёргать» обновление кэфов прямо из админки (по кнопке), ты просто **импортируешь `OddsService`** в свой `views.py` |

---

## 4. Как теперь работать

```bash
# Для обновления кэфов:
python manage.py update_odds --league=soccer_epl

# Для статики (если напишешь команду под StatsService):
python manage.py import_stats --league_id=123
```

> ✅ Теперь у тебя в проекте **идеальный порядок**.
> Завтра, когда будешь грузить CSV или парсить лигу, у тебя под рукой уже будет **готовый инструмент**, который **не «развалится»** от масштабирования.

---

## 5. Архитектурная карта данных

Давай зафиксируем эту архитектуру, чтобы у тебя была **чёткая картина**, как все три источника данных работают вместе, **не конфликтуя** друг с другом.

Вот как выглядит **«закон разделения ответственности»** в твоём случае:

| Тип данных | Источник | Роль | Частота обновления |
|---|---|---|---|
| **Статика** (Расписание / Результаты) | `football-data.co.uk` (CSV) | **Фундамент** (названия команд, даты, лиги) | Периодически (**раз в неделю**) |
| **История** (API) | **API-Football** | Дополнение статистики (голы, карточки) | Разово по завершении матча |
| **Динамика** (Коэффициенты) | **The Odds API** | Актуальный **Value** (ставки, кэфы) | В реальном времени (**каждые 15 мин**) |

---

## 6. Почему твоя структура теперь «неубиваемая»

Когда ты разделил эти сущности в `services.py`, ты добился важного преимущества: **декаплинга**.

| Сценарий | Что происходит |
|---|---|
| 🔴 **Упал API-Football** | Твой дашборд **продолжает работать** на старых данных из CSV |
| 🟡 **Изменился формат CSV** | Ты правишь **только логику импорта** (например, в `import_csv.py`), не трогая `OddsService` |
| 🟢 **Хочешь сменить букмекера** | Ты правишь **только один параметр** в `OddsService`, и вся система **мгновенно подхватывает** новые данные |

---

## 7. Золотое правило «Статика + Динамика»

Твой дашборд сейчас показывает **«Валуйную ставку»**.

С точки зрения архитектуры, это означает, что в твоём представлении (`views.py`) происходит **джойн** (объединение):

1. Берётся `MatchStat` (**имя команды из CSV**).
2. К нему привязывается `MatchOdds` (**коэффициент из API**).
3. Вычисляется:

```text
Value = (Вероятность × Кэф) − 1
```

---

## 8. Твой профессиональный план действий

Поскольку ты теперь **мастер архитектуры**, давай закрепим **«железный»** порядок работы с файлами:

| Файл | Правило |
|---|---|
| 📁 `sports_data/services.py` | Здесь живут твои **«чистые» функции**. **Никакого `self.stdout.write`** — только обработка данных и возврат результата |
| 📁 `sports_data/management/commands/` | Здесь живут **«тонкие» команды-обёртки**. Они просто **вызывают нужный сервис** из `services.py` и выводят пользователю результат (**Success** или **Error**) |
| 📥 **Импорт CSV** | Сейчас это твой **самый важный процесс**. Раз он даёт **имена команд**, от которых зависит работа `OddsService` (поиск через `icontains`), важно, чтобы **имена в CSV были максимально близки** к стандартам, которые ты видишь в The Odds API |

---

> 💬 Ты построил **движок**, который готов к **любой лиге мира**.
> Теперь, когда ты загрузишь свой CSV (например, MLS), просто прогони через `OddsService` — и если **названия в CSV и API совпадают**, твои **«Валуйные ставки»** станут **абсолютно реальными и применимыми в жизни**.

> 💡 У тебя есть все файлы для **«Фурора»**.
> Если что-то не будет матчиться в поиске — пиши, мы добавим в `services.py` **«словарь синонимов»** (мап), чтобы связывать, например, `Man United` и `Manchester United` **навсегда**.

---

<div align="center">

**Архитектурный кейс: Разделение ответственности в Sports Trading Bot**

`Django` · `PostgreSQL` · `StatsService` · `OddsService` · `Decoupling` · `Масштабируемость`

</div>