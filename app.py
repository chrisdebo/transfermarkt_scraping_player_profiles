import json
import warnings
import os
import time
from datetime import datetime

import pandas as pd
from tqdm import tqdm

from classes.competition import Competition
from classes.competition_scraper import CompetitionScraper
from classes.player import Player
from classes.player_scraper import PlayerScraper
from classes.team import Team
from classes.team_scraper import TeamScraper
from helpers import extract_team_id, player_to_dict, convert_to_serializable

warnings.simplefilter(action='ignore', category=FutureWarning)

def log_progress(message):
    """Loggt eine Nachricht mit Zeitstempel."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# Erstelle output Verzeichnis falls es nicht existiert
if not os.path.exists('output'):
    os.makedirs('output')

# Competitions laden
log_progress("Lade Competitions aus JSON...")
df_comp = pd.read_json("competitions_tm_germany.json")

# nur comp 0,1,2,5
df_comp = df_comp[df_comp["name"].isin(["Bundesliga", "2. Bundesliga", "3. Liga", "Regionalliga West"])]

competitions = []
for _, row in df_comp.iterrows():
    competition = Competition(
        name=row["name"],
        base_url=row["url"],
        season=2024
    )
    competitions.append(competition)

# CompetitionScraper um Teams zu holen
log_progress("Starte CompetitionScraper...")
c_scraper = CompetitionScraper(competitions)
c_scraper.scrape_all()

all_rows = []
player_scraper = PlayerScraper()

competition_progress = tqdm(competitions, desc="Competitions", unit="competition")

for comp in competition_progress:
    competition_name = comp.name
    competition_season = comp.season
    competition_url = comp.get_season_url()
    competition_id = comp.competition_id

    log_progress(f"Starte Scraping für Competition: {competition_name}")

    # Teams scrapen
    teams = comp.teams.items()
    team_progress = tqdm(teams, desc=f"Teams in {comp.name}", unit="team", leave=False)
    for team_name, team_url in team_progress:
        team_id = extract_team_id(team_url)
        team_obj = Team(name=team_name, url=team_url, team_id=team_id)

        # Prüfe, ob das Team bereits gespeichert wurde
        team_filename = f"output/{competition_name}_{team_name}_{team_id}.json"
        if os.path.exists(team_filename):
            log_progress(f"Team {team_name} ({team_id}) bereits vorhanden, überspringe...")
            continue

        log_progress(f"Starte Scraping für Team: {team_name} ({team_id})")
        t_scraper = TeamScraper(team_obj)
        try:
            player_basic_info_list = t_scraper.fetch_player_urls()
            log_progress(f"Gefundene Spieler für {team_name}: {len(player_basic_info_list)}")
        except Exception as e:
            log_progress(f"FEHLER beim Abrufen der Spieler für Team {team_name}: {str(e)}")
            continue

        team_rows = []  # Liste für die Spieler des aktuellen Teams

        # Jeden Spieler flach machen
        for p_info in player_basic_info_list:
            try:
                p_obj = Player(player_id=p_info["player_id"], player_url=p_info["player_url"])
                player_url_name = p_info["player_url"].split("/")[-4]

                log_progress(f"Starte Scraping für Spieler: {player_url_name} ({p_info['player_id']})")
                
                # Hole alle Stammdaten in einem Durchgang
                basic_data = player_scraper.scrape_all_basic_data(p_obj.player_url)
                if basic_data is None:
                    log_progress(f"FEHLER: Konnte keine Stammdaten für Spieler {p_obj.player_id} holen")
                    continue

                log_progress(f"Stammdaten erfolgreich für {player_url_name}")

                # Setze die Stammdaten
                p_obj.set_name(basic_data['name'])
                p_obj.set_birthday_height(basic_data['birthday'], basic_data['height'])
                p_obj.set_nationalities(basic_data['nationalities'])
                p_obj.set_positions(basic_data['main_position'], basic_data['side_positions'])
                p_obj.set_preferred_foot(basic_data['preferred_foot'])
                p_obj.set_social_media(basic_data['social_media'])
                p_obj.set_contract_info(
                    basic_data['current_club'],
                    basic_data['in_team_since'],
                    basic_data['contract_until'],
                    basic_data['last_extension']
                )
                p_obj.set_player_agent(basic_data['player_agent'])
                p_obj.set_birth_place(basic_data['birth_place'])

                # Hole die zusätzlichen Daten
                log_progress(f"Hole Marktwert-Historie für {player_url_name}")
                try:
                    p_obj.set_market_value_history(player_scraper.scrape_market_value_history(p_obj.player_id))
                    if p_obj.market_value_history is not None and not p_obj.market_value_history.empty:
                        p_obj.set_market_value(p_obj.market_value_history["mw"].iloc[-1])
                    else:
                        p_obj.set_market_value(None)
                except Exception as e:
                    log_progress(f"FEHLER bei Marktwert-Historie für {player_url_name}: {e}")
                    p_obj.set_market_value_history(pd.DataFrame())
                    p_obj.set_market_value(None)

                log_progress(f"Hole Leistungsdaten für {player_url_name}")
                try:
                    performance_data = player_scraper.scrape_performance_data(p_obj.player_id, p_obj.player_url)
                    p_obj.set_performance_data(performance_data if performance_data else [])
                except Exception as e:
                    log_progress(f"FEHLER bei Leistungsdaten für {player_url_name}: {e}")
                    p_obj.set_performance_data([])

                # player_data holen
                player_data = player_to_dict(p_obj)

                # Komplexe Felder in JSON-Strings umwandeln
                def to_json_str(value):
                    if value is None:
                        return None
                    if isinstance(value, pd.DataFrame):
                        return value.to_dict(orient='records')
                    if isinstance(value, list):
                        # Prüfe den Typ, den wir zurückgeben
                        log_progress(f"Performance-Daten Typ: {type(value)}")
                        return value  # Liste direkt zurückgeben, da sie bereits das richtige Format hat
                    return json.dumps(value, ensure_ascii=False)

                # Debug-Ausgabe für den Performance-Daten-Typ
                if player_data["performance_data"] is not None:
                    log_progress(f"Performance-Daten-Typ für {player_url_name}: {type(player_data['performance_data'])}")
                
                row = {
                    "competition_name": competition_name,
                    "competition_season": competition_season,
                    "competition_url": competition_url,
                    "competition_id": competition_id,
                    "team_name": team_name,
                    "team_id": team_id,
                    "team_url": team_url,
                    "player_id": player_data["player_id"],
                    "player_name": player_data["player_name"],
                    "player_url": player_data["player_url"],
                    "birthday": player_data["birthday"],
                    "height": player_data["height"],
                    "nationalities": to_json_str(player_data["nationalities"]),
                    "main_position": player_data["main_position"],
                    "side_positions": to_json_str(player_data["side_positions"]),
                    "preferred_foot": player_data["preferred_foot"],
                    "social_media": to_json_str(player_data["social_media"]),
                    "market_value": player_data["market_value"],
                    "market_value_history": to_json_str(player_data["market_value_history"]),
                    "current_club": player_data["current_club"],
                    "in_team_since": player_data["in_team_since"],
                    "contract_until": player_data["contract_until"],
                    "last_extension": player_data["last_extension"],
                    "player_agent": player_data["player_agent"],
                    "birth_place": player_data["birth_place"],
                    "performance_data": player_data["performance_data"]  # Direkt verwenden, keine Konvertierung
                }

                team_rows.append(row)
                all_rows.append(row)
                log_progress(f"Spieler {player_url_name} erfolgreich verarbeitet")

            except Exception as e:
                log_progress(f"FEHLER bei Verarbeitung von Spieler {p_info['player_id']}: {e}")
                continue

        # Speichere die Daten des aktuellen Teams in einer JSON-Datei
        team_filename = f"output/{competition_name}_{team_name}_{team_id}.json"
        with open(team_filename, 'w', encoding='utf-8') as f:
            json.dump(team_rows, f, ensure_ascii=False, indent=2, default=convert_to_serializable)
        log_progress(f"Team-Daten gespeichert in {team_filename}")

# Speichere alle Daten in einer JSON-Datei
#with open("output/all_data.json", 'w', encoding='utf-8') as f:
#    json.dump(all_rows, f, ensure_ascii=False, indent=2, default=convert_to_serializable)
#log_progress("Alle Daten gespeichert in output/all_data.json")