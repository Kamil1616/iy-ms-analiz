import os
import requests

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE_URL = "https://" + API_HOST
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}

def default_stats():
    return {"general": {"avg_scored": 1.35, "goals_scored": 27, "goals_conceded": 20, "btts_rate": 0.45, "ht_goal_ratio": 0.27, "tempo_score": 2.5}, "home": {"avg_scored": 1.5, "goals_scored": 15, "goals_conceded": 10}, "away": {"avg_scored": 1.2, "goals_scored": 12, "goals_conceded": 12}}

def parse_team_stats(data):
    if not data:
        return default_stats()
    goals = data.get("goals", {})
    fix = data.get("fixtures", {})
    ph = fix.get("played", {}).get("home", 10)
    pa = fix.get("played", {}).get("away", 10)
    pt = fix.get("played", {}).get("total", 20)
    sh = goals.get("for", {}).get("total", {}).get("home", 15)
    sa = goals.get("for", {}).get("total", {}).get("away", 12)
    st = goals.get("for", {}).get("total", {}).get("total", 27)
    ct = goals.get("against", {}).get("total", {}).get("total", 20)
    if pt == 0 or st == 0:
        return default_stats()
    return {"general": {"avg_scored": st/max(pt,1), "goals_scored": st, "goals_conceded": ct, "btts_rate": 0.45, "ht_goal_ratio": 0.27, "tempo_score": 2.5}, "home": {"avg_scored": sh/max(ph,1), "goals_scored": sh, "goals_conceded": 0}, "away": {"avg_scored": sa/max(pa,1), "goals_scored": sa, "goals_conceded": 0}}

def get_fixtures(date):
    r = requests.get(BASE_URL+"/fixtures", headers=HEADERS, params={"date": date, "timezone": "Europe/Istanbul"}, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_team_last_matches(team_id, count=10):
    try:
        r = requests.get(BASE_URL+"/fixtures", headers=HEADERS, params={"team": team_id, "last": count, "status": "FT"}, timeout=30)
        r.raise_for_status()
        return r.json().get("response", [])
    except:
        return []

def stats_from_matches(matches, team_id, venue="home"):
    scored = []
    conceded = []
    ht_scored = []
    for m in matches:
        teams = m.get("teams", {})
        goals = m.get("goals", {})
        score = m.get("score", {})
        is_home = teams.get("home", {}).get("id") == team_id
        if venue == "home" and not is_home:
            continue
        if venue == "away" and is_home:
            continue
        if is_home:
            s = goals.get("home") or 0
            c = goals.get("away") or 0
            ht_s = (score.get("halftime", {}) or {}).get("home") or 0
        else:
            s = goals.get("away") or 0
            c = goals.get("home") or 0
            ht_s = (score.get("halftime", {}) or {}).get("away") or 0
        scored.append(s)
        conceded.append(c)
        ht_scored.append(ht_s)
    if not scored:
        return None
    avg_s = sum(scored) / len(scored)
    avg_c = sum(conceded) / len(conceded)
    avg_ht = sum(ht_scored) / len(ht_scored)
    ht_ratio = avg_ht / avg_s if avg_s > 0 else 0.27
    ht_ratio = max(0.15, min(0.55, ht_ratio))
    btts = sum(1 for s, c in zip(scored, conceded) if s > 0 and c > 0) / len(scored)
    return {"avg_scored": avg_s, "goals_scored": sum(scored), "goals_conceded": sum(conceded), "btts_rate": btts, "ht_goal_ratio": ht_ratio, "tempo_score": 2.5}

def get_team_stats(team_id, league_id, season):
    try:
        r = requests.get(BASE_URL+"/teams/statistics", headers=HEADERS, params={"team": team_id, "league": league_id, "season": season}, timeout=30)
        r.raise_for_status()
        data = r.json().get("response", {})
        parsed = parse_team_stats(data)
        if parsed["general"]["avg_scored"] != 1.35:
            return parsed
    except:
        pass
    matches = get_team_last_matches(team_id, 10)
    if not matches:
        return default_stats()
    general = stats_from_matches(matches, team_id, "all") or default_stats()["general"]
    home_s = stats_from_matches(matches, team_id, "home") or default_stats()["home"]
    away_s = stats_from_matches(matches, team_id, "away") or default_stats()["away"]
    return {"general": general, "home": {"avg_scored": home_s["avg_scored"], "goals_scored": home_s["goals_scored"], "goals_conceded": home_s["goals_conceded"]}, "away": {"avg_scored": away_s["avg_scored"], "goals_scored": away_s["goals_scored"], "goals_conceded": away_s["goals_conceded"]}}
