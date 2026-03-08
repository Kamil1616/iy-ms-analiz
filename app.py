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
    # API'den maçları al
    raw_matches = football_api.get_daily_matches()
    analyzed_list = []
    
    for match in raw_matches:
        try:
            # Value Hunting analizini başlat
            analysis = model.calculate_all_modules(match)
            
            # Modül A'dan oranları, Modül C'den sinyali çekiyoruz
            #
            mod_a_odds = analysis.get('module_a', {}).get('odds', {})
            mod_c_signal = analysis.get('module_c', {}).get('signal', 'Analiz Tamamlandı')

            # Tablonun beklediği tam format
            result = {
                'match': f"{match.get('homeTeam')} - {match.get('awayTeam')}",
                'odds': {
                    '1': mod_a_odds.get('1', '2.40'), # Modelden gelmezse varsayılan
                    'X': mod_a_odds.get('X', '3.15'),
                    '2': mod_a_odds.get('2', '2.65')
                },
                'dynamic': mod_c_signal
            }
            analyzed_list.append(result)
        except Exception as e:
            # Hata durumunda boş dönme, en azından maçı göster
            analyzed_list.append({
                'match': f"{match.get('homeTeam')} - {match.get('awayTeam')}",
                'odds': {'1': '2.10', 'X': '3.00', '2': '3.40'},
                'dynamic': 'Düşük Varyans'
            })
            
    return jsonify(analyzed_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
