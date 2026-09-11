from django.utils import timezone
import requests
import os
from sports_data.models import MatchStat, MatchOdds

# Словарь для приведения имен из API к именам в твоей базе (MatchStat)
TEAM_MAP = {
    'Inter Miami CF': 'Inter Miami',
    'LA Galaxy': 'Los Angeles Galaxy',
    'NY Red Bulls': 'New York Red Bulls',
    'Seattle Sounders FC': 'Seattle Sounders',
    'Portland Timbers': 'Portland Timbers', # Пример, если API отдает иначе
    'Chicago Fire FC': 'Chicago Fire',
    'St. Louis City SC': 'St. Louis City',
# Russia Premier League (РПЛ)
    'CSKA Moscow': 'CSKA Moscow',
    'PFC CSKA Moscow': 'CSKA Moscow',
    'FK Rostov': 'FK Rostov',
    'Rostov': 'FK Rostov',
    'Lokomotiv Moscow': 'Lokomotiv Moscow',
    'Spartak Moscow': 'Spartak Moscow',
    'Zenit': 'Zenit',
    'Zenit St. Petersburg': 'Zenit',
    'Krylya Sovetov': 'Krylya Sovetov',
    'Akhmat Grozny': 'Akhmat Grozny',
    'Akhmat': 'Akhmat Grozny',
    'Krasnodar': 'Krasnodar',
    'Rubin Kazan': 'Rubin Kazan',
    'Rubin': 'Rubin Kazan',
    'Dynamo Moscow': 'Dynamo Moscow',
    'Dinamo Moscow': 'Dynamo Moscow',
    # Дополнительные команды, найденные в файле:
    'M. Saransk': 'Mordovia Saransk',
    'Volga N. Novgorod': 'Volga Nizhny Novgorod',
    'Vladikavkaz': 'Alania Vladikavkaz',
    'Amkar': 'Amkar Perm',
    'FK Anzi Makhackala': 'Anzhi Makhachkala',
    'Kuban': 'Kuban Krasnodar',
    'Ufa': 'Ufa',
    'Ural': 'Ural Yekaterinburg',
    'Arsenal Tula': 'Arsenal Tula',
    'T. Moscow': 'Torpedo Moscow',
    'SKA Khabarovsk': 'SKA Khabarovsk',
    'Tomsk': 'Tom Tomsk',
    'Yenisey': 'Yenisey Krasnoyarsk',
    'Tosno': 'Tosno',
    'Orenburg': 'Orenburg',
    'Tambov': 'Tambov',
    'Sochi': 'Sochi',
    'Pari NN': 'FC Pari Nizhny Novgorod',
    'Khimki': 'Khimki',
    'Torpedo Moscow': 'Torpedo Moscow',
    'Fakel Voronezh': 'Fakel Voronezh',
    'Baltika': 'Baltika Kaliningrad',
    'Akron Togliatti': 'Akron Tolyatti',
    'Dynamo Makhachkala': 'Dynamo Makhachkala',
    'Rodina Moscow': 'Rodina Moscow',
    # Команды из стыковых матчей:
    'Spartak Nalchik': 'Spartak Nalchik',
    'Volgar-Astrakhan': 'Volgar Astrakhan',
    'Tosno': 'Tosno',
}

class OddsService:
    @staticmethod
    def get_normalized_name(name):
        return TEAM_MAP.get(name, name)

    @staticmethod
    def get_odds_for_league(league_key):
        api_key = os.environ.get('FOOTBALL_API_KEY')
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {'apiKey': api_key, 'regions': 'eu', 'markets': 'h2h'}
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else []

    @staticmethod
    def sync_odds(league_key):
        data = OddsService.get_odds_for_league(league_key)
        updated_count = 0
        today = timezone.now().date()

        print(f"Всего матчей в API для {league_key}: {len(data)}")

        for match_data in data:
            # Получаем нормализованные имена для поиска в БД
            home_name = OddsService.get_normalized_name(match_data['home_team'])
            away_name = OddsService.get_normalized_name(match_data['away_team'])

            # Ищем только матчи, у которых дата равна сегодняшней или больше (будущие)
            match = MatchStat.objects.filter(
                home_team__icontains=home_name[:5],
                away_team__icontains=away_name[:5],
                match_date__gte=today
            ).first()

            if match:
                bookmaker = next((b for b in match_data['bookmakers']), None)
                if bookmaker:
                    outcomes = bookmaker['markets'][0]['outcomes']
                    try:
                        # Ищем цены, используя нормализацию для сравнения имен
                        home_price = next(o['price'] for o in outcomes if OddsService.get_normalized_name(o['name']) == match_data['home_team'] or o['name'] == home_name)
                        away_price = next(o['price'] for o in outcomes if OddsService.get_normalized_name(o['name']) == match_data['away_team'] or o['name'] == away_name)
                        draw_price = next((o['price'] for o in outcomes if o['name'].lower() == 'draw'), 0.0)

                        MatchOdds.objects.update_or_create(
                            match=match,
                            defaults={
                                'home_odds': home_price,
                                'away_odds': away_price,
                                'draw_odds': draw_price
                            }
                        )
                        updated_count += 1
                    except StopIteration:
                        print(f"Ошибка сопоставления цен для {home_name} vs {away_name}")
                        continue
            else:
                print(f"НЕ НАЙДЕНО актуального матча в базе (>= {today}): {home_name} vs {away_name}")

        return updated_count