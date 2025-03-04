import numpy as np
import pandas as pd

def convert_to_serializable(obj):
    if isinstance(obj, np.integer):
        return int(obj)  # numpy-Int zu Python-Int
    elif isinstance(obj, np.floating):
        return float(obj)  # numpy-Float zu Python-Float
    elif isinstance(obj, np.ndarray):
        return obj.tolist()  # numpy-Array zu Python-Liste
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()  # Timestamp zu String
    raise TypeError(f"Type {type(obj)} not serializable")

def extract_team_id(team_url):
    # Beispielhafte URL: "https://www.transfermarkt.de/holstein-kiel/startseite/verein/269/saison_id/2024"
    # Wir splitten nach '/verein/' und dann nehmen wir den nächsten Abschnitt bis zum nächsten '/'
    # "verein/269/saison_id" -> team_id = "269"
    try:
        part = team_url.split("/verein/")[1]
        team_id = part.split("/")[0]
        return team_id
    except:
        return None

def player_to_dict(player):
    return {
        "player_id": player.player_id,
        "player_name": player.name,
        "player_url": player.player_url,
        "birthday": player.birthday,
        "height": player.height,
        "nationalities": player.nationalities,
        "main_position": player.main_position,
        "side_positions": player.side_positions,
        "preferred_foot": player.preferred_foot,
        "social_media": player.social_media,
        "market_value": player.market_value,
        "market_value_history": player.market_value_history.to_dict(orient='records') if player.market_value_history is not None else None,
        "current_club": player.current_club,
        "in_team_since": player.in_team_since,
        "contract_until": player.contract_until,
        "last_extension": player.last_extension,
        "player_agent": player.player_agent,
        "birth_place": player.birth_place
    }