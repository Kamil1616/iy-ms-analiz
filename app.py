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
    # 1. API'den maçları çek
    raw_matches = football_api.get_daily_matches()
    
    if not raw_matches:
        return jsonify([])

    # 2. Maçları Value Hunting (A, B ve C Modülleri) ile analiz et
    analyzed_list = []
    for match in raw_matches:
        # Modelin içinde Modül C hesaplamalarının da olduğundan emin oluyoruz
        analysis = model.calculate_all_modules(match) 
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
