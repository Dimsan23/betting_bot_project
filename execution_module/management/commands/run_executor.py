# execution_module/management/commands/run_executor.py
from django.core.management.base import BaseCommand
import asyncio
from execution_module.bet_executor import run_bot_loop

class Command(BaseCommand):
    help = 'Запуск бота-исполнителя (уведомления + ставки)'

    def handle(self, *args, **options):
        asyncio.run(run_bot_loop())