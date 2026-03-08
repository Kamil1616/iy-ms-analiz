from flask import Flask, render_template, jsonify, request
import os
from datetime import datetime
from api.football_api import FootballAPI
from models.value_hunting import ValueHuntingModel

# 1. ÖNCE APP NESNESİNİ TANIMLA (Hata buradaydı)
app = Flask(__name__)

# 2. MODÜLLERİ BAŞLAT
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
    # API'den ham maç verilerini çek
    raw_matches = football_api.get_daily_matches()
    
    if not raw_matches:
        return jsonify([])

    analyzed_list = []
    for match in raw_matches:
        # Value Hunting analizini yap
        analysis = model.calculate_all_modules(match)
        
        # ÖNEMLİ: Frontend'in lig listesini doldurması için 
        # 'competition' veya 'league' bilgisini en üst seviyeye ekle
        analysis['league'] = match.get('league', 'Diğer Ligler')
        analysis['competition'] = match.get('league', 'Diğer Ligler')
        
        # Maç saati ve takımları doğrula
        analysis['homeTeam'] = match.get('homeTeam')
        analysis['awayTeam'] = match.get('awayTeam')
        analysis['time'] = match.get('utcDate', '')[11:16] # "20:30" formatı
        
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
