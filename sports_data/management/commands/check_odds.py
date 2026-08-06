from django.core.management.base import BaseCommand
from core.analyzer import run_analysis


class Command(BaseCommand):
    help = 'Анализ валуйных ставок'

    def handle(self, *args, **options):
        # 1. Получаем результат работы анализатора
        result = run_analysis("Arsenal", "Chelsea", {'home': 2.10})

        # 2. Выводим переменную result, а не self.result
        self.stdout.write(result)