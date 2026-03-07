import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, jsonify, request
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

from api.football_api import (
    get_todays_fixtures, get_tomorrows_fixtures, get_fixtures_by_date,
    get_team_last_matches, get_team_last_home_matches, get_team_last_away_matches,
    parse_match_data, extract_team_stats
)
from api import cache
from models.value_hunting import run_analysis

def get_fixtures_for_date(date_str):
    cached = cache.get(f"fixtures_{date_str}", ttl_minutes=30)
    if cached:
        return cached
    try:
        raw = get_fixtures_by_date(date_str)
        fixtures = [parse_match_data(f) for f in raw]
        fixtures = [f for f in fixtures if f["status"] in ("FT", "NS", "1H", "2H", "HT")]
        cache.set(f"fixtures_{date_str}", fixtures)
        return fixtures
    except Exception as e:
        print(f"API error: {e}")
        return []

def get_team_stats(team_id):
    cached = cache.get(f"stats_{team_id}", ttl_minutes=120)
    if cached:
        return cached
    try:
        general = get_team_last_matches(team_id, last=6)
        home = get_team_last_home_matches(team_id, last=6)
        away = get_team_last_away_matches(team_id, last=6)
        stats = {
            "general": extract_team_stats(general, team_id, "general"),
            "home": extract_team_stats(home, team_id, "home"),
            "away": extract_team_stats(away, team_id, "away"),
        }
        cache.set(f"stats_{team_id}", stats)
        return stats
    except Exception as e:
        print(f"Stats error for team {team_id}: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/fixtures")
def api_fixtures():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    fixtures = get_fixtures_for_date(date_str)
    return jsonify({"fixtures": fixtures, "date": date_str})

@app.route("/api/analyze/<int:fixture_id>")
def api_analyze(fixture_id):
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    fixtures = get_fixtures_for_date(date_str)
    fixture = next((f for f in fixtures if f["fixture_id"] == fixture_id), None)
    if not fixture:
        return jsonify({"error": "Mac bulunamadi"}), 404
    home_id = fixture["home_team_id"]
    away_id = fixture["away_team_id"]
    analysis_key = f"analysis_{fixture_id}"
    cached_analysis = cache.get(analysis_key, ttl_minutes=240)
    if cached_analysis:
        return jsonify({"fixture": fixture, "analysis": cached_analysis})
    home_stats = get_team_stats(home_id)
    away_stats = get_team_stats(away_id)
    if not home_stats or not away_stats:
        return jsonify({"error": "Takim verileri alinamadi"}), 500
    analysis = run_analysis(
        home_stats_general=home_stats["general"],
        home_stats_home=home_stats["home"],
        away_stats_general=away_stats["general"],
        away_stats_away=away_stats["away"],
    )
    cache.set(analysis_key, analysis)
    return jsonify({"fixture": fixture, "analysis": analysis})

@app.route("/api/analyze-all")
def api_analyze_all():
    date_str = request.args.get("date", datetime.now().strftime("%Y-%m-%d"))
    fixtures = get_fixtures_for_date(date_str)
    results = []
    for fix in fixtures[:50]:
        home_id = fix["home_team_id"]
        away_id = fix["away_team_id"]
        if not home_id or not away_id:
            continue
        analysis_key = f"analysis_{fix['fixture_id']}"
        cached_analysis = cache.get(analysis_key, ttl_minutes=240)
        if cached_analysis:
            results.append({"fixture": fix, "analysis": cached_analysis})
            continue
        home_stats = get_team_stats(home_id)
        away_stats = get_team_stats(away_id)
        if not home_stats or not away_stats:
            continue
        analysis = run_analysis(
            home_stats_general=home_stats["general"],
            home_stats_home=home_stats["home"],
            away_stats_general=away_stats["general"],
            away_stats_away=away_stats["away"],
        )
        cache.set(analysis_key, analysis)
        results.append({"fixture": fix, "analysis": analysis})
    return jsonify({"results": results, "date": date_str, "count": len(results)})

@app.route("/api/dates")
def api_dates():
    today = datetime.now()
    dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(-1, 4)]
    return jsonify({"dates": dates})

if __name__ == "__main__":
    os.makedirs("instance/cache", exist_ok=True)
    app.run(debug=True, port=5000)
