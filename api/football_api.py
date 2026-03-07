import os
import requests

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE_URL = f"https://{API_HOST}"

HEADERS = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": API_HOST
}

def get_fixtures(date):
    url = f"{BASE_URL}/fixtures"
    params = {"date": date, "timezone": "Europe/Istanbul"}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def get_team_stats(team_id, league_id, season):
    url = f"{BASE_URL}/teams/statistics"
    params = {"team": team_id, "league": league_id, "season": season}
    r = requests.get(url, headers=HEADERS, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("response", {})
    return parse_team_stats(data)

def parse_team_stats(data):
    if not data:
        return default_stats()
    goals = data.get("goals", {})
    fixtures = data.get("fixtures", {})
    played_home = fixtures.get("played", {}).get("home", 10)
    played_away = fixtures.get("played", {}).get("away", 10)
    played_total = fixtures.get("played", {}).get("total", 20)
    scored_home = goals.get("for", {}).get("total", {}).get("home", 15)
    scored_away = goals.get("for", {}).get("total", {}).get("away", 12)
    scored_total = goals.get("for", {}).get("total", {}).get("total", 27)
    conceded_total = goals.get("against", {}).get("total", {}).get("total", 20)
    avg_scored_home = scored_home / max(played_home, 1)
    avg_scored_away = scored_away / max(played_away, 1)
    avg_scored_total = scored_total / max(played_total, 1)
    return {
        "general": {
            "avg_scored": avg_scored_total,
            "goals_scored": scored_total,
            "goals_conceded": conceded_total,
            "btts_rate": 0.45,
            "ht_goal_ratio": 0.27,
            "tempo_score": 2.5
        },
        "home": {
            "avg_scored": avg_scored_home,
            "goals_scored": scored_home,
            "goals_conceded": 0
        },
        "away": {
            "avg_scored": avg_scored_away,
            "goals_scored": scored_away,
            "goals_conceded": 0
        }
    }

def default_stats():
    return {
        "general": {
            "avg_scored": 1.35,
            "goals_scored": 27,
            "goals_conceded": 20,
            "btts_rate": 0.45,
            "ht_goal_ratio": 0.27,
            "tempo_score": 2.5
        },
        "home": {"avg_scored": 1.5, "goals_scored": 15, "goals_conceded": 10},
        "away": {"avg_scored": 1.2, "goals_scored": 12, "goals_conceded": 12}
    }
