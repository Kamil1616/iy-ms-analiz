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

@app.route('/api/analyze')
def analyze():
    # 1. Güncel maç verilerini API'den çek
    raw_matches = football_api.get_daily_matches()
    
    if not raw_matches:
        return jsonify([])

    # 2. Her maçı Value Hunting modeline sok
    analyzed_list = []
    for match in raw_matches:
        # Modelin hesaplama fonksiyonunu çağırıyoruz
        analysis = model.calculate_value(match)
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)

if __name__ == '__main__':
    # Render.com için port ayarı
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
