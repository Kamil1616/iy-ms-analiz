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
    return {"general": {"avg_scored": st/max(pt,1), "goals_scored": st, "goals_conceded": ct, "btts_rate": 0.45, "ht_goal_ratio": 0.27, "tempo_score": 2.5}, "home": {"avg_scored": sh/max(ph,1), "goals_scored": sh, "goals_conceded": 0}, "away": {"avg_scored": sa/max(pa,1), "goals_scored": sa, "goals_conceded": 0}}

def get_fixtures(date):
    r = requests.get(BASE_URL+"/fixtures", headers=HEADERS, params={"date": date, "timezone": "Europe/Istanbul"}, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_team_stats(team_id, league_id, season):
    r = requests.get(BASE_URL+"/teams/statistics", headers=HEADERS, params={"team": team_id, "league": league_id, "season": season}, timeout=30)
    r.raise_for_status()
    return parse_team_stats(r.json().get("response", {}))
