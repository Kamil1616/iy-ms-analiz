import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")

from api.football_api import get_fixtures, get_team_stats
from api import cache
from models.value_hunting import run_analysis


def get_fixtures_for_date(date_str):
    cached = cache.get(f"fixtures_{date_str}", ttl_minutes=30)
    if cached:
        return cached
    raw = get_fixtures(date_str)
    ALLOWED = {2,3,39,40,41,42,61,62,78,79,88,89,94,95,98,99,103,104,106,107,
               113,114,119,135,136,140,141,144,169,170,172,173,179,180,188,197,
               198,203,204,207,208,210,211,218,235,244,253,262,263,271,283,286,
               292,293,296,299,323,330,331,332,345,348,356,357,358,431,462,463,
               667,848}
    fixtures = []
    for f in raw:
        if f.get("league", {}).get("id") not in ALLOWED:
            continue
        fix = f.get("fixture", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        league = f.get("league", {})
        fixtures.append({
            "fixture_id": fix.get("id"),
            "date": fix.get("date"),
            "status": fix.get("status", {}).get("short"),
            "elapsed": fix.get("status", {}).get("elapsed"),
            "home_team_id": teams.get("home", {}).get("id"),
            "home_team_name": teams.get("home", {}).get("name"),
            "away_team_id": teams.get("away", {}).get("id"),
            "away_team_name": teams.get("away", {}).get("name"),
            "home_goals": goals.get("home"),
            "away_goals": goals.get("away"),
            "league_id": league.get("id"),
            "league_name": league.get("name"),
            "season": league.get("season"),
        })
    cache.set(f"fixtures_{date_str}", fixtures)
    return fixtures


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/fixtures")
def api_fixtures():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        fixtures = get_fixtures_for_date(date)
        return jsonify({"fixtures": fixtures, "date": date})
    except Exception as e:
        return jsonify({"error": str(e), "fixtures": []}), 500


@app.route("/api/analyze/<int:fixture_id>")
def api_analyze(fixture_id):
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        fixtures = get_fixtures_for_date(date)
        fix = next((f for f in fixtures if f["fixture_id"] == fixture_id), None)
        if not fix:
            return jsonify({"error": "Mac bulunamadi"}), 404

        analysis_key = f"analysis_{fixture_id}"
        cached = cache.get(analysis_key, ttl_minutes=60)
        if cached:
            return jsonify({"fixture": fix, "analysis": cached})

        season = fix.get("season") or 2024
        league_id = fix.get("league_id") or 39

        home_stats = get_team_stats(fix["home_team_id"], league_id, season)
        away_stats = get_team_stats(fix["away_team_id"], league_id, season)

        # Default stats kullanılıyorsa uyar
        home_is_default = home_stats["general"]["goals_scored"] == 27
        away_is_default = away_stats["general"]["goals_scored"] == 27

        analysis = run_analysis(
            home_stats_general=home_stats["general"],
            home_stats_home=home_stats["home"],
            away_stats_general=away_stats["general"],
            away_stats_away=away_stats["away"],
            home_stats=home_stats,
            away_stats=away_stats,
        )
        analysis["data_warning"] = home_is_default or away_is_default
        cache.set(analysis_key, analysis)
        return jsonify({"fixture": fix, "analysis": analysis})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/analyze-all")
def api_analyze_all():
    date = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        fixtures = get_fixtures_for_date(date)
        results = []
        for fix in fixtures[:50]:
            try:
                analysis_key = f"analysis_{fix['fixture_id']}"
                cached = cache.get(analysis_key, ttl_minutes=60)
                if cached:
                    results.append({"fixture": fix, "analysis": cached})
                    continue
                season = fix.get("season") or 2024
                league_id = fix.get("league_id") or 39
                home_stats = get_team_stats(fix["home_team_id"], league_id, season)
                away_stats = get_team_stats(fix["away_team_id"], league_id, season)
                analysis = run_analysis(
                    home_stats_general=home_stats["general"],
                    home_stats_home=home_stats["home"],
                    away_stats_general=away_stats["general"],
                    away_stats_away=away_stats["away"],
                    home_stats=home_stats,
                    away_stats=away_stats,
                )
                cache.set(analysis_key, analysis)
                results.append({"fixture": fix, "analysis": analysis})
            except:
                continue
        return jsonify({"results": results, "date": date})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/clear-cache", methods=["POST","GET"])
def clear_cache():
    import shutil
    cache_dir = "instance/cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        os.makedirs(cache_dir, exist_ok=True)
    return jsonify({"status": "ok", "message": "Cache temizlendi"})


@app.route("/api/debug")
def api_debug():
    import requests as req
    date = datetime.now().strftime("%Y-%m-%d")
    key = os.environ.get("API_FOOTBALL_KEY","")
    host = os.environ.get("API_FOOTBALL_HOST","v3.football.api-sports.io")
    try:
        r = req.get(f"https://{host}/fixtures",
                    headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
                    params={"date": date, "timezone": "Europe/Istanbul"}, timeout=15)
        data = r.json()
        return jsonify({
            "status": r.status_code,
            "results": data.get("results", 0),
            "errors": data.get("errors", {}),
            "date": date,
            "key_set": bool(key),
            "remaining": r.headers.get("x-ratelimit-requests-remaining","?")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/dates")
def api_dates():
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-1, 4)]
    return jsonify({"dates": dates})


if __name__ == "__main__":
    os.makedirs("instance/cache", exist_ok=True)
    app.run(debug=True, port=5000)
