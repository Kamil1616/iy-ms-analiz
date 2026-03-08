@app.route('/api/fixtures')
def get_fixtures():
    raw_matches = football_api.get_daily_matches()
    
    if not raw_matches:
        return jsonify([])

    analyzed_list = []
    for match in raw_matches:
        # Value Hunting Modüllerini çalıştır
        analysis = model.calculate_all_modules(match)
        # Frontend'in lig filtresi için lig ismini eklediğimizden emin olalım
        analysis['league'] = match.get('league', 'Bilinmeyen Lig')
        analyzed_list.append(analysis)
    
    return jsonify(analyzed_list)
