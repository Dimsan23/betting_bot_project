from core.math_engine import MathEngine

def run_analysis(home_team, away_team, bookie_odds):
    # Получаем вероятности из движка
    prob = MathEngine.get_match_prediction(home_team, away_team)

    # Рассчитываем значение (возвращаем только число)
    home_value = MathEngine.calculate_value(prob['home'], bookie_odds['home'])

    # Возвращаем число, округленное до 3 знаков
    return round(home_value, 3)