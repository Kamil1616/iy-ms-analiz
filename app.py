from flask import Flask, render_template, jsonify, request
from api.football_api import FootballAPI
from models.value_hunting import ValueHuntingModel
import os
from datetime import datetime

app = Flask(__name__)
football_api = FootballAPI()
model = ValueHuntingModel()

@app.route('/')
def index():
    return render_template('index.html')

# Loglarda görünen eksik adres 1: Tarih listesi
@app.route('/api/dates')
def get_dates():
    # Arayüzün hata vermemesi için bugün ve yarını dönüyoruz
    today = datetime.now().strftime('%Y-%m-%d')
    return jsonify([today])

# Loglarda görünen eksik adres 2: Maç fikstürü ve Analiz
@app.route('/api/fixtures')
def get_fixtures():
    date = request.args.get('date')
    raw_matches = football_api.get_daily_matches() # Tarih parametresini istersen api'ye iletebilirsin
    
    if not raw_matches:
        return jsonify([])

    analyzed_list = []
    for match in raw_matches:
        # Modül A, B ve C'yi içeren yeni fonksiyonu çağırıyoruz
        analysis = model.calculate_all_modules(match)
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
