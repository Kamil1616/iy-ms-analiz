import os
import requests
from datetime import datetime, timedelta

AS_KEY = os.environ.get("ALLSPORTS_KEY", "")
AS_URL = "https://apiv2.allsportsapi.com/football"

FD_KEY = os.environ.get("FOOTBALL_API_KEY", "") or os.environ.get("FOOTBALL_DATA_KEY", "")
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

def default_stats():
    return {
        "home_attack": 1.0, "home_defence": 1.0,
        "away_attack": 1.0, "away_defence": 1.0,
        "general": {
            "avg_scored": 1.35, "goals_scored": 27, "goals_conceded": 20,
            "btts_rate": 0.45, "ht_goal_ratio": 0.27, "tempo_score": 2.5
        },
        "home": {"avg_scored": 1.5, "goals_scored": 15, "goals_conceded": 10},
        "away": {"avg_scored": 1.1, "goals_scored": 12, "goals_conceded": 14}
    }

def get_fixtures_allsports(date):
    try:
        r = requests.get(AS_URL, params={
            "met": "Fixtures", "APIkey": AS_KEY, "from": date, "to": date
        }, timeout=30)
        if r.status_code != 200:
            return []
        matches = r.json().get("result", []) or []
        result = []
        for m in matches:
            home_goals = None
            away_goals = None
            final = m.get("event_final_result", "")
            if final and " - " in final:
                parts = final.split(" - ")
                try:
                    home_goals = int(parts[0].strip())
                    away_goals = int(parts[1].strip())
                except:
                    pass
            status_raw = str(m.get("event_status", ""))
            if status_raw == "Finished":
                status = "FT"
            elif "'" in status_raw:
                status = "1H"
            else:
                status = "NS"
            elapsed = None
            if "'" in status_raw:
                try:
                    elapsed = int(status_raw.replace("'", ""))
                except:
                    pass
            result.append({
                "fixture": {
                    "id": int(m.get("event_key", 0)),
                    "date": m.get("event_date", date) + "T" + m.get("event_time", "00:00") + ":00+01:00",
                    "status": {"short": status, "elapsed": elapsed}
                },
                "teams": {
                    "home": {"id": int(m.get("home_team_key", 0)), "name": m.get("event_home_team", "")},
                    "away": {"id": int(m.get("away_team_key", 0)), "name": m.get("event_away_team", "")}
                },
                "goals": {"home": home_goals, "away": away_goals},
                "league": {
                    "id": int(m.get("league_key", 0)),
                    "name": m.get("league_name", ""),
                    "season": m.get("league_year", ""),
                    "country": m.get("country_name", "")
                }
            })
        return result
    except Exception as e:
        print(f"AllSports fixtures error: {e}")
        return []

def get_fixtures(date):
    fixtures = get_fixtures_allsports(date)
    if fixtures:
        return fixtures
    return get_fixtures_fd(date)

def get_team_stats_allsports(team_id):
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        r = requests.get(AS_URL, params={
            "met": "Fixtures", "APIkey": AS_KEY,
            "teamId": team_id, "from": from_date, "to": today
        }, timeout=30)
        if r.status_code != 200:
            return None
        matches = r.json().get("result", []) or []
        finished = [m for m in matches if m.get("event_status") == "Finished" and m.get("event_final_result")]
        finished = finished[-10:]
        if not finished:
            return None
        return stats_from_allsports(finished, team_id)
    except Exception as e:
        print(f"AllSports team stats error: {e}")
        return None

def stats_from_allsports(matches, team_id):
    home_scored, home_conceded = [], []
    away_scored, away_conceded = [], []
    scored_all, conceded_all, ht_scored_all = [], [], []
    for m in matches:
        home_id = int(m.get("home_team_key", 0))
        is_home = home_id == int(team_id)
        final = m.get("event_final_result", "")
        if not final or " - " not in final:
            continue
        parts = final.split(" - ")
        try:
            hg, ag = int(parts[0].strip()), int(parts[1].strip())
        except:
            continue
        gf = hg if is_home else ag
        ga = ag if is_home else hg
        ht = m.get("event_halftime_result", "")
        ht_gf = 0
        if ht and " - " in ht:
            ht_parts = ht.split(" - ")
            try:
                ht_gf = int(ht_parts[0].strip()) if is_home else int(ht_parts[1].strip())
            except:
                pass
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
        return None
    lig_ort = 1.35
    avg_sh = sum(home_scored) / max(len(home_scored), 1)
    avg_sa = sum(away_scored) / max(len(away_scored), 1)
    avg_ch = sum(home_conceded) / max(len(home_conceded), 1)
    avg_ca = sum(away_conceded) / max(len(away_conceded), 1)
    avg_st = sum(scored_all) / len(scored_all)
    avg_ct = sum(conceded_all) / len(conceded_all)
    btts = sum(1 for s, c in zip(scored_all, conceded_all) if s > 0 and c > 0) / len(scored_all)
    total_ft = sum(scored_all)
    ht_ratio = max(0.15, min(0.55, sum(ht_scored_all) / total_ft if total_ft > 0 else 0.27))
    return {
        "home_attack":  round(avg_sh / lig_ort if avg_sh > 0 else 1.0, 4),
        "home_defence": round(avg_ch / lig_ort if avg_ch > 0 else 1.0, 4),
        "away_attack":  round(avg_sa / lig_ort if avg_sa > 0 else 1.0, 4),
        "away_defence": round(avg_ca / lig_ort if avg_ca > 0 else 1.0, 4),
        "general": {
            "avg_scored": avg_st, "goals_scored": sum(scored_all),
            "goals_conceded": sum(conceded_all), "btts_rate": btts,
            "ht_goal_ratio": ht_ratio, "tempo_score": avg_st + avg_ct
        },
        "home": {"avg_scored": avg_sh, "goals_scored": sum(home_scored), "goals_conceded": sum(home_conceded)},
        "away": {"avg_scored": avg_sa, "goals_scored": sum(away_scored), "goals_conceded": sum(away_conceded)}
    }

def get_fixtures_fd(date):
    try:
        date_plus = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        r = requests.get(f"{FD_URL}/matches", headers=FD_HEADERS,
            params={"dateFrom": date, "dateTo": date_plus}, timeout=30)
        if r.status_code != 200:
            return []
        matches = r.json().get("matches", [])
        result = []
        for m in matches:
            comp = m.get("competition", {})
            home = m.get("homeTeam", {})
            away = m.get("awayTeam", {})
            ft = m.get("score", {}).get("fullTime", {})
            status = m.get("status", "TIMED")
            st_map = {"IN_PLAY": "1H", "HALFTIME": "HT", "FINISHED": "FT", "TIMED": "NS", "SCHEDULED": "NS"}
            result.append({
                "fixture": {"id": m.get("id"), "date": m.get("utcDate"),
                    "status": {"short": st_map.get(status, "NS"), "elapsed": None}},
                "teams": {"home": {"id": home.get("id"), "name": home.get("name")},
                    "away": {"id": away.get("id"), "name": away.get("name")}},
                "goals": {"home": ft.get("home"), "away": ft.get("away")},
                "league": {"id": comp.get("id"), "name": comp.get("name"), "season": None}
            })
        return result
    except Exception as e:
        print(f"FD fixtures error: {e}")
        return []

def get_team_stats(team_id, league_id, season):
    stats = get_team_stats_allsports(team_id)
    if stats and stats["general"]["goals_scored"] > 0:
        return stats
    return default_stats()
