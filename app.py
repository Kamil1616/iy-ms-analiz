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
    return jsonify([datetime.now().strftime('%Y-%m-%d')])

@app.route('/api/fixtures')
def get_fixtures():
    raw_matches = football_api.get_daily_matches()
    analyzed_list = []
    
    for match in raw_matches:
        try:
            # Value Hunting analizini yap (Modül A, B, C)
            analysis = model.calculate_all_modules(match)
            
            # ARAYÜZÜN HER İHTİMALİNİ KAPSIYORUZ
            result = {
                # Ev Sahibi (Her iki formatta)
                'homeTeam': match.get('homeTeam'),
                'home_team': match.get('homeTeam'),
                
                # Deplasman (Her iki formatta)
                'awayTeam': match.get('awayTeam'),
                'away_team': match.get('awayTeam'),
                
                # Diğer Bilgiler
                'league': match.get('league', 'Analiz'),
                'competition': match.get('league', 'Analiz'),
                'time': match.get('utcDate', '20:00')[11:16],
                
                # Analiz Verileri
                'analysis': analysis
            }
            analyzed_list.append(result)
        except Exception as e:
            continue
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
