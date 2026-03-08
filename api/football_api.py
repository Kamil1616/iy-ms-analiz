import os
import requests

# football-data.org - ANA KAYNAK
# Render'da FOOTBALL_API_KEY olarak tanımlı
FD_KEY = os.environ.get("FOOTBALL_API_KEY", "") or os.environ.get("FOOTBALL_DATA_KEY", "")
FD_URL = "https://api.football-data.org/v4"
FD_HEADERS = {"X-Auth-Token": FD_KEY}

# AllSports - YEDEK KAYNAK
AS_KEY = os.environ.get("ALLSPORTS_KEY", "")
AS_URL = "https://apiv2.allsportsapi.com/football"

# football-data.org lig kodları → bizim league_id eşleştirmesi
FD_LEAGUE_MAP = {
    # Lig ID (API-Football) → football-data.org competition code
    39: "PL",    # Premier League
    140: "PD",   # La Liga
    135: "SA",   # Serie A
    78: "BL1",   # Bundesliga
    61: "FL1",   # Ligue 1
    88: "DED",   # Eredivisie
    94: "PPL",   # Primeira Liga
    106: "ELC",  # Championship
    2: "CL",     # Champions League
    3: "EL",     # Europa League
    848: "ECL",  # Conference League
    103: "EL",   # Eliteserien (Norway) - yaklaşık
    113: "PPL",  # Allsvenskan yaklaşık
}

def default_stats():
    return {
        "home_attack": 1.0,
        "home_defence": 1.0,
        "away_attack": 1.0,
        "away_defence": 1.0,
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

# ── football-data.org fixtures ────────────────────────
def get_fixtures_fd(date):
    """football-data.org'dan maç listesi"""
    try:
        from datetime import datetime as dt2, timedelta
        date_plus = (dt2.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        r = requests.get(
            f"{FD_URL}/matches",
            headers=FD_HEADERS,
            params={"dateFrom": date, "dateTo": date_plus},
            timeout=30
        )
        if r.status_code != 200:
            return []
        data = r.json()
        matches = data.get("matches", [])
        result = []
        for m in matches:
            comp = m.get("competition", {})
            home = m.get("homeTeam", {})
            away = m.get("awayTeam", {})
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            status = m.get("status", "TIMED")

            # Status mapping
            st_map = {
                "IN_PLAY": "1H", "HALFTIME": "HT",
                "FINISHED": "FT", "TIMED": "NS",
                "SCHEDULED": "NS", "POSTPONED": "PST"
            }

            result.append({
                "fixture_id": m.get("id"),
                "date": m.get("utcDate"),
                "status": st_map.get(status, "NS"),
                "elapsed": None,
                "home_team_id": home.get("id"),
                "home_team_name": home.get("name") or home.get("shortName"),
                "away_team_id": away.get("id"),
                "away_team_name": away.get("name") or away.get("shortName"),
                "home_goals": ft.get("home"),
                "away_goals": ft.get("away"),
                "league_id": comp.get("id"),
                "league_name": comp.get("name"),
                "season": None,
                "fd_competition_code": comp.get("code"),
            })
        return result
    except Exception as e:
        print(f"FD fixtures error: {e}")
        return []

def get_fixtures(date):
    """Ana fixture fonksiyonu - football-data.org kullan"""
    fixtures = get_fixtures_fd(date)
    if fixtures:
        return _convert_to_apifootball_format(fixtures)
    return []

def _convert_to_apifootball_format(fixtures):
    """football-data.org formatını iç formata çevir"""
    result = []
    for f in fixtures:
        result.append({
            "fixture": {
                "id": f["fixture_id"],
                "date": f["date"],
                "status": {"short": f["status"], "elapsed": f["elapsed"]}
            },
            "teams": {
                "home": {"id": f["home_team_id"], "name": f["home_team_name"]},
                "away": {"id": f["away_team_id"], "name": f["away_team_name"]}
            },
            "goals": {"home": f["home_goals"], "away": f["away_goals"]},
            "league": {
                "id": f["league_id"],
                "name": f["league_name"],
                "season": f.get("season"),
                "fd_code": f.get("fd_competition_code")
            }
        })
    return result

# ── football-data.org team stats ──────────────────────
def get_team_stats_fd(team_id, competition_code, season=None):
    """football-data.org'dan takım son maçlarını çek"""
    try:
        # Son 10 maç
        r = requests.get(
            f"{FD_URL}/teams/{team_id}/matches",
            headers=FD_HEADERS,
            params={"status": "FINISHED", "limit": 10},
            timeout=30
        )
        if r.status_code != 200:
            return None
        matches = r.json().get("matches", [])
        if not matches:
            return None
        return stats_from_fd_matches(matches, team_id)
    except Exception as e:
        print(f"FD team stats error: {e}")
        return None

def stats_from_fd_matches(matches, team_id):
    """football-data.org maçlarından istatistik üret"""
    home_scored, home_conceded = [], []
    away_scored, away_conceded = [], []
    scored_all, conceded_all = [], []

    for m in matches:
        home_team = m.get("homeTeam", {})
        away_team = m.get("awayTeam", {})
        score = m.get("score", {})
        ft = score.get("fullTime", {})

        is_home = home_team.get("id") == team_id
        gf_raw = ft.get("home") if is_home else ft.get("away")
        ga_raw = ft.get("away") if is_home else ft.get("home")

        if gf_raw is None or ga_raw is None:
            continue

        gf = int(gf_raw)
        ga = int(ga_raw)

        scored_all.append(gf)
        conceded_all.append(ga)

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
    ht_ratio = 0.27  # football-data.org free plan'da HT skoru yok

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
            "tempo_score": (avg_st + avg_ct)
        },
        "home": {
            "avg_scored": avg_sh,
            "goals_scored": sum(home_scored),
            "goals_conceded": sum(home_conceded)
        },
        "away": {
            "avg_scored": avg_sa,
            "goals_scored": sum(away_scored),
            "goals_conceded": sum(away_conceded)
        }
    }

