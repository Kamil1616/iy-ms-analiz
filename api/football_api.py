import requests
from datetime import datetime

class FootballAPI:
    def __init__(self):
        # Senin sağladığın API Key buraya eklendi
        self.api_key = '409f68cec9f2435ea2203618c84e7ae2'
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            # Bugünün maçlarını çeken endpoint
            endpoint = f"{self.base_url}/matches"
            response = requests.get(endpoint, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                matches = []
                for match in data.get('matches', []):
                    # Frontend ve Modelin beklediği temel veri yapısı
                    matches.append({
                        'homeTeam': match['homeTeam']['name'],
                        'awayTeam': match['awayTeam']['name'],
                        'utcDate': match['utcDate'],
                        'league': match['competition']['name'],
                        'status': match['status']
                    })
                return matches
            else:
                print(f"API Hatası: {response.status_code}")
                return []
        except Exception as e:
            print(f"Bağlantı Hatası: {e}")
            return []
