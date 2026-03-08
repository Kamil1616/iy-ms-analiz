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

@app.route('/api/fixtures')
def get_fixtures():
    raw_matches = football_api.get_daily_matches()
    analyzed_list = []
    
    for match in raw_matches:
        try:
            # Senin 12 adımlı modelin çalışıyor (Dixon-Coles, Poisson vb.)
            #
            raw_analysis = model.calculate_all_modules(match)
            
            # FRONTEND'DEKİ 'signal' HATASINI ÇÖZEN YAPI
            analysis_package = {
                "module_c": {
                    "signal": raw_analysis.get('module_c', {}).get('signal', 'Sinyal Yok')
                },
                "module_b": {
                    "over_1_5_prob": raw_analysis.get('module_b', {}).get('over_1_5_prob', 0)
                }
            }
            
            result = {
                'homeTeam': match.get('homeTeam'),
                'awayTeam': match.get('awayTeam'),
                'league': match.get('league', 'Analiz'),
                'time': match.get('utcDate', '20:00')[11:16],
                'analysis': analysis_package # İşte o 'signal' burada!
            }
            analyzed_list.append(result)
        except Exception as e:
            print(f"Hata: {e}")
            continue
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
