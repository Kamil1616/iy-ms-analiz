import requests
import os

class FootballAPI:
    def __init__(self):
        # Render panelindeki anahtarı çekiyoruz
        self.api_key = os.environ.get('FOOTBALL_API_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            # Ücretsiz planda tüm maçlar gelmeyebilir, 
            # bu yüzden belirli bir tarih aralığı veya lig kısıtlaması olmadan çekiyoruz
            endpoint = f"{self.base_url}/matches"
            response = requests.get(endpoint, headers=self.headers)
            
            print(f"DEBUG: API Status Code: {response.status_code}") # Render loglarında göreceğiz
            
            if response.status_code == 200:
                data = response.json()
                matches = []
                for match in data.get('matches', []):
                    matches.append({
                        'homeTeam': match['homeTeam']['name'],
                        'awayTeam': match['awayTeam']['name'],
                        'league': match['competition']['name'],
                        'utcDate': match['utcDate']
                    })
                print(f"DEBUG: Bulunan Maç Sayısı: {len(matches)}")
                return matches
            else:
                print(f"DEBUG: API Hatası: {response.text}")
                return []
        except Exception as e:
            print(f"DEBUG: Bağlantı Hatası: {str(e)}")
            return []
