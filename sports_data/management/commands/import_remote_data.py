import csv
import requests
import io
from datetime import datetime
from django.core.management.base import BaseCommand
from sports_data.models import MatchStat, League


class Command(BaseCommand):
    help = 'Импорт данных из CSV (football-data.co.uk)'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, required=True, help='Прямая ссылка на CSV')
        parser.add_argument('--league_name', type=str, required=True, help='Имя лиги в БД')

    def handle(self, *args, **options):
        league_name = options['league_name']
        url = options['url']

        league, _ = League.objects.get_or_create(name=league_name)

        try:
            response = requests.get(url)
            response.raise_for_status()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка скачивания: {e}'))
            return

        file_data = io.StringIO(response.text)
        reader = csv.DictReader(file_data)
        count = 0

        for row in reader:
            # Парсим дату (football-data.co.uk использует формат DD/MM/YY или DD/MM/YYYY)
            try:
                # Попробуем оба формата
                match_date = datetime.strptime(row['Date'], '%d/%m/%Y').date()
            except ValueError:
                match_date = datetime.strptime(row['Date'], '%d/%m/%y').date()

            _, created = MatchStat.objects.update_or_create(
                home_team=row['HomeTeam'],
                away_team=row['AwayTeam'],
                match_date=match_date,
                defaults={
                    'league': league,
                    'home_goals': int(row.get('FTHG', 0)),
                    'away_goals': int(row.get('FTAG', 0)),
                }
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Готово! Импортировано {count} матчей для {league_name}'))