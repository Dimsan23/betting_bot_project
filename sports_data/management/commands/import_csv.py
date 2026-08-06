import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from sports_data.models import MatchStat, League

class Command(BaseCommand):
    help = 'Импорт матчей с автоматическим созданием лиги'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)
        parser.add_argument('--league_name', type=str, required=True)
        parser.add_argument('--api_id', type=int, required=True)

    def handle(self, *args, **options):
        league, _ = League.objects.get_or_create(
            name=options['league_name'],
            defaults={'api_id': options['api_id']}
        )

        with open(options['file_path'], 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                # Преобразуем дату из 10/03/2012 в 2012-03-10
                raw_date = row['Date']
                try:
                    # Указываем формат, в котором дата лежит в CSV (день/месяц/год)
                    formatted_date = datetime.strptime(raw_date, '%d/%m/%Y').strftime('%Y-%m-%d')
                except ValueError:
                    # Если формат даты другой, пропускаем строку или выводим ошибку
                    continue

                MatchStat.objects.update_or_create(
                    match_date=formatted_date,
                    home_team=row['Home'],
                    away_team=row['Away'],
                    defaults={
                        'league': league,
                        'home_goals': int(row.get('HG', 0)),
                        'away_goals': int(row.get('AG', 0))
                    }
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f'Импортировано {count} матчей для {league.name}!'))