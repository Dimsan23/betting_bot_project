import os
from django.core.management.base import BaseCommand
from sports_data.models import League
from sports_data.services import FootballDataFetcher


class Command(BaseCommand):
    def handle(self, *args, **options):
        api_key = os.environ.get('FOOTBALL_API_KEY')
        fetcher = FootballDataFetcher(api_key)

        for league in League.objects.filter(is_active=True):
            self.stdout.write(f"Обновляю: {league.name}...")
            if fetcher.fetch_matches(league):
                self.stdout.write(self.style.SUCCESS('Готово!'))