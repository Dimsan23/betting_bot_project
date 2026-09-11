import asyncio
import os
import logging
from aiogram import Bot
from sports_data.models import MatchOdds
from core.math_engine import MathEngine
from asgiref.sync import sync_to_async

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)


# Выносим всю работу с БД и логикой в одну синхронную функцию,
# которая будет целиком выполняться в отдельном потоке через sync_to_async
def check_and_process_odds(odds_id):
    try:
        odds = MatchOdds.objects.select_related('match').get(id=odds_id, notified=False)
    except MatchOdds.DoesNotExist:
        return None, None

    home_team = odds.match.home_team
    away_team = odds.match.away_team

    prob = MathEngine.get_match_prediction(home_team, away_team)

    if prob and 'home' in prob:
        value = MathEngine.calculate_value(prob['home'], odds.home_odds)
        if value > 0.3:
            odds.notified = True
            odds.save()
            return value, f"🔥 Валуй: {value:.2f}\n{home_team} vs {away_team}"

    return None, None


async def run_bot_loop():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')

    if not token or not chat_id:
        logger.error("Токен или Chat ID не найдены!")
        return

    bot = Bot(token=token)
    logger.info("Бот-исполнитель успешно запущен и начал опрос базы данных...")

    while True:
        try:
            logger.info("Проверка новых коэффициентов в базе...")

            # Получаем только список ID незаверенных записей (быстро и без проблем с асинхронностью)
            query = MatchOdds.objects.filter(notified=False).values_list('id', flat=True)
            pending_ids = await sync_to_async(list)(query)
            logger.info(f"Найдено неподтвержденных записей: {len(pending_ids)}")

            for odds_id in pending_ids:
                try:
                    # Обрабатываем каждую запись безопасно через ID
                    value, text = await sync_to_async(check_and_process_odds)(odds_id)

                    if text:
                        await bot.send_message(chat_id=chat_id, text=text)
                        logger.info(f"Уведомление отправлено для матча ID: {odds_id}")

                except Exception as e:
                    logger.error(f"Ошибка при обработке матча ID {odds_id}: {e}")

        except Exception as e:
            logger.warning(f"База данных недоступна или запускается ({e}). Ждем 5 секунд...")
            await asyncio.sleep(5)
            continue

        logger.info("Итерация цикла завершена. Ожидание 60 секунд...")
        await asyncio.sleep(60)