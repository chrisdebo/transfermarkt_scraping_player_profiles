class Player:
    def __init__(self, player_id, player_url):
        self.player_id = player_id
        self.player_url = player_url
        self.name = ""
        self.birthday = None
        self.height = 0.0
        self.nationalities = []
        self.main_position = ""
        self.side_positions = []
        self.preferred_foot = ""
        self.social_media = []
        self.market_value = 0
        self.market_value_history = []
        self.current_club = ""
        self.in_team_since = ""
        self.contract_until = ""
        self.last_extension = ""
        self.player_agent = ""
        self.birth_place = ""


    # Setter methods to populate attributes
    def set_name(self, name):
        self.name = name

    def set_birthday_height(self, birthday, height):
        self.birthday = birthday
        self.height = height

    def set_nationalities(self, nationalities_list):
        self.nationalities = nationalities_list

    def set_positions(self, main_position, side_positions):
        self.main_position = main_position
        self.side_positions = side_positions

    def set_preferred_foot(self, foot):
        self.preferred_foot = foot

    def set_social_media(self, social_media_list):
        self.social_media = social_media_list

    def set_market_value(self, market_value):
        self.market_value = market_value

    def set_market_value_history(self, market_value_history):
        self.market_value_history = market_value_history

    def set_contract_info(self, current_club, in_team_since, contract_until, last_extension):
        self.current_club = current_club
        self.in_team_since = in_team_since
        self.contract_until = contract_until
        self.last_extension = last_extension

    def set_player_agent(self, agent):
        self.player_agent = agent

    def set_birth_place(self, birth_place):
        self.birth_place = birth_place

    def player_to_dict(self):
        return {
            "player_id": self.player_id,
            "player_url": self.player_url,
            "name": self.name,
            "birthday": self.birthday,
            "height": self.height,
            "nationalities": self.nationalities,
            "main_position": self.main_position,
            "side_positions": self.side_positions,
            "preferred_foot": self.preferred_foot,
            "social_media": self.social_media,
            "market_value": self.market_value,
            "market_value_history": self.market_value_history if self.market_value_history is not None else None,
            "current_club": self.current_club,
            "in_team_since": self.in_team_since,
            "contract_until": self.contract_until,
            "last_extension": self.last_extension,
            "player_agent": self.player_agent,
            "birth_place": self.birth_place
        }

    def __str__(self):
        return (f"{self.name} ({self.player_id}) - "
                f"Main Position: {self.main_position}, Market Value: {self.market_value}, "
                f"Current Club: {self.current_club}, Birthplace: {self.birth_place} "
                f"Nationalities: {self.nationalities}, Social Media: {self.social_media}, "
                f"Height: {self.height}, Birthday: {self.birthday}, "
                f"Preferred Foot: {self.preferred_foot}, Player Agent: {self.player_agent}, "
                f"Contract Until: {self.contract_until}, Last Extension: {self.last_extension} "
                f"Market Value History: {self.market_value_history}")
