from django.shortcuts import render
from sports_data.models import MatchStat, MatchOdds
from core.math_engine import MathEngine


def dashboard(request):
    # Теперь запрашиваем только те матчи, для которых есть коэффициенты
    matches = MatchStat.objects.filter(odds__isnull=False).order_by('-match_date')[:10]
    results = []

    for m in matches:
        # Проверяем связь напрямую через related_name='odds'
        has_odds = hasattr(m, 'odds')
        odds_val = m.odds.home_odds if has_odds else None

        value = None
        stake = 0

        if has_odds:
            # Пытаемся получить прогноз
            prob = MathEngine.get_match_prediction(m.home_team, m.away_team)
            if prob and 'home' in prob:
                win_prob = prob['home']
                value = MathEngine.calculate_value(win_prob, odds_val)
                stake = MathEngine.get_optimal_stake(win_prob, odds_val, bankroll=1000)

        results.append({
            'match': m,
            'value': value,
            'kelly_stake': stake,
            'home_odds': odds_val,
            'has_odds': has_odds  # Для отладки в шаблоне
        })

    return render(request, 'sports_data/dashboard.html', {'results': results})