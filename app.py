from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
from api.football_api import FootballAPI
from models.value_hunting import ValueHuntingModel

# 1. GUNICORN'UN BULABİLMESİ İÇİN APP NESNESİ BURADA OLMALI
app = Flask(__name__)

# Modülleri başlat
football_api = FootballAPI()
model = ValueHuntingModel()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dates')
def get_dates():
    today = datetime.now().strftime('%Y-%m-%d')
    return jsonify([today])

@app.route('/api/fixtures')
def get_fixtures():
    # API'den verileri çek
    raw_matches = football_api.get_daily_matches()
    
    if not raw_matches:
        return jsonify([])

    analyzed_list = []
    for match in raw_matches:
        # Value Hunting analizini yap
        analysis = model.calculate_all_modules(match)
        
        # Frontend için gerekli alanları eşle
        analysis['league'] = match.get('league', 'Diğer')
        analysis['homeTeam'] = match.get('homeTeam')
        analysis['awayTeam'] = match.get('awayTeam')
        # Saat formatını ayarla (20:30 gibi)
        if 'utcDate' in match:
            analysis['time'] = match['utcDate'][11:16]
        
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)

# Render için port ayarı
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
