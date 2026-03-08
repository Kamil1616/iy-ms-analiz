import requests
import os

class FootballAPI:
    def __init__(self):
        self.api_key = os.environ.get('FOOTBALL_API_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            # Önce gerçek API'den çekmeyi deniyoruz
            endpoint = f"{self.base_url}/matches"
            response = requests.get(endpoint, headers=self.headers)
            
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
                
                # Eğer API başarılı ama maç listesi boşsa (ücretsiz plan kısıtı)
                if not matches:
                    return self.get_test_data("API Başarılı Ama Maç Yok (Ücretsiz Plan)")
                return matches
            else:
                # API hatası (403/429 vb.) durumunda test verisi göster
                return self.get_test_data(f"API Hatası (Kod: {response.status_code})")
                
        except Exception as e:
            return self.get_test_data(f"Bağlantı Hatası: {str(e)}")

    def get_test_data(self, reason):
        """Veri gelmediğinde sistemin çalıştığını kanıtlayan test verisi."""
        return [{
            'homeTeam': f"TEST-EV ({reason})",
            'awayTeam': "TEST-DEP",
            'league': "TEST LİGİ",
            'utcDate': "2026-03-08T20:30:00Z"
        }]
