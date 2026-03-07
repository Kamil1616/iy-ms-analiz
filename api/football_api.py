import os
import requests

# API-Football
API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE_URL = "https://" + API_HOST
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}

# Football-Data.org
FD_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

# AllSports API
AS_KEY = os.environ.get("ALLSPORTS_KEY", "")
AS_URL = "https://apiv2.allsportsapi.com/football"

# Football-Data league mapping
FD_LEAGUES = {
    39: 2021, 140: 2014, 135: 2019, 78: 2002, 61: 2015,
    2: 2001, 3: 2119, 848: 2119
}

def default_stats():
    return {
        "general": {"avg_scored": 1.35, "goals_scored": 27, "goals_conceded": 20, "btts_rate": 0.45, "ht_goal_ratio": 0.27, "tempo_score": 2.5},
        "home": {"avg_scored": 1.5, "goals_scored": 15, "goals_conceded": 10},
        "away": {"avg_scored": 1.2, "goals_scored": 12, "goals_conceded": 12}
    }

def get_fixtures(date):
    r = requests.get(BASE_URL+"/fixtures", headers=HEADERS, params={"date": date, "timezone": "Europe/Istanbul"}, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def stats_from_matches(matches, team_id):
    scored_h, conceded_h, scored_a, conceded_a = [], [], [], []
    ht_scored_all, scored_all, conceded_all = [], [], []
    for m in matches:
        teams = m.get("teams", {})
        goals = m.get("goals", {})
        score = m.get("score", {})
        is_home = teams.get("home", {}).get("id") == team_id
        gf = (goals.get("home") or 0) if is_home else (goals.get("away") or 0)
        ga = (goals.get("away") or 0) if is_home else (goals.get("home") or 0)
        ht = score.get("halftime", {}) or {}
        ht_gf = (ht.get("home") or 0) if is_home else (ht.get("away") or 0)
        scored_all.append(gf)
        conceded_all.append(ga)
        ht_scored_all.append(ht_gf)
        if is_home:
            scored_h.append(gf); conceded_h.append(ga)
        else:
            scored_a.append(gf); conceded_a.append(ga)
    if not scored_all:
        return default_stats()
    avg_s = sum(scored_all)/len(scored_all)
    avg_c = sum(conceded_all)/len(conceded_all)
    avg_ht = sum(ht_scored_all)/len(ht_scored_all)
    ht_ratio = max(0.15, min(0.55, avg_ht/avg_s if avg_s > 0 else 0.27))
    btts = sum(1 for s,c in zip(scored_all,conceded_all) if s>0 and c>0)/len(scored_all)
    avg_sh = sum(scored_h)/max(len(scored_h),1)
    avg_sa = sum(scored_a)/max(len(scored_a),1)
    return {
        "general": {"avg_scored": avg_s, "goals_scored": sum(scored_all), "goals_conceded": sum(conceded_all), "btts_rate": btts, "ht_goal_ratio": ht_ratio, "tempo_score": 2.5},
        "home": {"avg_scored": avg_sh, "goals_scored": sum(scored_h), "goals_conceded": sum(conceded_h)},
        "away": {"avg_scored": avg_sa, "goals_scored": sum(scored_a), "goals_conceded": sum(conceded_a)}
    }

def get_stats_from_apifootball(team_id, league_id, season):
    try:
        r = requests.get(BASE_URL+"/fixtures", headers=HEADERS, params={"team": team_id, "last": 15, "status": "FT"}, timeout=30)
        r.raise_for_status()
        matches = r.json().get("response", [])
        if matches:
            return stats_from_matches(matches, team_id)
    except:
        pass
    return None

def get_stats_from_footballdata(team_id, league_id):
    try:
        fd_league = FD_LEAGUES.get(league_id)
        if not fd_league or not FD_KEY:
            return None
        r = requests.get(f"{FD_URL}/competitions/{fd_league}/matches", headers=FD_HEADERS, params={"status": "FINISHED"}, timeout=30)
        if r.status_code != 200:
            return None
        matches_raw = r.json().get("matches", [])
        team_matches = []
        for m in matches_raw:
            home_id = m.get("homeTeam", {}).get("id")
            away_id = m.get("awayTeam", {}).get("id")
            if home_id != team_id and away_id != team_id:
                continue
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            ht = score.get("halfTime", {})
            is_home = home_id == team_id
            team_matches.append({
                "teams": {"home": {"id": home_id}, "away": {"id": away_id}},
                "goals": {"home": ft.get("home", 0), "away": ft.get("away", 0)},
                "score": {"halftime": {"home": ht.get("home", 0), "away": ht.get("away", 0)}}
            })
            if len(team_matches) >= 15:
                break
        if team_matches:
            return stats_from_matches(team_matches, team_id)
    except:
        pass
    return None

def get_stats_from_allsports(team_id):
    try:
        if not AS_KEY:
            return None
        r = requests.get(AS_URL, params={"met": "Fixtures", "APIkey": AS_KEY, "teamId": team_id, "from": "2024-01-01", "to": "2026-03-07"}, timeout=30)
        if r.status_code != 200:
            return None
        data = r.json()
        matches_raw = data.get("result", []) or []
        matches = []
        for m in matches_raw:
            if m.get("event_status") != "Finished":
                continue
            home_id = int(m.get("home_team_key", 0))
            away_id = int(m.get("away_team_key", 0))
            is_home = home_id == team_id
            try:
                hg = int(m.get("event_final_result", "0-0").split("-")[0].strip())
                ag = int(m.get("event_final_result", "0-0").split("-")[1].strip())
                ht_res = m.get("event_halftime_result", "0-0") or "0-0"
                hht = int(ht_res.split("-")[0].strip())
                aht = int(ht_res.split("-")[1].strip())
            except:
                continue
            matches.append({
                "teams": {"home": {"id": home_id}, "away": {"id": away_id}},
                "goals": {"home": hg, "away": ag},
                "score": {"halftime": {"home": hht, "away": aht}}
            })
            if len(matches) >= 15:
                break
        if matches:
            return stats_from_matches(matches, team_id)
    except:
        pass
    return None

def get_team_stats(team_id, league_id, season):
    # 1. API-Football son maçlar
    stats = get_stats_from_apifootball(team_id, league_id, season)
    if stats and stats["general"]["avg_scored"] != 1.35:
        return stats
    # 2. Football-Data.org
    stats = get_stats_from_footballdata(team_id, league_id)
    if stats and stats["general"]["avg_scored"] != 1.35:
        return stats
    # 3. AllSports API
    stats = get_stats_from_allsports(team_id)
    if stats and stats["general"]["avg_scored"] != 1.35:
        return stats
    return default_stats()
