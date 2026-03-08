import requests
import os

class FootballAPI:
    def __init__(self):
        self.api_key = os.environ.get('FOOTBALL_API_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            # Gerçek API'den veri çekmeyi dene
            response = requests.get(f"{self.base_url}/matches", headers=self.headers)
            
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
                
                # Eğer API başarılı ama maç listesi boşsa (Bugün büyük liglerde maç yoksa)
                if not matches:
                    return self.get_fake_test_data("API Başarılı - Bugün Maç Yok")
                return matches
            else:
                # API Key geçersizse veya limit dolmuşsa burası çalışır
                return self.get_fake_test_data(f"API Hatası (Kod: {response.status_code})")
                
        except Exception as e:
            return self.get_fake_test_data(f"Bağlantı Hatası: {str(e)}")

    def get_fake_test_data(self, message):
        """Arayüzün çalıştığını kanıtlamak için sahte maç verisi."""
        return [{
            'homeTeam': f"TEST: {message}",
            'awayTeam': "DENEME-DEP",
            'league': "TEST LİGİ",
            'utcDate': "2026-03-08T20:30:00Z"
        }]
