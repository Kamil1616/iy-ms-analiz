import requests
import os
from datetime import datetime

class FootballAPI:
    def __init__(self):
        # Render panelindeki FOOTBALL_API_KEY'i otomatik çeker
        self.api_key = os.environ.get('FOOTBALL_API_KEY')
        self.base_url = 'https://api.football-data.org/v4'
        self.headers = {'X-Auth-Token': self.api_key}

    def get_daily_matches(self):
        try:
            endpoint = f"{self.base_url}/matches"
            response = requests.get(endpoint, headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                matches = []
                for match in data.get('matches', []):
                    matches.append({
                        'homeTeam': match['homeTeam']['name'],
                        'awayTeam': match['awayTeam']['name'],
                        'utcDate': match['utcDate'],
                        'league': match['competition']['name'],
                        'status': match['status']
                    })
                return matches
            return []
        except Exception:
            return []
