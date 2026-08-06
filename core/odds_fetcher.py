import requests
from sports_data.models import MatchStat, MatchOdds


class OddsFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'x-apisports-key': self.api_key}

    def update_odds_for_match(self, match_stat):
        # Пример эндпоинта (проверь документацию API-Sports)
        url = f"https://v3.football.api-sports.io/odds"
        params = {'fixture': match_stat.api_id}  # Предполагаем, что у MatchStat есть api_id

        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            data = response.json().get('response', [])
            # Парсинг логики...
            # Сохраняем в MatchOdds
            MatchOdds.objects.update_or_create(
                match=match_stat,
                defaults={'home_odds': ..., 'away_odds': ..., 'draw_odds': ...}
            )