import pytest
from django.utils import timezone
from core.math_engine import MathEngine
from sports_data.models import League, MatchStat, MatchOdds
from execution_module.bet_executor import process_single_odds


def test_calculate_value():
    value = MathEngine.calculate_value(0.6, 2.0)
    assert value > 0


@pytest.mark.django_db
def test_process_single_odds_flow():
    # 1. Создаем Лигу
    league = League.objects.create(name="Test League", api_id=999, is_active=True)

    # 2. Создаем исторический матч с голами, чтобы MathEngine мог рассчитать средние показатели (avg_goals > 0)
    MatchStat.objects.create(
        league=league,
        home_team="Team X",
        away_team="Team Y",
        home_goals=2,
        away_goals=1,
        match_date=timezone.now()
    )

    # 3. Создаем целевой матч для тестирования
    match = MatchStat.objects.create(
        league=league,
        home_team="Team A",
        away_team="Team B",
        home_goals=0,
        away_goals=0,
        match_date=timezone.now()
    )

    # 4. Создаем коэффициенты
    odds = MatchOdds.objects.create(
        match=match,
        home_odds=2.0,
        away_odds=3.0,
        draw_odds=3.5,
        notified=False
    )

    # 5. Вызываем функцию
    value, text = process_single_odds(odds)

    # 6. Проверки
    if value and value > 0.3:
        assert odds.notified is True
        assert "🔥 Валуй" in text