import os
import requests

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = os.environ.get("API_FOOTBALL_HOST", "v3.football.api-sports.io")
BASE_URL = "https://" + API_HOST
HEADERS = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": API_HOST}

FD_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

AS_KEY = os.environ.get("ALLSPORTS_KEY", "")
AS_URL = "https://apiv2.allsportsapi.com/football"

def default_stats():
    return {
        "home_attack": 1.5,
        "home_defence": 1.2,
        "away_attack": 1.1,
        "away_defence": 1.4,
        "general": {
            "avg_scored": 1.35,
            "goals_scored": 27,
            "goals_conceded": 20,
            "btts_rate": 0.45,
            "ht_goal_ratio": 0.27,
            "tempo_score": 2.5
        },
        "home": {"avg_scored": 1.5, "goals_scored": 15, "goals_conceded": 10},
        "away": {"avg_scored": 1.1, "goals_scored": 12, "goals_conceded": 14}
    }

def get_fixtures(date):
    r = requests.get(BASE_URL + "/fixtures", headers=HEADERS,
                     params={"date": date, "timezone": "Europe/Istanbul"}, timeout=30)
    r.raise_for_status()
    return r.json().get("response", [])

def parse_team_stats(data):
    if not data:
        return default_stats()
    goals = data.get("goals", {})
    fix = data.get("fixtures", {})

    ph = fix.get("played", {}).get("home", 0)
    pa = fix.get("played", {}).get("away", 0)
    pt = fix.get("played", {}).get("total", 0)

    # Attakc (atılan)
    sh = goals.get("for", {}).get("total", {}).get("home", 0)
    sa = goals.get("for", {}).get("total", {}).get("away", 0)
    st = goals.get("for", {}).get("total", {}).get("total", 0)

    # Defence (yenilen)
    ch = goals.get("against", {}).get("total", {}).get("home", 0)
    ca = goals.get("against", {}).get("total", {}).get("away", 0)
    ct = goals.get("against", {}).get("total", {}).get("total", 0)

    if pt == 0 or st == 0:
        return default_stats()

    avg_sh = sh / max(ph, 1)
    avg_sa = sa / max(pa, 1)
    avg_st = st / max(pt, 1)
    avg_ch = ch / max(ph, 1)
    avg_ca = ca / max(pa, 1)
    avg_ct = ct / max(pt, 1)

    # Lig ortalaması varsayılan 1.35 gol/maç
    lig_ort = 1.35

    # Dixon-Coles attack/defence katsayıları
    # attack = takımın attığı / lig ortalaması
    # defence = takımın yediği / lig ortalaması (düşük = iyi savunma)
    home_attack = avg_sh / lig_ort if avg_sh > 0 else 1.0
    away_attack = avg_sa / lig_ort if avg_sa > 0 else 1.0
    home_defence = avg_ch / lig_ort if avg_ch > 0 else 1.0
    away_defence = avg_ca / lig_ort if avg_ca > 0 else 1.0

    btts = 0.45
    ht_ratio = 0.27

    return {
        "home_attack": round(home_attack, 4),
        "home_defence": round(home_defence, 4),
        "away_attack": round(away_attack, 4),
        "away_defence": round(away_defence, 4),
        "general": {
            "avg_scored": avg_st,
            "goals_scored": st,
            "goals_conceded": ct,
            "btts_rate": btts,
            "ht_goal_ratio": ht_ratio,
            "tempo_score": 2.5
        },
        "home": {"avg_scored": avg_sh, "goals_scored": sh, "goals_conceded": ch},
        "away": {"avg_scored": avg_sa, "goals_scored": sa, "goals_conceded": ca}
    }

def stats_from_matches(matches, team_id):
    home_scored, home_conceded = [], []
    away_scored, away_conceded = [], []
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
            home_scored.append(gf)
            home_conceded.append(ga)
        else:
            away_scored.append(gf)
            away_conceded.append(ga)

    if not scored_all:
        return default_stats()

    lig_ort = 1.35
    avg_sh = sum(home_scored) / max(len(home_scored), 1)
    avg_sa = sum(away_scored) / max(len(away_scored), 1)
    avg_ch = sum(home_conceded) / max(len(home_conceded), 1)
    avg_ca = sum(away_conceded) / max(len(away_conceded), 1)
    avg_st = sum(scored_all) / len(scored_all)
    avg_ct = sum(conceded_all) / len(conceded_all)

    avg_ht = sum(ht_scored_all) / len(ht_scored_all)
    ht_ratio = max(0.15, min(0.55, avg_ht / avg_st if avg_st > 0 else 0.27))
    btts = sum(1 for s, c in zip(scored_all, conceded_all) if s > 0 and c > 0) / len(scored_all)

    home_attack = avg_sh / lig_ort if avg_sh > 0 else 1.0
    away_attack = avg_sa / lig_ort if avg_sa > 0 else 1.0
    home_defence = avg_ch / lig_ort if avg_ch > 0 else 1.0
    away_defence = avg_ca / lig_ort if avg_ca > 0 else 1.0

    return {
        "home_attack": round(home_attack, 4),
        "home_defence": round(home_defence, 4),
        "away_attack": round(away_attack, 4),
        "away_defence": round(away_defence, 4),
        "general": {
            "avg_scored": avg_st,
            "goals_scored": sum(scored_all),
            "goals_conceded": sum(conceded_all),
            "btts_rate": btts,
            "ht_goal_ratio": ht_ratio,
            "tempo_score": 2.5
        },
        "home": {"avg_scored": avg_sh, "goals_scored": sum(home_scored), "goals_conceded": sum(home_conceded)},
        "away": {"avg_scored": avg_sa, "goals_scored": sum(away_scored), "goals_conceded": sum(away_conceded)}
    }

def get_team_stats(team_id, league_id, season):
    # 1. API-Football resmi istatistik
    try:
        r = requests.get(BASE_URL + "/teams/statistics", headers=HEADERS,
                         params={"team": team_id, "league": league_id, "season": season}, timeout=30)
        r.raise_for_status()
        data = r.json().get("response", {})
        parsed = parse_team_stats(data)
        if parsed["general"]["goals_scored"] > 0:
            return parsed
    except:
        pass

    # 2. API-Football son 15 maç
    try:
        r = requests.get(BASE_URL + "/fixtures", headers=HEADERS,
                         params={"team": team_id, "last": 15, "status": "FT"}, timeout=30)
        r.raise_for_status()
        matches = r.json().get("response", [])
        if matches:
            parsed = stats_from_matches(matches, team_id)
            if parsed["general"]["goals_scored"] > 0:
                return parsed
    except:
        pass

    return default_stats()
