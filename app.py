from flask import Flask, render_template, jsonify
from api.football_api import FootballAPI
from models.value_hunting import ValueHuntingModel
import os

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
            # Senin 12 adımlı modelin tam kapasite çalışıyor
            analysis = model.calculate_all_modules(match)
            
            # Veriyi senin tablo formatına uygun şekilde hazırlıyoruz
            result = {
                'match': f"{match.get('homeTeam')} - {match.get('awayTeam')}",
                'odds': analysis.get('module_a', {}).get('odds', {'1': '-', 'X': '-', '2': '-'}),
                'dynamic': analysis.get('module_c', {}).get('signal', 'Analiz Bekleniyor'),
                'iy_prob': analysis.get('module_b', {}).get('over_1_5_prob', 0)
            }
            analyzed_list.append(result)
        except:
            continue
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
