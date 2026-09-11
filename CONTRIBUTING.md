<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                    CONTRIBUTING.md                             -->
<!-- ═══════════════════════════════════════════════════════════════ -->

<div align="center">

# 🤝 Contributing to Sports Trading Bot

**Спасибо, что хотите помочь проекту!** ❤️

Мы приветствуем любой вклад — от исправления опечаток до новых модулей.

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=for-the-badge)](http://makeapullrequest.com)
[![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg?style=for-the-badge)](./CODE_OF_CONDUCT.md)
[![Discussions](https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github)](../../discussions)

</div>

---

## 📑 Содержание

- [Кодекс поведения](#-кодекс-поведения)
- [Способы внести вклад](#-способы-внести-вклад)
- [Настройка окружения](#-настройка-окружения)
- [Процесс работы с Git](#-процесс-работы-с-git)
- [Стандарты кода](#-стандарты-кода)
- [Тестирование](#-тестирование)
- [Документация](#-документация)
- [Процесс Pull Request](#-процесс-pull-request)
- [Сообщение об ошибках](#-сообщение-об-ошибках)
- [Предложение новых функций](#-предложение-новых-функций)
- [Вопросы и обсуждения](#-вопросы-и-обсуждения)

---

## 🌟 Кодекс поведения

Проект следует **[Contributor Covenant v2.1](./CODE_OF_CONDUCT.md)**.

**Кратко:**
- Будьте вежливы и уважительны.
- Никаких оскорблений, дискриминации, токсичности.
- Конструктивная критика — приветствуется, деструктивная — нет.
- Технические споры — по существу, без перехода на личности.

Нарушения → письмо на `conduct@your-project.com` (замени на свой).

---

## 💡 Способы внести вклад

| Тип вклада | Сложность | Как начать |
|---|---|---|
| 🐛 **Исправить баг** | 🟢 Легко | [Issues с меткой `bug`](../../issues?q=is%3Aissue+is%3Aopen+label%3Abug) |
| 📝 **Улучшить документацию** | 🟢 Легко | [Issues с меткой `documentation`](../../issues?q=is%3Aissue+is%3Aopen+label%3Adocumentation) |
| ✨ **Добавить фичу** | 🟡 Средне | [Issues с меткой `enhancement`](../../issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) |
| 🧪 **Написать тесты** | 🟡 Средне | [Issues с меткой `tests`](../../issues?q=is%3Aissue+is%3Aopen+label%3Atests) |
| 🧠 **Новый AI-модуль** | 🔴 Сложно | [Issues с меткой `ai`](../../issues?q=is%3Aissue+is%3Aopen+label%3Aai) |
| 👁 **YOLO-интеграция** | 🔴 Сложно | [Issues с меткой `vision`](../../issues?q=is%3Aissue+is%3Aopen+label%3Avision) |

### 🎯 Хорошие точки входа для новичков

Ищите Issues с меткой **[`good first issue`](../../issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22)** — они специально подобраны для новых контрибьюторов.

---

## 🛠 Настройка окружения

### 1. Форк и клонирование

```bash
# Форкните репозиторий через GitHub UI, затем:
git clone https://github.com/YOUR-USERNAME/sports-trading-bot.git
cd sports-trading-bot

# Добавьте upstream, чтобы синхронизироваться с оригиналом
git remote add upstream https://github.com/ORIGINAL-OWNER/sports-trading-bot.git
```

### 2. Виртуальное окружение

```bash
# Создаём venv
python -m venv venv

# Активируем
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

### 3. Зависимости

```bash
# Основные
pip install -r requirements/base.txt

# Для разработки (линтеры, тесты, pre-commit)
pip install -r requirements/dev.txt
```

### 4. Переменные окружения

```bash
cp .env.example .env
# Отредактируйте .env:
#   - DATABASE_URL
#   - DEEPSEEK_API_KEY (для тестов — можно mock)
#   - GEMINI_API_KEY
#   - OPENAI_API_KEY
```

### 5. Docker (рекомендуется)

```bash
docker-compose up -d --build

# Проверка
docker-compose ps
```

### 6. Pre-commit hooks (обязательно!)

```bash
pre-commit install
```

Теперь при каждом коммите автоматически запускаются **линтеры, форматтеры и тесты**.

---

## 🌿 Процесс работы с Git

### Стратегия ветвления

Мы используем **GitHub Flow**:

```text
main ────●────────●────────●──────►  (production-ready)
          \      /        /
           ●────●        /            (feature branches)
                \      /
                 ●────●
```

- **`main`** — всегда стабильная, production-ready.
- **Ветки для фич** — создаются от `main`, живут недолго.

### Именование ветвей

| Тип | Формат | Пример |
|---|---|---|
| ✨ Фича | `feature/short-description` | `feature/clv-tracking` |
| 🐛 Багфикс | `fix/short-description` | `fix/team-name-mapping` |
| 📝 Документация | `docs/short-description` | `docs/yolo-guide` |
| ♻️ Рефакторинг | `refactor/short-description` | `refactor/odds-service` |
| 🧪 Тесты | `test/short-description` | `test/math-engine` |
| 🔧 Chore | `chore/short-description` | `chore/update-deps` |

### Создание ветки

```bash
# Синхронизация с upstream
git checkout main
git pull upstream main

# Создание ветки
git checkout -b feature/my-awesome-feature
```

### Коммиты — Conventional Commits

Мы используем **[Conventional Commits](https://www.conventionalcommits.org/)**.

**Формат:**
```text
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Типы:**

| Тип | Когда использовать |
|---|---|
| `feat` | Новая функция |
| `fix` | Исправление бага |
| `docs` | Изменения в документации |
| `style` | Форматирование (не меняет логику) |
| `refactor` | Рефакторинг |
| `perf` | Улучшение производительности |
| `test` | Добавление/исправление тестов |
| `chore` | Обновление зависимостей, конфигов |
| `ci` | Изменения в CI/CD |

**Примеры:**

```bash
# ✅ Хорошо
git commit -m "feat(math-engine): add ELO rating integration"
git commit -m "fix(odds-service): handle empty bookmakers list"
git commit -m "docs(readme): update quick start section"
git commit -m "test(analyzer): add unit tests for voting logic"

# ❌ Плохо
git commit -m "fixed stuff"
git commit -m "update"
git commit -m "WIP"
```

---

## 🎨 Стандарты кода

### Python

| Инструмент | Назначение | Конфиг |
|---|---|---|
| **Black** | Форматирование | `pyproject.toml` |
| **isort** | Сортировка импортов | `pyproject.toml` |
| **flake8** | Линтинг | `setup.cfg` |
| **mypy** | Типизация | `mypy.ini` |
| **pylint** | Дополнительный линт | `.pylintrc` |

### Стиль кода

```python
# ✅ Хорошо
class OddsService:
    """Сервис для работы с коэффициентами из The Odds API."""

    TIMEOUT: int = 30

    @classmethod
    def sync_odds(cls, league_key: str) -> int:
        """
        Синхронизирует коэффициенты для указанной лиги.

        Args:
            league_key: Ключ лиги (например, 'soccer_usa_mls').

        Returns:
            Количество обновлённых матчей.
        """
        ...
```

**Правила:**
- ✅ Type hints **обязательны** для публичных функций.
- ✅ Docstring в формате **Google** — обязателен.
- ✅ Максимальная длина строки — **100 символов**.
- ✅ Функции — **не более 50 строк**, классы — не более **300**.
- ✅ Имена: `snake_case` для функций/переменных, `PascalCase` для классов, `UPPER_CASE` для констант.
- ❌ Никаких `print()` в production-коде — только `logging`.
- ❌ Никаких «магических чисел» — выносите в константы.

### Форматирование перед коммитом

```bash
# Автоформат
black .
isort .

# Проверка
flake8 .
mypy apps/
```

Или одной командой:
```bash
make format
make lint
```

### SQL / Django

- ✅ Используйте `select_related` и `prefetch_related` — **избегайте N+1**.
- ✅ Индексы — на поля, по которым фильтруете.
- ✅ Миграции — **никогда не редактируйте** после merge.
- ❌ Никаких raw SQL в бизнес-логике — только через ORM.

### JavaScript / HTML / CSS

- ✅ **Bootstrap 5** для UI.
- ✅ Никакого инлайн-JS — только в `<script>`.
- ✅ Комментарии — на русском или английском (единообразно).

---

## 🧪 Тестирование

### Структура тестов

```text
tests/
├── unit/
│   ├── test_math_engine.py
│   ├── test_analyzer.py
│   └── test_odds_service.py
├── integration/
│   ├── test_update_odds.py
│   └── test_telegram_notify.py
├── load/
│   └── test_concurrency.py
└── conftest.py
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=apps --cov-report=html

# Конкретный файл
pytest tests/unit/test_math_engine.py -v

# Только быстрые (без integration)
pytest -m "not integration"
```

### Что тестировать обязательно

- ✅ **MathEngine** — все формулы (Пуассон, Kelly, Value).
- ✅ **Analyzer** — логика голосования и агрегации.
- ✅ **OddsService** — парсинг ответов, нормализация имён команд.
- ✅ **LLM Clients** — обработка ошибок, таймаутов, невалидного JSON.
- ✅ **Django Models** — методы, свойства, валидация.

### Что можно не тестировать

- ⚪ Django admin.
- ⚪ Тривиальные getters/setters.
- ⚪ Конфигурационные файлы.

### Покрытие

- 🎯 **Минимум:** 60% (ниже — PR не пройдёт).
- 🎯 **Цель:** 80%+ для критичных модулей (`math_engine`, `analyzer`).

### Пример теста

```python
# tests/unit/test_math_engine.py
import pytest
from core.math_engine import MathEngine


class TestMathEngine:
    def test_poisson_probabilities_sum_to_one(self):
        """Сумма вероятностей всех исходов должна быть равна 1."""
        engine = MathEngine()
        probs = engine.calculate_probabilities(
            home_attack=1.5,
            away_attack=1.2,
            home_defence=1.0,
            away_defence=1.1,
        )
        total = probs["home"] + probs["draw"] + probs["away"]
        assert abs(total - 1.0) < 0.001

    @pytest.mark.parametrize("prob,odds,expected", [
        (0.5, 2.0, 0.0),    # безубыток
        (0.6, 2.0, 0.2),    # выгодно
        (0.4, 2.0, -0.2),   # невыгодно
    ])
    def test_calculate_value(self, prob, odds, expected):
        """Проверка формулы Value = (P × Odds) − 1."""
        engine = MathEngine()
        value = engine.calculate_value(prob, odds)
        assert abs(value - expected) < 0.001
```

---

## 📖 Документация

### Где что лежит

```text
docs/
├── 00-case-sports-trading-bot.md      # Обзор проекта
├── 01-architecture.md                  # Архитектура
├── 02-data-collection.md               # Сбор данных
├── ...
└── 15-analytics-module-full.md         # AI-модуль (полный)
```

### Требования к документации

- ✅ Каждый **новый модуль** → отдельный `.md` в `docs/`.
- ✅ Каждая **новая фича** → обновить или создать раздел в документации.
- ✅ Заголовки — **на русском**, код и имена — **на английском**.
- ✅ **Слово в слово** — не переписывайте смысл, только улучшайте оформление.
- ✅ **Диаграммы** — Mermaid (рендерится на GitHub).
- ✅ **Примеры кода** — обязательно рабочие.

### Стиль документации

- Начинайте с **«Зачем это нужно»** — мотивация, потом детали.
- Используйте **таблицы** для сравнений.
- `<details>` для **сворачиваемых** блоков кода.
- **Callout-блоки** для важного:

```markdown
> 💡 **Совет:** ...
> ⚠️ **Важно:** ...
> 🛑 **Внимание:** ...
```

### Обновление README

Если вы добавляете новую крупную фичу — **обязательно** обновите:
- раздел [**Roadmap**](./README.md#-roadmap) в README,
- раздел [**Документация**](./README.md#-документация) — добавьте ссылку на новый кейс.

---

## 📤 Процесс Pull Request

### Чек-лист перед PR

- [ ] Ветка создана от **свежего `main`**.
- [ ] Все тесты проходят: `pytest`.
- [ ] Линтеры не ругаются: `make lint`.
- [ ] Код отформатирован: `make format`.
- [ ] Type hints добавлены ко всем публичным функциям.
- [ ] Docstrings написаны (формат Google).
- [ ] Обновлена документация (если нужно).
- [ ] Обновлён `CHANGELOG.md` (если есть).
- [ ] Нет конфликтов с `main`.

### Создание PR

```bash
# Синхронизация перед PR
git fetch upstream
git rebase upstream/main

# Пуш
git push origin feature/my-awesome-feature
```

Затем в GitHub UI → **New Pull Request**.

### Шаблон PR

```markdown
## 📌 Что сделано

Краткое описание изменений.

## 🎯 Зачем

Ссылка на Issue: `Closes #123`

## 🔧 Как тестировать

```bash
pytest tests/unit/test_new_feature.py
```

## 📸 Скриншоты / примеры

(если применимо)

## ✅ Чек-лист

- [ ] Тесты проходят
- [ ] Линтеры чистые
- [ ] Документация обновлена
- [ ] Нет breaking changes
```

### Review Process

1. **Автоматические проверки:** CI (GitHub Actions) — тесты, линтеры, coverage.
2. **Ревью мейнтейнера:** минимум 1 approve.
3. **Правки:** по комментариям — доп. коммиты в ту же ветку.
4. **Merge:** squash-and-merge (если много мелких коммитов) или rebase.
5. **Удаление ветки:** автоматически после merge.

### Время ревью

- 🟢 Маленькие PR (< 100 строк) — **1–2 дня**.
- 🟡 Средние (100–500) — **2–5 дней**.
- 🔴 Большие (500+) — **до недели** (лучше дробить!).

---

## 🐛 Сообщение об ошибках

### Перед созданием Issue

1. Проверьте **существующие Issues** — возможно, уже есть.
2. Обновите до **последней `main`** — вдруг уже исправлено.
3. Проверьте **документацию** — может, это не баг, а by design.

### Шаблон баг-репорта

```markdown
## 🐛 Описание

Что происходит не так.

## 🔁 Воспроизведение

1. Запускаю `python manage.py update_odds --league=soccer_epl`
2. Жду 30 секунд
3. Получаю ошибку `KeyError: 'bookmakers'`

## 🎯 Ожидаемое поведение

Команда должна обновить коэффициенты без ошибок.

## 📸 Скриншоты / логи

```text
Traceback (most recent call last):
  File "...", line 42, in sync_odds
    bookmark = next(...)
KeyError: 'bookmakers'
```

## 🖥 Окружение

- OS: Ubuntu 22.04
- Python: 3.10.12
- Docker: 24.0.5
- Project version: `main@abc1234`

## 📎 Дополнительный контекст

Возможно, связано с #42.
```

### Метки Issues

| Метка | Значение |
|---|---|
| `bug` | Баг |
| `enhancement` | Новая фича |
| `documentation` | Проблема с докой |
| `good first issue` | Для новичков |
| `help wanted` | Нужна помощь |
| `wontfix` | Не будет исправлено |
| `duplicate` | Дубликат |
| `priority: high` | Срочно |

---

## ✨ Предложение новых функций

### Обсуждение перед реализацией

**Сначала** создайте **Issue** с меткой `enhancement`, чтобы обсудить фичу. Это **сэкономит время** вам и мейнтейнерам.

### Шаблон Feature Request

```markdown
## ✨ Что предлагаете

Краткое описание фичи.

## 🎯 Проблема, которую решает

Какую боль закрывает? Например: «Сейчас нет CLV-трекинга, поэтому сложно оценить реальное преимущество».

## 💡 Возможная реализация

- Добавить модель `ClosingLine`
- Записывать финальный коэффициент перед стартом матча
- Считать CLV = (bet_odds / closing_odds) − 1
- Отображать в дашборде

## 🔀 Альтернативы

Можно использовать внешний сервис, но это дороже.

## 📸 Скриншоты / примеры

(если есть)

## 🏷 Приоритет

Средний.
```

---

## 💬 Вопросы и обсуждения

- 💬 **GitHub Discussions** — для общих вопросов.
- 🐛 **GitHub Issues** — для багов и фич.
- 📧 **Email** — для приватных вопросов: `maintainer@your-project.com`.
- 💌 **Telegram** — [@your_project_chat](https://t.me/your_project_chat).

### Что где спрашивать

| Тема | Куда |
|---|---|
| «Как настроить X?» | Discussions → Q&A |
| «Нашёл баг» | Issues → Bug Report |
| «Хочу фичу Y» | Issues → Feature Request |
| «Помогите с кодом» | Discussions → Help |
| «Хочу поучаствовать» | Issues → `good first issue` |

---

## 🎉 Спасибо!

<div align="center">

**Каждый вклад — большой или маленький — делает проект лучше.**

Спасибо, что вы с нами! ❤️

---

**Авторы проекта** собираются здесь: [Contributors](../../graphs/contributors)

</div>

---

<div align="center">

[⬆ Наверх](#-contributing-to-sports-trading-bot)

</div>

<!-- ═══════════════════════════════════════════════════════════════ -->
<!--                    END OF CONTRIBUTING.md                      -->
<!-- ═══════════════════════════════════════════════════════════════ -->