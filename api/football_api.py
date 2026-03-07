import requests
import os
from datetime import datetime, timedelta

API_KEY = os.getenv("API_FOOTBALL_KEY")
API_HOST = os.getenv("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE_URL = f"https://{API_HOST}"

HEADERS = {
    "x-apisports-key": API_KEY,
    "x-apisports-host": API_HOST
}

def get_fixtures_by_date(date_str):
    url = f"{BASE_URL}/fixtures"
    params = {"date": date_str, "timezone": "Europe/Istanbul"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("response", [])

def get_team_last_matches(team_id, last=6):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": last, "timezone": "Europe/Istanbul"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    return r.json().get("response", [])

def get_team_last_home_matches(team_id, last=6):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": last * 2, "timezone": "Europe/Istanbul"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    all_matches = r.json().get("response", [])
    home_matches = [m for m in all_matches if m["teams"]["home"]["id"] == team_id]
    return home_matches[:last]

def get_team_last_away_matches(team_id, last=6):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "last": last * 2, "timezone": "Europe/Istanbul"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()
    all_matches = r.json().get("response", [])
    away_matches = [m for m in all_matches if m["teams"]["away"]["id"] == team_id]
    return away_matches[:last]

def get_todays_fixtures():
    return get_fixtures_by_date(datetime.now().strftime("%Y-%m-%d"))

def get_tomorrows_fixtures():
    return get_fixtures_by_date((datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"))

def parse_match_data(fixture):
    teams = fixture.get("teams", {})
    goals = fixture.get("goals", {})
    score = fixture.get("score", {})
    fixture_info = fixture.get("fixture", {})
    league = fixture.get("league", {})
    halftime = score.get("halftime", {})
    return {
        "fixture_id": fixture_info.get("id"),
        "date": fixture_info.get("date"),
        "status": fixture_info.get("status", {}).get("short"),
        "league_id": league.get("id"),
        "league_name": league.get("name"),
        "league_country": league.get("country"),
        "league_logo": league.get("logo"),
        "home_team_id": teams.get("home", {}).get("id"),
        "home_team_name": teams.get("home", {}).get("name"),
        "home_team_logo": teams.get("home", {}).get("logo"),
        "away_team_id": teams.get("away", {}).get("id"),
        "away_team_name": teams.get("away", {}).get("name"),
        "away_team_logo": teams.get("away", {}).get("logo"),
        "home_goals": goals.get("home"),
        "away_goals": goals.get("away"),
        "ht_home": halftime.get("home"),
        "ht_away": halftime.get("away"),
    }

def extract_team_stats(matches, team_id, venue="general"):
    stats = {
        "matches": [],
        "goals_scored": 0,
        "goals_conceded": 0,
        "ht_goals_scored": 0,
        "ht_goals_conceded": 0,
        "btts_count": 0,
        "ht_draw_count": 0,
        "lead_protected": 0,
        "lead_total": 0,
        "first_goal_count": 0,
        "total_matches": 0,
    }
    for f in matches:
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        score = f.get("score", {})
        halftime = score.get("halftime", {})
        is_home = teams.get("home", {}).get("id") == team_id
        if is_home:
            scored = goals.get("home") or 0
            conceded = goals.get("away") or 0
            ht_scored = halftime.get("home") or 0
            ht_conceded = halftime.get("away") or 0
            won = teams.get("home", {}).get("winner")
        else:
            scored = goals.get("away") or 0
            conceded = goals.get("home") or 0
            ht_scored = halftime.get("away") or 0
            ht_conceded = halftime.get("home") or 0
            won = teams.get("away", {}).get("winner")
        stats["goals_scored"] += scored
        stats["goals_conceded"] += conceded
        stats["ht_goals_scored"] += ht_scored
        stats["ht_goals_conceded"] += ht_conceded
        stats["total_matches"] += 1
        if scored > 0 and conceded > 0:
            stats["btts_count"] += 1
        if ht_scored == ht_conceded:
            stats["ht_draw_count"] += 1
        if scored > 0:
            stats["lead_total"] += 1
            if won:
                stats["lead_protected"] += 1
            stats["first_goal_count"] += 1
        stats["matches"].append({
            "scored": scored, "conceded": conceded,
            "ht_scored": ht_scored, "ht_conceded": ht_conceded, "won": won,
        })
    n = stats["total_matches"] or 1
    stats["avg_scored"] = stats["goals_scored"] / n
    stats["avg_conceded"] = stats["goals_conceded"] / n
    stats["avg_ht_scored"] = stats["ht_goals_scored"] / n
    stats["avg_ht_conceded"] = stats["ht_goals_conceded"] / n
    stats["btts_rate"] = stats["btts_count"] / n
    stats["ht_draw_rate"] = stats["ht_draw_count"] / n
    stats["lead_protection"] = (stats["lead_protected"] / stats["lead_total"]) if stats["lead_total"] > 0 else 0
    stats["first_goal_rate"] = stats["first_goal_count"] / n
    total_goals = stats["goals_scored"] + stats["goals_conceded"]
    total_ht_goals = stats["ht_goals_scored"] + stats["ht_goals_conceded"]
    stats["ht_goal_ratio"] = (total_ht_goals / total_goals) if total_goals > 0 else 0.27
    stats["tempo_score"] = total_goals / n
    return stats

cat > models/value_hunting.py << 'EOF'
import math
from scipy.stats import poisson as scipy_poisson

DC_RHO = -0.13

def dixon_coles_correction(home_goals, away_goals, lambda_home, lambda_away, rho=DC_RHO):
    if home_goals == 0 and away_goals == 0:
        return 1 - lambda_home * lambda_away * rho
    elif home_goals == 0 and away_goals == 1:
        return 1 + lambda_home * rho
    elif home_goals == 1 and away_goals == 0:
        return 1 + lambda_away * rho
    elif home_goals == 1 and away_goals == 1:
        return 1 - rho
    else:
        return 1.0

def poisson_prob(lam, k):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return scipy_poisson.pmf(k, lam)

def score_matrix(lambda_home, lambda_away, max_goals=8):
    matrix = {}
    for h in range(max_goals + 1):
        for a in range(max_goals + 1):
            p = poisson_prob(lambda_home, h) * poisson_prob(lambda_away, a)
            p *= dixon_coles_correction(h, a, lambda_home, lambda_away)
            matrix[(h, a)] = p
    total = sum(matrix.values())
    if total > 0:
        matrix = {k: v / total for k, v in matrix.items()}
    return matrix

def compute_lambdas(home_stats_general, home_stats_home, away_stats_general, away_stats_away):
    home_attack = (home_stats_general["avg_scored"] + home_stats_home["avg_scored"]) / 2
    away_attack = (away_stats_general["avg_scored"] + away_stats_away["avg_scored"]) / 2
    home_gd = home_stats_general["goals_scored"] - home_stats_general["goals_conceded"]
    away_gd = away_stats_general["goals_scored"] - away_stats_general["goals_conceded"]
    net_diff = (home_gd - away_gd) / 10.0
    net_diff = max(-0.3, min(0.3, net_diff))
    lambda_home = home_attack * 0.95 * (1 + net_diff * 0.1)
    lambda_away = away_attack * 1.00 * (1 - net_diff * 0.1)
    form_diff_h = home_stats_general["avg_scored"] - home_attack
    form_diff_a = away_stats_general["avg_scored"] - away_attack
    if abs(form_diff_h) > 0.5:
        lambda_home += form_diff_h * 0.3
    if abs(form_diff_a) > 0.5:
        lambda_away += form_diff_a * 0.3
    lambda_home = max(0.3, lambda_home)
    lambda_away = max(0.3, lambda_away)
    return lambda_home, lambda_away

def compute_lambda_iy(lambda_total, home_stats_general, away_stats_general, home_stats_home, away_stats_away):
    ht_ratio_home = home_stats_general.get("ht_goal_ratio", 0.27)
    ht_ratio_away = away_stats_general.get("ht_goal_ratio", 0.27)
    ht_ratio = (ht_ratio_home + ht_ratio_away) / 2
    ht_ratio = max(0.15, min(0.55, ht_ratio))
    lambda_iy = lambda_total * ht_ratio
    btts_avg = (home_stats_general.get("btts_rate", 0.4) + away_stats_general.get("btts_rate", 0.4)) / 2
    if btts_avg > 0.6:
        lambda_iy *= 1.08
    tempo_home = home_stats_general.get("tempo_score", 2.5)
    tempo_away = away_stats_general.get("tempo_score", 2.5)
    tempo_match = (tempo_home + tempo_away) / 2
    if tempo_match > 4.0:
        lambda_iy *= 1.05
    return lambda_iy

def compute_halftime_probs(lambda_home, lambda_away, lambda_iy):
    total = lambda_home + lambda_away
    if total > 0:
        lh_iy = lambda_iy * (lambda_home / total)
        la_iy = lambda_iy * (lambda_away / total)
    else:
        lh_iy = lambda_iy / 2
        la_iy = lambda_iy / 2
    max_g = 6
    ht_probs = {"1": 0, "X": 0, "2": 0}
    for h in range(max_g + 1):
        for a in range(max_g + 1):
            p = poisson_prob(lh_iy, h) * poisson_prob(la_iy, a)
            p *= dixon_coles_correction(h, a, lh_iy, la_iy)
            if h > a:
                ht_probs["1"] += p
            elif h == a:
                ht_probs["X"] += p
            else:
                ht_probs["2"] += p
    total_ht = sum(ht_probs.values())
    if total_ht > 0:
        ht_probs = {k: v / total_ht for k, v in ht_probs.items()}
    return ht_probs

def compute_iyms_probs(lambda_home, lambda_away, lambda_iy):
    ft_matrix = score_matrix(lambda_home, lambda_away)
    ht_probs = compute_halftime_probs(lambda_home, lambda_away, lambda_iy)
    ft_probs = {"1": 0, "X": 0, "2": 0}
    for (h, a), p in ft_matrix.items():
        if h > a:
            ft_probs["1"] += p
        elif h == a:
            ft_probs["X"] += p
        else:
            ft_probs["2"] += p
    iyms = {}
    for ht in ["1", "X", "2"]:
        for ft in ["1", "X", "2"]:
            key = f"{ht}/{ft}"
            raw = ht_probs[ht] * ft_probs[ft]
            if ht == ft:
                raw *= 1.35
            elif (ht == "1" and ft == "2") or (ht == "2" and ft == "1"):
                raw *= 0.55
            else:
                raw *= 0.90
            iyms[key] = raw
    total = sum(iyms.values())
    if total > 0:
        iyms = {k: v / total for k, v in iyms.items()}
    return iyms

def compute_iy_over_probs(lambda_iy):
    def p_at_least(lam, k):
        return 1 - sum(poisson_prob(lam, i) for i in range(k))
    return {
        "1.5": p_at_least(lambda_iy, 2),
        "2.5": p_at_least(lambda_iy, 3),
        "3.5": p_at_least(lambda_iy, 4),
    }

SIGNAL_THRESHOLDS = {"1.5": 0.90, "2.5": 0.80, "3.5": 0.70}

def get_iy_signals(iy_over_probs):
    signals = []
    for market, prob in iy_over_probs.items():
        threshold = SIGNAL_THRESHOLDS.get(market, 1.0)
        if prob >= threshold:
            signals.append({
                "market": f"IY {market} Ust",
                "probability": round(prob * 100, 1),
                "signal": "Guclu Sinyal"
            })
    return signals

def run_analysis(home_stats_general, home_stats_home, away_stats_general, away_stats_away):
    lambda_home, lambda_away = compute_lambdas(
        home_stats_general, home_stats_home,
        away_stats_general, away_stats_away
    )
    lambda_total = lambda_home + lambda_away
    lambda_iy = compute_lambda_iy(
        lambda_total, home_stats_general, away_stats_general,
        home_stats_home, away_stats_away
    )
    iyms_probs = compute_iyms_probs(lambda_home, lambda_away, lambda_iy)
    sorted_iyms = sorted(iyms_probs.items(), key=lambda x: x[1], reverse=True)
    iyms_results = []
    for i, (selection, prob) in enumerate(sorted_iyms):
        fair_odd = 1 / prob if prob > 0 else 999
        model_odd = fair_odd * 0.90
        iyms_results.append({
            "rank": i + 1,
            "selection": selection,
            "probability": round(prob * 100, 2),
            "model_odd": round(model_odd, 2),
            "site_odd": None,
            "diff_pct": None,
            "status": None,
            "divider": i == 4
        })
    iy_over_probs = compute_iy_over_probs(lambda_iy)
    iy_signals = get_iy_signals(iy_over_probs)
    return {
        "lambda_home": round(lambda_home, 3),
        "lambda_away": round(lambda_away, 3),
        "lambda_total": round(lambda_total, 3),
        "lambda_iy": round(lambda_iy, 3),
        "iyms_results": iyms_results,
        "iy_over_probs": {k: round(v * 100, 1) for k, v in iy_over_probs.items()},
        "iy_signals": iy_signals,
    }
