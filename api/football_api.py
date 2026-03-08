import requests
import os

class FootballAPI:
    def __init__(self):
        self.api_key = os.environ.get('FOOTBALL_API_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            # 1. Gerçek API'den veri çekmeyi dene
            response = requests.get(f"{self.base_url}/matches", headers=self.headers, timeout=10)
            
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
                
                # Eğer API boş dönerse (Ücretsiz plan kısıtı), Test Verisi bas
                if not matches:
                    return self._generate_fallback_data("API Aktif (Bugün Maç Yok)")
                return matches
            else:
                return self._generate_fallback_data(f"API Hatası (Kod: {response.status_code})")
                
        except Exception:
            return self._generate_fallback_data("Bağlantı Sorunu")

    def _generate_fallback_data(self, status):
        """API veri vermediğinde sistemi canlandıran gerçekçi maçlar."""
        return [
            {
                'homeTeam': "Real Madrid",
                'awayTeam': "Barcelona",
                'league': f"SİSTEM KONTROL ({status})",
                'utcDate': "2026-03-08T21:00:00Z"
            },
            {
                'homeTeam': "Galatasaray",
                'awayTeam': "Fenerbahçe",
                'league': "SİSTEM KONTROL (Test)",
                'utcDate': "2026-03-08T19:00:00Z"
            }
        ]
