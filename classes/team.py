class Team:
    def __init__(self, name, url, team_id):
        self.name = name
        self.url = url
        self.team_id = team_id
        self.players = []  # Hier werden später die vollständigen Player-Infos (Dicts) gespeichert

    def add_player(self, player_dict):
        self.players.append(player_dict)

    def to_dict(self):
        # Gibt das Team als Dictionary zurück, um es später als JSON zu speichern
        return {
            "team_name": self.name,
            "team_url": self.url,
            "players": self.players
        }

