from django.core.management.base import BaseCommand
from django.core.management import call_command  # <--- Импортируем вызов других команд
from sports_data.models import MatchOdds
from core.math_engine import MathEngine


class Command(BaseCommand):
    help = 'Обновление коэффициентов и поиск валуйных ставок'

    def handle(self, *args, **kwargs):
        self.stdout.write("1. Запуск обновления коэффициентов из API...")
        # Автоматически вызываем update_odds прямо перед анализом
        try:
            call_command('update_odds', league='soccer_russia_premier_league')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"Не удалось обновить кэфы из API: {e}. Работаем с тем, что есть в базе."))

        self.stdout.write("2. Запуск анализа матчей и поиска валуев...")
        odds_qs = MatchOdds.objects.select_related('match').all()
        count = 0

        for odds in odds_qs:
            match = odds.match
            home_team = match.home_team
            away_team = match.away_team

            probs = MathEngine.get_match_prediction(home_team, away_team)

            if odds.home_odds and odds.home_odds > 1:
                val_home = MathEngine.calculate_value(probs['home'], odds.home_odds)
                if val_home > 0.0:
                    self.stdout.write(self.style.SUCCESS(f"Валуй! П1 {home_team} vs {away_team}: {val_home}"))

            if odds.away_odds and odds.away_odds > 1:
                val_away = MathEngine.calculate_value(probs['away'], odds.away_odds)
                if val_away > 0.0:
                    self.stdout.write(self.style.SUCCESS(f"Валуй! П2 {home_team} vs {away_team}: {val_away}"))

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Проанализировано матчей: {count}"))