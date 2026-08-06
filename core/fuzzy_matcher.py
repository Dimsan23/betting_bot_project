from difflib import SequenceMatcher


def get_best_match(target_name, candidates, threshold=0.7):
    """
    target_name: имя из API
    candidates: список имен из базы данных (MatchStat)
    threshold: порог схожести (0.7 = 70% совпадения)
    """
    best_match = None
    highest_ratio = 0

    for candidate in candidates:
        ratio = SequenceMatcher(None, target_name.lower(), candidate.lower()).ratio()
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = candidate

    return best_match if highest_ratio >= threshold else None