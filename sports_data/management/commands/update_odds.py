from django.core.management.base import BaseCommand
from sports_data.services import OddsService


class Command(BaseCommand):
    help = 'Обновление коэффициентов из The Odds API'

    def add_arguments(self, parser):
        parser.add_argument('--league', type=str, required=True, help='Ключ лиги (напр. soccer_usa_mls)')

    def handle(self, *args, **kwargs):
        league_key = kwargs['league']
        self.stdout.write(f"Запуск синхронизации для {league_key}...")

        try:
            # Вызываем сервис синхронизации
            count = OddsService.sync_odds(league_key)
            self.stdout.write(self.style.SUCCESS(f"Успешно обновлено {count} матчей."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Ошибка при синхронизации: {e}"))