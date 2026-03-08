from flask import Flask, render_template, jsonify
import os
from datetime import datetime
from api.football_api import FootballAPI
from models.value_hunting import ValueHuntingModel

app = Flask(__name__)

football_api = FootballAPI()
model = ValueHuntingModel()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dates')
def get_dates():
    # Arayüzün tarih listesini doldurması için
    return jsonify([datetime.now().strftime('%Y-%m-%d')])

@app.route('/api/fixtures')
def get_fixtures():
    # 1. Önce API'den veya Fallback'ten maçları al
    raw_matches = football_api.get_daily_matches()
    
    analyzed_list = []
    
    # 2. Maçları analiz et ve arayüzün (JS) beklediği formatta paketle
    for match in raw_matches:
        try:
            # Model hesaplamalarını yap (Poisson, Dixon-Coles vb.)
            analysis = model.calculate_all_modules(match)
            
            # ARAYÜZÜN BEKLEDİĞİ KRİTİK ALANLAR (Hata buradaydı)
            result = {
                'homeTeam': match.get('homeTeam'),
                'awayTeam': match.get('awayTeam'),
                'league': match.get('league', 'Analiz Ligi'),
                'time': match.get('utcDate', '20:00')[11:16],
                'analysis': analysis # Modül A, B, C verileri burada
            }
            analyzed_list.append(result)
        except Exception as e:
            print(f"Maç analiz hatası: {e}")
            continue
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
