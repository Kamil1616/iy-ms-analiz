from flask import Flask, render_template, jsonify
import os
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
    # 1. API'den veya fallback'ten ham maçları çek
    raw_matches = football_api.get_daily_matches()
    analyzed_list = []
    
    for match in raw_matches:
        try:
            # 2. Value Hunting modelini çalıştır (Poisson/Dixon-Coles)
            analysis = model.calculate_all_modules(match)
            
            # 3. TABLO FORMATI İÇİN VERİ PAKETLEME
            # Model çıktılarını güvenli bir şekilde alıyoruz
            mod_a = analysis.get('module_a', {})
            mod_c = analysis.get('module_c', {})
            
            result = {
                'match': f"{match.get('homeTeam')} - {match.get('awayTeam')}",
                'odds': {
                    '1': mod_a.get('odds', {}).get('1', '2.50'), # Varsayılan değerler eklendi
                    'X': mod_a.get('odds', {}).get('X', '3.10'),
                    '2': mod_a.get('odds', {}).get('2', '2.70')
                },
                'dynamic': mod_c.get('signal', 'Dengeli Varyans'),
                'iy_prob': analysis.get('module_b', {}).get('over_1_5_prob', 0)
            }
            analyzed_list.append(result)
        except Exception as e:
            print(f"Model Hatası: {e}")
            continue
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