# ── AllSports yedek ───────────────────────────────────
def get_team_stats_allsports(team_id):
    """AllSports API'den son maçları çek"""
    try:
        r = requests.get(
            AS_URL,
            params={
                "met": "Fixtures",
                "APIkey": AS_KEY,
                "teamId": team_id,
                "from": "2024-07-01",
                "to": "2026-12-31"
            },
            timeout=30
        )
        if r.status_code != 200:
            return None
        data = r.json()
        matches = data.get("result", [])
        if not matches:
            return None
        # Son 10 tamamlanmış maç
        finished = [m for m in matches if m.get("event_final_result")][-10:]
        if not finished:
            return None
        return stats_from_allsports_matches(finished, team_id)
    except Exception as e:
        print(f"AllSports error: {e}")
        return None

def stats_from_allsports_matches(matches, team_id):
    home_scored, home_conceded = [], []
    away_scored, away_conceded = [], []
    scored_all, conceded_all = [], []

    for m in matches:
        home_id = int(m.get("event_home_team_id", 0))
        result = m.get("event_final_result", "")
        if not result or "-" not in result:
            continue
        parts = result.split(" - ")
        if len(parts) != 2:
            continue
        try:
            hg, ag = int(parts[0].strip()), int(parts[1].strip())
        except:
            continue

        is_home = home_id == int(team_id)
        gf = hg if is_home else ag
        ga = ag if is_home else hg

        scored_all.append(gf)
        conceded_all.append(ga)
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

    return {
        "home_attack": round(avg_sh / lig_ort if avg_sh > 0 else 1.0, 4),
        "home_defence": round(avg_ch / lig_ort if avg_ch > 0 else 1.0, 4),
        "away_attack": round(avg_sa / lig_ort if avg_sa > 0 else 1.0, 4),
        "away_defence": round(avg_ca / lig_ort if avg_ca > 0 else 1.0, 4),
        "general": {
            "avg_scored": avg_st,
            "goals_scored": sum(scored_all),
            "goals_conceded": sum(conceded_all),
            "btts_rate": btts,
            "ht_goal_ratio": 0.27,
            "tempo_score": avg_st + avg_ct
        },
        "home": {"avg_scored": avg_sh, "goals_scored": sum(home_scored), "goals_conceded": sum(home_conceded)},
        "away": {"avg_scored": avg_sa, "goals_scored": sum(away_scored), "goals_conceded": sum(away_conceded)}
    }

# ── ANA get_team_stats ────────────────────────────────
def get_team_stats(team_id, league_id, season):
    # 1. football-data.org
    comp_code = FD_LEAGUE_MAP.get(league_id)
    stats = get_team_stats_fd(team_id, comp_code, season)
    if stats and stats["general"]["goals_scored"] > 0:
        return stats

    # 2. AllSports yedek
    stats = get_team_stats_allsports(team_id)
    if stats and stats["general"]["goals_scored"] > 0:
        return stats

    return default_stats()
