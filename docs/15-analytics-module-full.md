# 🧠 ПОЛНЫЙ КЕЙС: Работа модуля аналитики «Информатор»

> **Django** · **DRF** · **PostgreSQL** · **Redis** · **Docker** · **DeepSeek** · **Gemini** · **ChatGPT** · **Multi-DB**

**Флагманский документ проекта.** Полный цикл работы модуля — от запроса пользователя до выдачи готового решения. Каждый шаг с объяснением **«почему именно так»**.

---

## 📑 Содержание

### Часть I. Логика модуля
- [1. Архитектура системы](#1-архитектура-системы)
- [2. Подготовка данных](#2-подготовка-данных)
- [3. Формирование промтов](#3-формирование-промтов)
- [4. Параллельные запросы к ИИ](#4-параллельные-запросы-к-ии)
- [5. Парсинг и валидация ответов](#5-парсинг-и-валидация-ответов)
- [6. Анализ и принятие решения](#6-анализ-и-принятие-решения)
- [7. Кэширование и хранение](#7-кэширование-и-хранение)

### Часть II. Docker-контейнеризация
- [8. Структура проекта](#8-структура-проекта)
- [9. Docker-контейнеризация модуля](#9-docker-контейнеризация-модуля)
- [10. Собственная база данных модуля](#10-собственная-база-данных-модуля)
- [11. Интеграция с основным проектом](#11-интеграция-с-основным-проектом)
- [12. Настройка переменных окружения](#12-настройка-переменных-окружения)
- [13. Запуск и тестирование](#13-запуск-и-тестирование)
- [14. Мониторинг и логирование](#14-мониторинг-и-логирование)

---
---

# Часть I. Логика модуля

---

## 1. Архитектура системы

### 1.1. Общая схема

```text
┌─────────────────────────────────────────────────────────────────┐
│                       ПОЛЬЗОВАТЕЛЬ                              │
│                   (API запрос / Admin)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DJANGO (WEB LAYER)                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API View / Management Command                           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                   ANALYTICS MODULE                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  1. Проверка кэша (Redis)                                │   │
│  │  2. Сбор данных матча из БД                              │   │
│  │  3. Формирование 3 промтов (для каждой модели)           │   │
│  │  4. Параллельные запросы к API ИИ                        │   │
│  │  5. Парсинг и валидация JSON-ответов                     │   │
│  │  6. Логика принятия решения (голосование)                │   │
│  │  7. Сохранение в БД (история)                            │   │
│  │  8. Кэширование результата                               │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  DeepSeek   │  │   Gemini    │  │  ChatGPT    │
│    API      │  │    API      │  │    API      │
└─────────────┘  └─────────────┘  └─────────────┘
```

### 1.2. Почему такая архитектура?

| Решение | Причина |
|---|---|
| **Синхронный запрос** | Для «информатора» не нужна асинхронность — пользователь ждёт ответ **5–10 секунд** |
| **Параллельные запросы** | Экономит время (3 запроса выполняются **одновременно**, а не последовательно) |
| **Кэширование** | Один матч анализируется **1 раз в час** — экономия API-запросов |
| **Сохранение истории** | **Аудит**, возможность сравнивать **точность моделей** |
| **Отсутствие шлюза** | Экономия на комиссии (**5–10%**), полный контроль над промтами |

---

## 2. Подготовка данных

### 2.1. Что происходит на этом этапе

```python
# analytics/services/data_preparer.py

class DataPreparer:
    @staticmethod
    def prepare_match_data(match_id: int) -> Dict:
        """Извлекает данные матча из БД и преобразует в словарь"""

        # ШАГ 1: Загрузка из БД
        match = Match.objects.select_related(
            'home_team', 'away_team', 'tournament'
        ).get(id=match_id)

        # ШАГ 2: Сбор всей необходимой информации
        match_data = {
            'match_id': match.id,
            'home_team': match.home_team.name,
            'away_team': match.away_team.name,
            'tournament': match.tournament.name,
            'odds_over': match.odds_over,      # Коэффициент на ТБ(2.5)
            'odds_under': match.odds_under,    # Коэффициент на ТМ(2.5)
            'match_date': match.date.strftime('%d.%m.%Y'),
            'match_time': match.time.strftime('%H:%M') if match.time else 'N/A',
        }

        # ШАГ 3: Дополнительные данные (если есть)
        # Травмы, дисквалификации, статистика
        if hasattr(match, 'injuries'):
            match_data['injuries'] = match.injuries

        # ШАГ 4: Статистика последних матчей (опционально)
        # Здесь можно подтянуть данные из внешнего API (Football-Data.org и т.д.)

        return match_data
```

### 2.2. Почему это важно?

| Шаг | Почему |
|---|---|
| **`select_related`** | Оптимизация SQL — **одна операция вместо 4-х** (JOIN с командами и турниром) |
| **Преобразование дат** | **Человекочитаемый формат** для ИИ (модели лучше понимают структурированные данные) |
| **Дополнительные данные** | ИИ может использовать их для **более точного прогноза** |

### 2.3. Пример данных, которые передаются в ИИ

```python
{
    'home_team': 'Спартак М',
    'away_team': 'Оренбург',
    'tournament': 'РПЛ',
    'odds_over': 1.55,
    'odds_under': 2.35,
    'match_date': '30.08.2026',
    'match_time': '19:00',
    'injuries': 'У Спартака травмированы: Промес, Соболев'
}
```

---

## 3. Формирование промтов

### 3.1. Почему мы используем промты, а не просто отправляем данные

**ИИ-модели — это не базы данных.** Они не умеют просто «посмотреть» на данные. Им нужна **инструкция**:

1. **Что анализировать** (конкретные данные матча).
2. **Как анализировать** (методология, факторы).
3. **Как отвечать** (структура ответа, формат).

### 3.2. Подробный разбор структуры промта

```python
def build_prompt(match_data: Dict) -> str:
    """
    ПОЧЕМУ ТАКАЯ СТРУКТУРА?

    1. РОЛЬ (System): Задает экспертный уровень → ответы становятся профессиональнее
    2. КОНТЕКСТ (Данные матча): Четкая структура → модель понимает, что важно
    3. МЕТОДОЛОГИЯ (Факторы): Направляет мышление модели в нужное русло
    4. ФОРМАТ (JSON): Гарантирует, что ответ можно будет обработать программно
    """

    return f"""
РОЛЬ: Ты профессиональный футбольный аналитик с 10-летним опытом.
Специализация: прогнозирование тоталов голов.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ДАННЫЕ ДЛЯ АНАЛИЗА:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Турнир: {match_data['tournament']}
Матч: {match_data['home_team']} vs {match_data['away_team']}
Коэффициент на ТБ (2.5): {match_data['odds_over']}
Коэффициент на ТМ (2.5): {match_data['odds_under']}
{additional_info if additional_info else ''}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
МЕТОДОЛОГИЯ АНАЛИЗА (используй все пункты):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Оцени текущую форму: как играют команды в последних 5 матчах
2. Проанализируй личные встречи: есть ли тренд на ТБ или ТМ
3. Учти мотивацию: борьба за место в таблице, кубковые задачи
4. Оцени тактику: атакующий или оборонительный стиль
5. Учти кадровые потери (если указаны)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ТРЕБОВАНИЯ К ОТВЕТУ:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ответь ТОЛЬКО в формате JSON (без дополнительного текста):

{{
    "analysis": "краткий анализ матча (2-3 предложения)",
    "recommended_bet": "ТБ (2.5)" или "ТМ (2.5)",
    "odds": числовое значение коэффициента,
    "confidence": число от 0.00 до 1.00 (уверенность),
    "key_factors": ["фактор1", "фактор2", "фактор3"]
}}

⚠️ ВНИМАНИЕ: Убедись, что ответ является валидным JSON!
"""
```

### 3.3. Почему важен JSON-формат

```text
БЕЗ JSON:
"Я думаю, что в этом матче будет много голов, так как Спартак играет дома
и Оренбург плохо защищается. Поэтому я рекомендую ТБ (2.5)."

С JSON:
{"analysis": "...", "recommended_bet": "ТБ (2.5)", "odds": 1.55, "confidence": 0.75}
```

> 💡 **Проблема:** Первый ответ **нельзя обработать автоматически**.
> **Решение:** JSON даёт **структуру**, которую можно **парсить**.

---

## 4. Параллельные запросы к ИИ

### 4.1. Полный код параллельных запросов

```python
# analytics/services/llm_clients.py

import httpx
import asyncio
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class LLMClients:
    """Клиент для параллельных запросов к 3 ИИ-моделям"""

    # Таймауты для каждой модели (в секундах)
    TIMEOUTS = {
        'deepseek': 30,
        'gemini': 35,
        'chatgpt': 25
    }

    @classmethod
    async def _call_deepseek(cls, prompt: str) -> Dict:
        """Асинхронный вызов DeepSeek"""
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUTS['deepseek']) as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "Ты эксперт по футболу. Отвечай только JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,  # Низкая температура = более детерминированные ответы
                        "max_tokens": 400,
                        "top_p": 0.9
                    }
                )

                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.status_code} - {response.text}")
                    return cls._error_response("API error")

                result = response.json()
                content = result['choices'][0]['message']['content']
                return cls._parse_json_response(content, 'deepseek')

        except httpx.TimeoutException:
            logger.error("DeepSeek timeout")
            return cls._error_response("Timeout")
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            return cls._error_response(str(e))

    @classmethod
    async def _call_gemini(cls, prompt: str) -> Dict:
        """Асинхронный вызов Gemini"""
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUTS['gemini']) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={settings.GEMINI_API_KEY}",
                    json={
                        "contents": [{
                            "parts": [{"text": f"Ты эксперт по футболу. Ответь ТОЛЬКО в формате JSON. {prompt}"}]
                        }],
                        "generationConfig": {
                            "temperature": 0.3,
                            "maxOutputTokens": 400
                        }
                    }
                )

                if response.status_code != 200:
                    logger.error(f"Gemini API error: {response.status_code}")
                    return cls._error_response("API error")

                result = response.json()
                text = result['candidates'][0]['content']['parts'][0]['text']
                return cls._parse_json_response(text, 'gemini')

        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return cls._error_response(str(e))

    @classmethod
    async def _call_chatgpt(cls, prompt: str) -> Dict:
        """Асинхронный вызов ChatGPT"""
        try:
            async with httpx.AsyncClient(timeout=cls.TIMEOUTS['chatgpt']) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",  # Дешевая и быстрая модель
                        "messages": [
                            {"role": "system", "content": "Ты эксперт по футболу. Отвечай только JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 400
                    }
                )

                if response.status_code != 200:
                    logger.error(f"ChatGPT API error: {response.status_code}")
                    return cls._error_response("API error")

                result = response.json()
                content = result['choices'][0]['message']['content']
                return cls._parse_json_response(content, 'chatgpt')

        except Exception as e:
            logger.error(f"ChatGPT error: {e}")
            return cls._error_response(str(e))

    @classmethod
    def _error_response(cls, error: str) -> Dict:
        """Стандартный ответ при ошибке"""
        return {
            'status': 'error',
            'recommended_bet': 'Ошибка',
            'odds': 0,
            'confidence': 0,
            'analysis': f"Ошибка: {error}"
        }

    @classmethod
    def _parse_json_response(cls, text: str, provider: str) -> Dict:
        """Извлекает JSON из ответа модели"""
        try:
            # Ищем первый { и последний }
            start = text.find('{')
            end = text.rfind('}') + 1

            if start == -1 or end == 0:
                logger.warning(f"No JSON found in {provider} response: {text[:100]}")
                return cls._error_response("No JSON found")

            json_str = text[start:end]
            data = json.loads(json_str)

            # Проверяем обязательные поля
            required_fields = ['recommended_bet', 'odds', 'confidence']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing field '{field}' in {provider} response")
                    data[field] = 0 if field != 'recommended_bet' else 'Не определено'

            # Нормализуем названия ставок
            if 'ТБ' in data['recommended_bet'] or 'over' in data['recommended_bet'].lower():
                data['recommended_bet'] = 'ТБ (2.5)'
            elif 'ТМ' in data['recommended_bet'] or 'under' in data['recommended_bet'].lower():
                data['recommended_bet'] = 'ТМ (2.5)'

            data['status'] = 'success'
            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in {provider}: {e}\nText: {text[:200]}")
            return cls._error_response("Invalid JSON")
        except Exception as e:
            logger.error(f"Parse error in {provider}: {e}")
            return cls._error_response(str(e))

    @classmethod
    async def get_all_predictions_async(cls, match_data: Dict) -> Dict:
        """Запускает параллельные запросы ко всем трем моделям"""

        prompt = cls._build_prompt(match_data)

        tasks = [
            cls._call_deepseek(prompt),
            cls._call_gemini(prompt),
            cls._call_chatgpt(prompt)
        ]

        # asyncio.gather() выполняет все задачи параллельно
        # return_exceptions=True — не прерывает выполнение при ошибке одной из задач
        results = await asyncio.gather(*tasks, return_exceptions=True)

        providers = ['deepseek', 'gemini', 'chatgpt']
        predictions = {}

        for provider, result in zip(providers, results):
            if isinstance(result, Exception):
                predictions[provider] = {
                    'status': 'error',
                    'recommended_bet': 'Ошибка',
                    'odds': 0,
                    'confidence': 0,
                    'analysis': f"Exception: {str(result)}"
                }
            else:
                predictions[provider] = result

        return predictions

    @classmethod
    def _build_prompt(cls, match_data: Dict) -> str:
        """Формирует промт из данных матча"""
        # ... (код из предыдущего раздела)
        return prompt
```

### 4.2. Почему параллельные запросы?

```text
ПОСЛЕДОВАТЕЛЬНЫЕ ЗАПРОСЫ:
DeepSeek (5с) → Gemini (5с) → ChatGPT (5с) = 15 секунд

ПАРАЛЛЕЛЬНЫЕ ЗАПРОСЫ:
DeepSeek ┐
Gemini   ├─ 5 секунд (все одновременно)
ChatGPT  ┘

ЭКОНОМИЯ: 15с → 5с (в 3 раза быстрее)
```

### 4.3. Почему разные таймауты?

```python
TIMEOUTS = {
    'deepseek': 30,  # Может быть медленнее из-за географии (Китай)
    'gemini': 35,    # Иногда долго обрабатывает
    'chatgpt': 25    # Самый быстрый
}
```

> 💡 **Причина:** У разных провайдеров **разное время ответа**. Если поставить одинаковый таймаут, можно получить **ложные срабатывания**.

---

## 5. Парсинг и валидация ответов

### 5.1. Почему нужен парсинг?

ИИ-модели иногда:

- Добавляют **пояснения вне JSON** (`"Вот мой анализ: {...}"`).
- Используют **нестандартные названия** (`"Over"` вместо `"ТБ"`).
- **Пропускают поля** или добавляют лишние.
- Выдают **невалидный JSON**.

### 5.2. Алгоритм парсинга

```python
def parse_llm_response(text: str, provider: str) -> Dict:
    """
    АЛГОРИТМ:
    1. Найти JSON в тексте
    2. Попытаться распарсить
    3. Если не получилось — попытаться исправить
    4. Валидация обязательных полей
    5. Нормализация значений
    """

    # ШАГ 1: Найти JSON
    start = text.find('{')
    end = text.rfind('}') + 1

    if start == -1 or end == 0:
        # Попытка найти JSON в обратных кавычках
        import re
        json_pattern = r'```json\n(.*?)\n```'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            return error_response("No JSON found")
    else:
        json_str = text[start:end]

    # ШАГ 2: Попытка парсинга
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        # Попытка исправить распространенные ошибки
        # Например: замена одинарных кавычек на двойные
        try:
            import ast
            data = ast.literal_eval(json_str)
        except:
            return error_response("Invalid JSON")

    # ШАГ 3: Валидация
    required_fields = ['recommended_bet', 'odds', 'confidence']
    for field in required_fields:
        if field not in data:
            data[field] = get_default_value(field)

    # ШАГ 4: Нормализация значений
    # Приводим названия ставок к единому формату
    bet = data['recommended_bet'].lower()
    if 'тб' in bet or 'over' in bet or 'bolshe' in bet:
        data['recommended_bet'] = 'ТБ (2.5)'
    elif 'тм' in bet or 'under' in bet or 'menshe' in bet:
        data['recommended_bet'] = 'ТМ (2.5)'
    else:
        data['recommended_bet'] = 'Не определено'

    # Конвертируем confidence в float (0-1)
    try:
        confidence = float(data['confidence'])
        data['confidence'] = max(0, min(1, confidence))  # Ограничиваем диапазон
    except:
        data['confidence'] = 0.0

    # Конвертируем odds в float
    try:
        data['odds'] = float(data['odds'])
    except:
        data['odds'] = 0.0

    data['status'] = 'success'
    return data
```

### 5.3. Почему важен fallback при ошибках?

```python
def get_all_predictions_safe(match_data: Dict) -> Dict:
    """
    ПРИНЦИП: Даже если одна модель упала, мы все равно получаем
    прогнозы от двух других.
    """
    predictions = {}

    # Пробуем DeepSeek
    try:
        predictions['deepseek'] = call_deepseek(match_data)
    except Exception as e:
        predictions['deepseek'] = error_response(str(e))
        # Логируем ошибку, но продолжаем работу

    # Пробуем Gemini
    try:
        predictions['gemini'] = call_gemini(match_data)
    except Exception as e:
        predictions['gemini'] = error_response(str(e))

    # Пробуем ChatGPT
    try:
        predictions['chatgpt'] = call_chatgpt(match_data)
    except Exception as e:
        predictions['chatgpt'] = error_response(str(e))

    return predictions
```

> 💡 **Почему:** Если одна модель упала, мы всё равно можем принять решение **на основе двух других**.

---

## 6. Анализ и принятие решения

### 6.1. Полный код анализатора

```python
# analytics/services/analyzer.py

from typing import Dict, List, Tuple
from decimal import Decimal
import statistics
import logging

logger = logging.getLogger(__name__)


class MatchAnalyzer:
    """
    АНАЛИЗАТОР: Сравнивает прогнозы трех ИИ и принимает решение

    АЛГОРИТМ ПРИНЯТИЯ РЕШЕНИЯ:
    1. Голосование: выбираем ставку, за которую проголосовало большинство
    2. Если голоса разделились (1-1-1) → смотрим на уверенность
    3. Расчет Expected Value (EV) для проверки рентабельности
    4. Генерация человекочитаемого отчета
    """

    @staticmethod
    def analyze(predictions: Dict[str, Dict]) -> Dict:
        """
        Принимает словарь с прогнозами от трех моделей.
        Возвращает итоговое решение.
        """

        # ШАГ 1: Собираем все валидные прогнозы
        valid_predictions = []
        for model_name, pred in predictions.items():
            if (pred.get('status') == 'success'
                    and pred.get('recommended_bet') not in ['Ошибка', 'Не определено']):
                valid_predictions.append({
                    'model': model_name,
                    'bet': pred['recommended_bet'],
                    'odds': pred.get('odds', 0),
                    'confidence': pred.get('confidence', 0),
                    'analysis': pred.get('analysis', '')
                })

        # Если нет валидных прогнозов → ошибка
        if not valid_predictions:
            return {
                'status': 'error',
                'message': 'Нет валидных прогнозов от ИИ-моделей',
                'recommended_bet': None
            }

        # ШАГ 2: Голосование
        votes = {}
        for pred in valid_predictions:
            bet = pred['bet']
            if bet not in votes:
                votes[bet] = {
                    'count': 0,
                    'confidences': [],
                    'odds': [],
                    'models': [],
                    'analyses': []
                }
            votes[bet]['count'] += 1
            votes[bet]['confidences'].append(pred['confidence'])
            votes[bet]['odds'].append(pred['odds'])
            votes[bet]['models'].append(pred['model'])
            votes[bet]['analyses'].append(pred['analysis'])

        # ШАГ 3: Выбор победителя
        # Критерии: 1) Больше голосов, 2) Выше средняя уверенность
        best_bet = max(votes.items(), key=lambda x: (
            x[1]['count'],
            statistics.mean(x[1]['confidences'])
        ))

        bet_name, data = best_bet

        # ШАГ 4: Расчет средних значений
        avg_confidence = statistics.mean(data['confidences'])
        avg_odds = statistics.mean(data['odds'])

        # ШАГ 5: Расчет Expected Value (EV)
        # EV = (вероятность * коэффициент) - 1
        # Если EV > 0, ставка рентабельна в долгосрочной перспективе
        probability = avg_confidence
        ev = (probability * avg_odds) - 1

        # ШАГ 6: Определение консенсуса
        all_models = set(predictions.keys())
        voted_for = set(data['models'])
        voted_against = all_models - voted_for

        # ШАГ 7: Генерация детального отчета
        reasoning_parts = []

        for model_name, pred in predictions.items():
            if model_name in voted_for:
                emoji = '✅'
                status_text = 'ЗА'
            else:
                emoji = '❌'
                status_text = 'ПРОТИВ'

            if pred.get('status') == 'success':
                bet_display = pred.get('recommended_bet', 'Не определено')
                confidence_display = pred.get('confidence', 0)
                reasoning_parts.append(
                    f"{emoji} {model_name.upper()}: {status_text} {bet_display} "
                    f"(уверенность: {confidence_display:.2f})"
                )
            else:
                reasoning_parts.append(f"⚠️ {model_name.upper()}: Ошибка - {pred.get('analysis', '')}")

        return {
            'status': 'success',
            'recommended_bet': bet_name,
            'odds': round(avg_odds, 2),
            'confidence': round(avg_confidence, 2),
            'votes': {
                'for': len(voted_for),
                'against': len(voted_against),
                'total': len(all_models)
            },
            'models_agreement': f"{len(voted_for)} из {len(all_models)} моделей согласны",
            'ev': round(ev, 3),
            'is_profitable': ev > 0,
            'profitability_label': 'Рентабельно ✓' if ev > 0 else 'Не рентабельно ✗',
            'reasoning': '\n'.join(reasoning_parts),
            'detailed_predictions': predictions,
            'vote_distribution': {
                bet: {
                    'count': data['count'],
                    'avg_confidence': round(statistics.mean(data['confidences']), 2),
                    'avg_odds': round(statistics.mean(data['odds']), 2),
                    'models': data['models']
                }
                for bet, data in votes.items()
            }
        }
```

### 6.2. Почему голосование, а не усреднение?

```text
ПРИМЕР 1 (ПОЛНЫЙ КОНСЕНСУС):
DeepSeek:   ТБ (2.5) | уверенность: 0.85
Gemini:     ТБ (2.5) | уверенность: 0.90
ChatGPT:    ТБ (2.5) | уверенность: 0.80
→ Решение: ТБ (2.5) | уверенность: 0.85 (средняя)

ПРИМЕР 2 (РАЗДЕЛИЛИСЬ):
DeepSeek:   ТБ (2.5) | уверенность: 0.95
Gemini:     ТМ (2.5) | уверенность: 0.80
ChatGPT:    ТБ (2.5) | уверенность: 0.60
→ Решение: ТБ (2.5) | уверенность: 0.775 (средняя)

ПРИМЕР 3 (НИЧЬЯ):
DeepSeek:   ТБ (2.5) | уверенность: 0.70
Gemini:     ТМ (2.5) | уверенность: 0.75
ChatGPT:    ТБ (2.5) | уверенность: 0.65
→ Решение: ТБ (2.5) | уверенность: 0.675 (выше средняя)
```

> 💡 **Почему:** Голосование позволяет **отсеять «выбросы»** — ошибочные прогнозы одной модели, даже если она **очень уверена**.

### 6.3. Расчёт Expected Value (EV)

```python
def calculate_ev(probability: float, odds: float) -> float:
    """
    EV = (Вероятность × Коэффициент) - 1

    Пример:
    probability = 0.65 (65% вероятность)
    odds = 1.80

    EV = (0.65 × 1.80) - 1 = 1.17 - 1 = 0.17

    Интерпретация:
    EV > 0   → В долгосрочной перспективе прибыльно
    EV = 0   → Безубыточно
    EV < 0   → Убыточно
    """
    return (probability * odds) - 1
```

> 💡 **Зачем это нужно:** Даже если модель **рекомендует ставку**, она может быть **невыгодной**, если коэффициент **слишком низкий**.

---

## 7. Кэширование и хранение

### 7.1. Кэширование результатов

```python
# analytics/views.py

from django.core.cache import cache
from django.conf import settings


@api_view(['POST'])
def analyze_match(request):
    match_id = request.data.get('match_id')

    # Проверяем кэш
    cache_key = f"analysis_{match_id}"
    cached_result = cache.get(cache_key)

    if cached_result:
        logger.info(f"Returning cached analysis for match {match_id}")
        return Response({
            'status': 'cached',
            'data': cached_result,
            'cached_at': cached_result.get('cached_at')
        })

    # Если нет в кэше — анализируем
    result = perform_analysis(match_id)

    # Сохраняем в кэш на 1 час
    cache.set(
        cache_key,
        {
            **result,
            'cached_at': timezone.now().isoformat()
        },
        timeout=3600  # 1 час
    )

    return Response(result)
```

### 7.2. Почему кэширование?

| Параметр | Без кэша | С кэшем |
|---|---|---|
| **Время ответа** | 5–10 секунд | **< 0.1 секунды** |
| **API-запросов** | 3 на каждый запрос | **1 на матч в час** |
| **Стоимость (100 матчей)** | **$3.50** | **$0.35** |

### 7.3. Сохранение истории

```python
# analytics/models.py

from django.db import models


class AnalysisHistory(models.Model):
    ...
```

> ⚠️ **Здесь исходный файл обрывается** — начинается новая тема (Docker-контейнеризация), и первая часть логически не завершена. Класс `AnalysisHistory` показан без тела.

---
---

# Часть II. Docker-контейнеризация

---

## 8. Структура проекта

### 8.1. Полная структура с модулем Analytics

```text
your_project/
├── docker-compose.yml              # Главный docker-compose
├── .env                            # Переменные окружения
├── .env.example                    # Пример переменных
│
├── apps/                           # Все Django-приложения
│   ├── core/                       # Базовые модели и утилиты
│   │   ├── models.py
│   │   └── ...
│   │
│   ├── matches/                    # Приложение для матчей
│   │   ├── models.py
│   │   ├── views.py
│   │   └── ...
│   │
│   └── analytics/                  # ⭐ НОВЫЙ МОДУЛЬ
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py               # Свои модели (связаны с matches)
│       ├── admin.py
│       ├── views.py                # API эндпоинты
│       ├── urls.py
│       │
│       ├── services/               # Бизнес-логика
│       │   ├── __init__.py
│       │   ├── llm_clients.py      # Клиенты для ИИ
│       │   ├── analyzer.py         # Анализ и принятие решений
│       │   ├── data_preparer.py    # Подготовка данных
│       │   └── cache_manager.py    # Управление кэшем
│       │
│       ├── management/             # Кастомные команды
│       │   └── commands/
│       │       ├── analyze.py      # Анализ матча
│       │       └── clean_cache.py  # Очистка кэша
│       │
│       ├── migrations/             # Миграции модуля
│       │   └── 0001_initial.py
│       │
│       ├── tests/                  # Тесты
│       │   ├── test_llm_clients.py
│       │   └── test_analyzer.py
│       │
│       ├── requirements.txt        # Зависимости модуля
│       └── README.md               # Документация модуля
│
├── config/                         # Конфигурация проекта
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
│
├── static/                         # Статические файлы
├── media/                          # Медиа-файлы
│
├── docker/                         # Docker-конфигурации
│   ├── web/
│   │   └── Dockerfile              # Dockerfile основного приложения
│   │
│   └── analytics/                  # ⭐ Dockerfile для модуля
│       ├── Dockerfile
│       ├── entrypoint.sh
│       └── gunicorn.conf.py
│
├── scripts/                        # Вспомогательные скрипты
│   ├── init_db.py
│   └── seed_data.py
│
├── requirements/
│   ├── base.txt                    # Основные зависимости
│   ├── dev.txt                     # Для разработки
│   └── analytics.txt               # ⭐ Зависимости модуля
│
└── manage.py
```

### 8.2. Почему такая структура?

| Решение | Причина |
|---|---|
| **Модуль в отдельной папке** | Изоляция кода, легче поддерживать |
| **Свои зависимости** | Модуль может использовать **специфические библиотеки** |
| **Свои миграции** | Управление схемой БД **независимо** от других приложений |
| **Свои тесты** | Тестирование только **функционала модуля** |
| **Свой Dockerfile** | Возможность **масштабировать модуль отдельно** |

---

## 9. Docker-контейнеризация модуля

### 9.1. Dockerfile для модуля Analytics

```dockerfile
# docker/analytics/Dockerfile

FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для безопасности
RUN groupadd -r analytics && useradd -r -g analytics analytics

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements/analytics.txt requirements/analytics.txt
RUN pip install --no-cache-dir -r requirements/analytics.txt

# Копируем код модуля
COPY apps/analytics /app/apps/analytics
COPY config /app/config
COPY manage.py /app/
COPY entrypoint.sh /app/

# Права доступа
RUN chmod +x /app/entrypoint.sh
RUN chown -R analytics:analytics /app

# Переключаемся на пользователя
USER analytics

# Точка входа
ENTRYPOINT ["/app/entrypoint.sh"]

# Команда по умолчанию (Gunicorn)
CMD ["gunicorn", "--config", "/app/docker/analytics/gunicorn.conf.py", "config.wsgi:application"]
```

### 9.2. Entrypoint скрипт

```bash
# docker/analytics/entrypoint.sh

#!/bin/bash
set -e

echo "🚀 Запуск модуля Analytics..."

# Ожидаем готовности базы данных
echo "⏳ Ожидание PostgreSQL..."
while ! nc -z ${DB_HOST:-db} ${DB_PORT:-5432}; do
    sleep 1
done
echo "✅ PostgreSQL готов!"

# Применяем миграции для модуля
echo "📦 Применение миграций..."
python manage.py migrate analytics --database=analytics_db

# Создаем суперпользователя (если нужно)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "👤 Создание суперпользователя..."
    python manage.py createsuperuser --noinput || true
fi

# Собираем статику
echo "📁 Сбор статики..."
python manage.py collectstatic --noinput

echo "✅ Модуль Analytics готов!"

# Запускаем команду
exec "$@"
```

### 9.3. Gunicorn конфигурация

```python
# docker/analytics/gunicorn.conf.py

import multiprocessing

# Порт
bind = "0.0.0.0:8001"

# Количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Таймауты
timeout = 60
graceful_timeout = 30

# Логирование
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Настройки для API запросов к ИИ
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 100
```

---

## 10. Собственная база данных модуля

### 10.1. Настройка подключения к БД

```python
# config/settings.py

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Основная база данных (ваш проект)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'your_project_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    },
    # ⭐ БАЗА ДАННЫХ МОДУЛЯ ANALYTICS
    'analytics_db': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('ANALYTICS_DB_NAME', 'analytics_db'),
        'USER': os.getenv('ANALYTICS_DB_USER', 'analytics_user'),
        'PASSWORD': os.getenv('ANALYTICS_DB_PASSWORD', 'analytics_password'),
        'HOST': os.getenv('ANALYTICS_DB_HOST', 'analytics_db'),
        'PORT': os.getenv('ANALYTICS_DB_PORT', '5432'),
        'OPTIONS': {
            'options': '-c search_path=analytics,public'
        }
    }
}

# Роутер для баз данных
DATABASE_ROUTERS = ['config.db_routers.AnalyticsRouter']
```

### 10.2. Роутер для разделения баз данных

```python
# config/db_routers.py


class AnalyticsRouter:
    """
    Роутер для направления запросов к правильной базе данных.

    Модели из приложения analytics используют базу 'analytics_db',
    все остальные - 'default'.
    """

    def db_for_read(self, model, **hints):
        """Определяет, из какой базы читать"""
        if model._meta.app_label == 'analytics':
            return 'analytics_db'
        return None

    def db_for_write(self, model, **hints):
        """Определяет, в какую базу писать"""
        if model._meta.app_label == 'analytics':
            return 'analytics_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Разрешает связи между моделями из разных баз.
        Важно: связи между разными базами данных не поддерживаются!
        """
        # Если модели из одной базы - разрешаем
        if obj1._state.db == obj2._state.db:
            return True
        # Если одна из моделей из analytics - запрещаем
        if obj1._meta.app_label == 'analytics' or obj2._meta.app_label == 'analytics':
            return False
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Определяет, в какую базу применять миграции.
        """
        if app_label == 'analytics':
            return db == 'analytics_db'
        return db == 'default'
```

### 10.3. Модели модуля Analytics

```python
# apps/analytics/models.py

from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import JSONField


class LLMProvider(models.TextChoices):
    DEEPSEEK = 'deepseek', 'DeepSeek'
    GEMINI = 'gemini', 'Google Gemini'
    CHATGPT = 'chatgpt', 'OpenAI ChatGPT'


class PromptTemplate(models.Model):
    """Шаблоны промтов для разных ситуаций"""
    name = models.CharField(max_length=100, unique=True)
    system_prompt = models.TextField()
    user_prompt_template = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'analytics_prompt_templates'
        ordering = ['-is_active', 'name']

    def __str__(self):
        return f"{self.name} ({'Активен' if self.is_active else 'Неактивен'})"


class AnalysisSession(models.Model):
    """Сессия анализа матча"""
    match_id = models.IntegerField()  # Ссылка на матч в основной БД
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'В ожидании'),
            ('processing', 'В обработке'),
            ('completed', 'Завершен'),
            ('failed', 'Ошибка')
        ],
        default='pending'
    )
    prompt_template = models.ForeignKey(
        PromptTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'analytics_sessions'
        indexes = [
            models.Index(fields=['match_id', '-started_at']),
            models.Index(fields=['status']),
        ]
        ordering = ['-started_at']

    def __str__(self):
        return f"Анализ матча #{self.match_id} ({self.status})"


class LLMAnalysis(models.Model):
    """Прогноз от конкретной ИИ-модели"""
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='llm_analyses'
    )
    provider = models.CharField(max_length=20, choices=LLMProvider.choices)
    match_analysis = models.TextField()
    recommended_bet = models.CharField(max_length=50)
    odds = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text="От 0.00 до 1.00"
    )
    raw_response = models.JSONField(default=dict)
    status = models.CharField(
        max_length=20,
        choices=[
            ('success', 'Успех'),
            ('error', 'Ошибка'),
            ('timeout', 'Таймаут')
        ],
        default='success'
    )
    error_message = models.TextField(blank=True)
    response_time = models.FloatField(
        null=True,
        blank=True,
        help_text="Время ответа в секундах"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_llm_analyses'
        unique_together = ['session', 'provider']
        indexes = [
            models.Index(fields=['provider', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.provider} - {self.recommended_bet} (уверенность: {self.confidence_score})"


class FinalDecision(models.Model):
    """Итоговое решение на основе анализа всех ИИ"""
    session = models.OneToOneField(
        AnalysisSession,
        on_delete=models.CASCADE,
        related_name='decision'
    )
    selected_bet = models.CharField(max_length=50)
    selected_odds = models.DecimalField(max_digits=5, decimal_places=2)
    confidence = models.DecimalField(max_digits=3, decimal_places=2)
    ev = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        help_text="Expected Value"
    )
    is_profitable = models.BooleanField(default=False)
    reasoning = models.TextField()
    vote_for = models.IntegerField()
    vote_against = models.IntegerField()
    vote_total = models.IntegerField()
    models_agreement = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_final_decisions'

    def __str__(self):
        return f"{self.selected_bet} (EV: {self.ev})"


class AnalyticsCache(models.Model):
    """Кэш результатов анализов"""
    match_id = models.IntegerField(unique=True)
    result = models.JSONField()
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'analytics_cache'
        indexes = [
            models.Index(fields=['expires_at']),
            models.Index(fields=['match_id', 'expires_at']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Кэш матча #{self.match_id} (до {self.expires_at})"
```

### 10.4. Миграции для модуля

```bash
# Создание миграций для модуля
python manage.py makemigrations analytics --database=analytics_db

# Применение миграций
python manage.py migrate analytics --database=analytics_db
```

---

## 11. Интеграция с основным проектом

### 11.1. Настройка settings.py

```python
# config/settings.py

# INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Ваши приложения
    'apps.core',
    'apps.matches',

    # ⭐ Модуль Analytics
    'apps.analytics',
]

# API ключи для ИИ-моделей
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Настройки кэширования
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}/1",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            },
            'MAX_CONNECTIONS': 1000,
            'PICKLE_VERSION': -1,
        },
        'KEY_PREFIX': 'analytics',
        'TIMEOUT': 3600,  # 1 час
    }
}

# Настройки логирования
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/analytics.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'analytics_file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/analytics_debug.log'),
            'maxBytes': 1024 * 1024 * 50,  # 50 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps.analytics': {
            'handlers': ['console', 'analytics_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'httpx': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
```

### 11.2. URL-конфигурация модуля

```python
# config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # ⭐ API модуля Analytics
    path('api/analytics/', include('apps.analytics.urls')),

    # Ваши другие URL
    path('api/matches/', include('apps.matches.urls')),
]
```

```python
# apps/analytics/urls.py

from django.urls import path
from .views import (
    AnalyzeMatchView,
    AnalysisStatusView,
    PromptTemplateListView,
    AnalysisHistoryView,
    CacheClearView
)

app_name = 'analytics'

urlpatterns = [
    # Основной эндпоинт для анализа
    path('analyze/', AnalyzeMatchView.as_view(), name='analyze'),

    # Статус анализа
    path('status/<int:session_id>/', AnalysisStatusView.as_view(), name='status'),

    # Шаблоны промтов
    path('prompts/', PromptTemplateListView.as_view(), name='prompts'),

    # История анализов
    path('history/', AnalysisHistoryView.as_view(), name='history'),
    path('history/<int:match_id>/', AnalysisHistoryView.as_view(), name='history_match'),

    # Управление кэшем
    path('cache/clear/', CacheClearView.as_view(), name='cache_clear'),
    path('cache/clear/<int:match_id>/', CacheClearView.as_view(), name='cache_clear_match'),
]
```

---

## 12. Настройка переменных окружения

### 12.1. Файл `.env.example`

```bash
# .env.example

# ========================
# ОСНОВНАЯ БАЗА ДАННЫХ
# ========================
DB_NAME=your_project_db
DB_USER=postgres
DB_PASSWORD=secure_password
DB_HOST=db
DB_PORT=5432

# ========================
# БАЗА ДАННЫХ ANALYTICS
# ========================
ANALYTICS_DB_NAME=analytics_db
ANALYTICS_DB_USER=analytics_user
ANALYTICS_DB_PASSWORD=analytics_password
ANALYTICS_DB_HOST=analytics_db
ANALYTICS_DB_PORT=5432

# ========================
# API КЛЮЧИ
# ========================
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...

# ========================
# DJANGO
# ========================
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# ========================
# REDIS
# ========================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=

# ========================
# SUPERUSER (опционально)
# ========================
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=admin123
DJANGO_SUPERUSER_EMAIL=admin@example.com
```

---

## 13. Запуск и тестирование

### 13.1. Полный `docker-compose.yml`

```yaml
# docker-compose.yml

version: '3.8'

services:
  # ========================
  # ОСНОВНОЙ ПРОЕКТ (Web)
  # ========================
  web:
    build:
      context: .
      dockerfile: docker/web/Dockerfile
    container_name: project_web
    volumes:
      - .:/app
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: python manage.py runserver 0.0.0.0:8000
    restart: unless-stopped

  # ========================
  # МОДУЛЬ ANALYTICS
  # ========================
  analytics:
    build:
      context: .
      dockerfile: docker/analytics/Dockerfile
    container_name: project_analytics
    volumes:
      - .:/app
      - logs_volume:/app/logs
    ports:
      - "8001:8001"  # Отдельный порт для модуля
    env_file:
      - .env
    depends_on:
      analytics_db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - project_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ========================
  # БАЗА ДАННЫХ (Основная)
  # ========================
  db:
    image: postgres:15
    container_name: project_db
    environment:
      POSTGRES_DB: ${DB_NAME:-your_project_db}
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - project_network

  # ========================
  # БАЗА ДАННЫХ ANALYTICS
  # ========================
  analytics_db:
    image: postgres:15
    container_name: project_analytics_db
    environment:
      POSTGRES_DB: ${ANALYTICS_DB_NAME:-analytics_db}
      POSTGRES_USER: ${ANALYTICS_DB_USER:-analytics_user}
      POSTGRES_PASSWORD: ${ANALYTICS_DB_PASSWORD:-analytics_password}
    volumes:
      - analytics_postgres_data:/var/lib/postgresql/data
    ports:
      - "5433:5432"  # Отдельный порт
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${ANALYTICS_DB_USER:-analytics_user}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - project_network

  # ========================
  # REDIS (Кэш)
  # ========================
  redis:
    image: redis:7-alpine
    container_name: project_redis
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - project_network

  # ========================
  # PGBOUNCER (Опционально)
  # ========================
  pgbouncer:
    image: edoburu/pgbouncer:latest
    container_name: project_pgbouncer
    environment:
      - DB_HOST=db
      - DB_PORT=5432
      - DB_USER=${DB_USER:-postgres}
      - DB_PASSWORD=${DB_PASSWORD:-password}
      - POOL_MODE=transaction
      - MAX_CLIENT_CONN=100
      - DEFAULT_POOL_SIZE=20
    ports:
      - "6432:5432"
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - project_network

# ========================
# СЕТИ
# ========================
networks:
  project_network:
    driver: bridge

# ========================
# ВОЛЮМЫ
# ========================
volumes:
  postgres_data:
  analytics_postgres_data:
  redis_data:
  static_volume:
  media_volume:
  logs_volume:
```

### 13.2. Скрипт для инициализации БД

```python
# scripts/init_analytics_db.py

"""
Скрипт для инициализации базы данных Analytics
Использование: python manage.py runscript init_analytics_db
"""

import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()


def create_analytics_schema():
    """Создает схему analytics в базе данных"""
    with connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS analytics")
        cursor.execute("GRANT ALL ON SCHEMA analytics TO analytics_user")
        print("✅ Схема analytics создана")


def create_prompt_templates():
    """Создает дефолтные шаблоны промтов"""
    from apps.analytics.models import PromptTemplate

    templates = [
        {
            'name': 'default',
            'system_prompt': (
                'Ты профессиональный футбольный аналитик с 10-летним опытом. '
                'Специализируешься на прогнозировании тоталов голов. '
                'Отвечай только в формате JSON.'
            ),
            'user_prompt_template': """
Проанализируй матч и дай прогноз на ТОТАЛ ГОЛОВ (2.5).

Турнир: {tournament}
Матч: {home_team} vs {away_team}
Коэффициент на ТБ (2.5): {odds_over}
Коэффициент на ТМ (2.5): {odds_under}

Ответь в формате JSON:
{{
    "analysis": "краткий анализ",
    "recommended_bet": "ТБ (2.5)" или "ТМ (2.5)",
    "odds": число,
    "confidence": число от 0.00 до 1.00
}}
            """
        },
        {
            'name': 'detailed',
            'system_prompt': (
                'Ты ведущий спортивный аналитик с экспертизой в футбольной статистике. '
                'Используй глубокий анализ. Отвечай только в формате JSON.'
            ),
            'user_prompt_template': """
Проведи детальный анализ матча:

📊 Данные:
Турнир: {tournament}
Матч: {home_team} vs {away_team}
Кэф ТБ (2.5): {odds_over}
Кэф ТМ (2.5): {odds_under}

📋 Факторы для анализа:
1. Форма команд в последних 5 матчах
2. История личных встреч
3. Мотивация
4. Тактические особенности

Ответ в JSON:
{{
    "analysis": "детальный анализ",
    "recommended_bet": "ТБ (2.5)" или "ТМ (2.5)",
    "odds": число,
    "confidence": число от 0.00 до 1.00,
    "key_factors": ["фактор1", "фактор2", "фактор3"]
}}
            """
        },
        {
            'name': 'quick',
            'system_prompt': (
                'Быстрый и точный анализатор футбольных матчей. '
                'Отвечай только в формате JSON.'
            ),
            'user_prompt_template': """
Быстрый анализ матча:

{home_team} vs {away_team}
Турнир: {tournament}
ТБ (2.5): {odds_over}
ТМ (2.5): {odds_under}

Ответ JSON:
{{
    "recommended_bet": "ТБ (2.5)" или "ТМ (2.5)",
    "odds": число,
    "confidence": число от 0.00 до 1.00
}}
            """
        }
    ]

    for template_data in templates:
        obj, created = PromptTemplate.objects.get_or_create(
            name=template_data['name'],
            defaults={
                'system_prompt': template_data['system_prompt'],
                'user_prompt_template': template_data['user_prompt_template'],
                'is_active': True
            }
        )
        if created:
            print(f"✅ Создан шаблон: {obj.name}")
        else:
            print(f"ℹ️ Шаблон уже существует: {obj.name}")


def run():
    print("🚀 Инициализация базы данных Analytics...")

    create_analytics_schema()
    create_prompt_templates()

    print("✅ Инициализация завершена!")
```

---

## 14. Мониторинг и логирование

### 14.1. Health Check эндпоинт

```python
# apps/analytics/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache
from django.db import connection


class HealthCheckView(APIView):
    """Проверка здоровья модуля"""

    def get(self, request):
        status = {
            'module': 'analytics',
            'status': 'healthy',
            'checks': {}
        }

        # Проверка базы данных
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            status['checks']['database'] = 'ok'
        except Exception as e:
            status['checks']['database'] = f'error: {str(e)}'
            status['status'] = 'unhealthy'

        # Проверка Redis
        try:
            cache.set('health_check', 'ok', 10)
            if cache.get('health_check') == 'ok':
                status['checks']['redis'] = 'ok'
            else:
                status['checks']['redis'] = 'error'
                status['status'] = 'unhealthy'
        except Exception as e:
            status['checks']['redis'] = f'error: {str(e)}'
            status['status'] = 'unhealthy'

        # Проверка API ключей
        from django.conf import settings
        api_keys = {
            'deepseek': bool(settings.DEEPSEEK_API_KEY),
            'gemini': bool(settings.GEMINI_API_KEY
```

> 🛑 **ЗДЕСЬ ФАЙЛ ОБРЫВАЕТСЯ.**
> Исходник заканчивается на середине выражения `settings.GEMINI_API_KEY` — без закрывающей скобки, без остатка словаря `api_keys`, без `return Response(...)`.
>
> **Что нужно от тебя:** скинь **продолжение** файла (оставшуюся часть `HealthCheckView` и всё, что после) — и я **дополню** этот markdown-файл без потери контекста.

---

## 🏁 Итог

Этот документ — **архитектурное ядро проекта**. Здесь собрано:

- 🧠 **Полный цикл** аналитики (от запроса до решения).
- 🤖 **3 ИИ-модели** и логика их **голосования**.
- 🐳 **Docker-контейнеризация** модуля как **отдельного сервиса**.
- 🗄 **Собственная БД** (`analytics_db`) + **роутер** для разделения.
- 📊 **Модели** для истории, кэша и решений.
- 🔐 **Переменные окружения**, **мониторинг** и **health check**.

---

<div align="center">

**ПОЛНЫЙ КЕЙС: Работа модуля аналитики «Информатор»**

`Django` · `DRF` · `PostgreSQL` · `Redis` · `Docker` · `DeepSeek` · `Gemini` · `ChatGPT` · `Multi-DB`

</div>