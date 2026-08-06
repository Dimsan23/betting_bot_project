import math
from django.db.models import Q
from sports_data.models import MatchStat

class MathEngine:
    HOME_ADVANTAGE = 1.1

    @staticmethod
    def get_league_averages():
        """Считает среднее количество голов одной команды за матч по всей базе"""
        matches = MatchStat.objects.all()
        if not matches.exists():
            return 1.3  # Стандартное значение для футбола

        total_goals = sum([m.home_goals + m.away_goals for m in matches])
        count = matches.count()
        return (total_goals / count) / 2

    @staticmethod
    def get_team_stats(team_name, last_n=5):
        """Возвращает среднее по последним N матчам с экспоненциальным весом"""
        matches = MatchStat.objects.filter(
            Q(home_team=team_name) | Q(away_team=team_name)
        ).order_by('-match_date')[:last_n]

        if not matches.exists():
            return 1.0, 1.0 # Возвращаем 1.0 как нейтральный коэффициент

        total_scored = 0
        total_conceded = 0
        total_weight = 0
        weights = [2.0, 1.5, 1.0, 0.7, 0.5]

        for i, m in enumerate(matches):
            weight = weights[i] if i < len(weights) else 0.5
            if m.home_team == team_name:
                scored, conceded = m.home_goals, m.away_goals
            else:
                scored, conceded = m.away_goals, m.home_goals
            total_scored += scored * weight
            total_conceded += conceded * weight
            total_weight += weight

        return total_scored / total_weight, total_conceded / total_weight

    @staticmethod
    def get_team_strength(team_name):
        """Возвращает индексы силы атаки и защиты команды"""
        avg_goals = MathEngine.get_league_averages()
        scored, conceded = MathEngine.get_team_stats(team_name)
        return scored / avg_goals, conceded / avg_goals

    @staticmethod
    def get_match_prediction(home_team, away_team):
        home_attack, home_defense_val = MathEngine.get_team_strength(home_team)
        away_attack, away_defense_val = MathEngine.get_team_strength(away_team)
        avg_goals = MathEngine.get_league_averages()

        # Ожидаемые голы: Атака хозяев * Оборона гостей * Средний тотал * Home Advantage
        home_expect = (home_attack * away_defense_val * avg_goals) * MathEngine.HOME_ADVANTAGE
        away_expect = (away_attack * home_defense_val * avg_goals)

        return MathEngine.calculate_poisson_probs(home_expect, away_expect)

    @staticmethod
    def calculate_poisson_probs(home_expect, away_expect):
        win_home, draw, win_away = 0, 0, 0
        for h in range(6):
            for a in range(6):
                prob = ((home_expect ** h * math.exp(-home_expect)) / math.factorial(h)) * \
                       ((away_expect ** a * math.exp(-away_expect)) / math.factorial(a))
                if h > a: win_home += prob
                elif h == a: draw += prob
                else: win_away += prob
        return {"home": win_home, "draw": draw, "away": win_away}

    @staticmethod
    def calculate_value(probability, odds):
        return round((probability * odds) - 1, 3)

    @staticmethod
    def get_optimal_stake(probability, odds, bankroll=1000):
        if odds <= 1: return 0
        fraction = (probability * odds - 1) / (odds - 1)
        stake = bankroll * min(fraction, 0.05)
        return round(max(stake, 0), 2)