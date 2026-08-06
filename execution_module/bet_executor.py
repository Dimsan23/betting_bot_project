import asyncio
import os
import logging
from aiogram import Bot
from sports_data.models import MatchOdds
from core.math_engine import MathEngine
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)


# Эта функция выполняется синхронно
def process_single_odds(odds):
    # Доступ к связанным данным здесь происходит синхронно, что безопасно
    home_team = odds.match.home_team
    away_team = odds.match.away_team

    prob = MathEngine.get_match_prediction(home_team, away_team)

    if prob and 'home' in prob:
        value = MathEngine.calculate_value(prob['home'], odds.home_odds)
        if value > 0.3:
            odds.notified = True
            odds.save()  # Синхронное сохранение
            return value, f"🔥 Валуй: {value:.2f}\n{home_team} vs {away_team}"
    return None, None


async def run_bot_loop():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        logger.error("Токен или Chat ID не найдены!")
        return

    bot = Bot(token=token)
    logger.info("Бот-исполнитель запущен...")

    while True:
        try:
            # Получаем список объектов (синхронно, внутри sync_to_async)
            query = MatchOdds.objects.filter(notified=False).select_related('match')
            pending_odds = await sync_to_async(list)(query)

            for odds in pending_odds:
                try:
                    # Вызываем всю логику обработки синхронно
                    value, text = await sync_to_async(process_single_odds)(odds)

                    if text:
                        await bot.send_message(chat_id=chat_id, text=text)
                        logger.info(f"Уведомление отправлено для матча {odds.id}")

                except Exception as e:
                    logger.error(f"Ошибка при обработке матча {odds}: {e}")

        except Exception as e:
            logger.error(f"Ошибка в основном цикле: {e}")

        await asyncio.sleep(60)