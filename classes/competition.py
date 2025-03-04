class Competition:
    def __init__(self, name, season, base_url):
        self.name = name
        self.season = season
        self.base_url = base_url
        self.competition_id = self.extract_competition_id()
        self.teams = {}

    def extract_competition_id(self):
        """Extracts the competition ID from the base URL."""
        return self.base_url.split('/')[-1]  # z.B. 'L1' oder 'GB1'

    def get_season_url(self):
        # Aus base_url und season die vollständige Competition-URL erzeugen
        # Beispiel: base_url = "https://www.transfermarkt.de/bundesliga/startseite/wettbewerb/L1"
        # => "https://www.transfermarkt.de/bundesliga/startseite/wettbewerb/L1/plus/?saison_id=2024"
        return f"{self.base_url}/plus/?saison_id={self.season}"

    def print_teams(self):
        for team_name, team_url in self.teams.items():
            print(f"{team_name}: {team_url}")

    def __str__(self):
        return f"{self.name} ({self.season}) - ID: {self.competition_id}"