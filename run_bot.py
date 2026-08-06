import os
import django
import asyncio

# Инициализация Django для доступа к моделям
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # Укажи свое имя проекта
django.setup()

from execution_module.bet_executor import run_bot_loop

if __name__ == "__main__":
    asyncio.run(run_bot_loop())