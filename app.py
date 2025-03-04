import pandas as pd
import json
import warnings
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from classes.competition import Competition
from classes.competition_scraper import CompetitionScraper
from classes.team import Team
from classes.team_scraper import TeamScraper
from classes.player import Player
from classes.player_scraper import PlayerScraper
from helpers import convert_to_serializable, extract_team_id, player_to_dict

warnings.simplefilter(action='ignore', category=FutureWarning)

# Competitions laden
df_comp = pd.read_json("competitions_tm.json")

df_comp_filter = df_comp[9:10]

df_comp = df_comp_filter

competitions = []
for _, row in df_comp.iterrows():
    competition = Competition(
        name=row["name"],
        base_url=row["url"],
        season=2024
    )
    competitions.append(competition)

# CompetitionScraper um Teams zu holen
c_scraper = CompetitionScraper(competitions)
#c_scraper.scrape_one(competitions[0])

c_scraper.scrape_all()

# Wir wollen ein flaches DataFrame:
# Spalten: competition_name, competition_season, competition_url, competition_id,
#          team_name, team_id, team_url,
#          player_id, player_name, player_url, birthday, height,
#          nationalities (JSON), main_position, side_positions (JSON), preferred_foot,
#          social_media (JSON), market_value, market_value_history (JSON),
#          current_club, in_team_since, contract_until, last_extension, player_agent, birth_place

all_rows = []

player_scraper = PlayerScraper()


competition_progress = tqdm(competitions, desc="Competitions", unit="competition")

for comp in competition_progress:
    competition_name = comp.name
    competition_season = comp.season
    competition_url = comp.get_season_url()
    competition_id = comp.competition_id

    # Teams scrapen
    teams = comp.teams.items()
    team_progress = tqdm(teams, desc=f"Teams in {comp.name}", unit="team", leave=False)
    for team_name, team_url in team_progress:
        team_id = extract_team_id(team_url)
        team_obj = Team(name=team_name, url=team_url, team_id=team_id)

        print("----------")
        print(f"Scraping team {team_name} ({team_id}) ...")
        print("----------")
        t_scraper = TeamScraper(team_obj)
        player_basic_info_list = t_scraper.fetch_player_urls()

        # Jeden Spieler flach machen
        for p_info in player_basic_info_list:
            p_obj = Player(player_id=p_info["player_id"], player_url=p_info["player_url"])

            p_obj.set_name(player_scraper.scrape_name(p_obj.player_url))
            p_obj.set_birthday_height(*player_scraper.scrape_birthday_height(p_obj.player_url))
            p_obj.set_nationalities(player_scraper.scrape_nationalities(p_obj.player_url))
            p_obj.set_positions(*player_scraper.scrape_positions(p_obj.player_url))
            p_obj.set_preferred_foot(player_scraper.scrape_foot(p_obj.player_url))
            p_obj.set_social_media(player_scraper.scrape_social_media(p_obj.player_url))
            p_obj.set_contract_info(*player_scraper.scrape_contract_info(p_obj.player_url))
            p_obj.set_player_agent(player_scraper.scrape_player_agency(p_obj.player_url))
            p_obj.set_birth_place(player_scraper.scrape_birth_place(p_obj.player_url))
            p_obj.set_market_value_history(player_scraper.scrape_market_value_history(p_obj.player_id))
            if p_obj.market_value_history is not None and not p_obj.market_value_history.empty:
                p_obj.set_market_value(p_obj.market_value_history["mw"].iloc[-1])
            else:
                p_obj.set_market_value(None)

            #print(f"Scraped player {p_obj.name} ({p_obj.player_id})")

            # player_data holen
            player_data = player_to_dict(p_obj)

            # Komplexe Felder in JSON-Strings umwandeln
            # nationalities, side_positions, social_media, market_value_history
            def to_json_str(value):
                if value is None:
                    return None
                return json.dumps(value, ensure_ascii=False)

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
                "birth_place": player_data["birth_place"]
            }

            all_rows.append(row)

# Aus all_rows ein DataFrame machen
df_flat = pd.DataFrame(all_rows, columns=[
    "competition_name", "competition_season", "competition_url", "competition_id",
    "team_name", "team_id", "team_url",
    "player_id", "player_name", "player_url", "birthday", "height",
    "nationalities", "main_position", "side_positions", "preferred_foot",
    "social_media", "market_value", "market_value_history",
    "current_club", "in_team_since", "contract_until", "last_extension",
    "player_agent", "birth_place"
])

# Nun df_flat pro Competition speichern
for comp_name_season, group_df in df_flat.groupby(["competition_name", "competition_season"]):
    comp_name, comp_season = comp_name_season
    file_name = f"{comp_name}_{comp_season}_flat.json".replace(" ", "_")
    # Speichere als JSON (orient="records" für eine Liste von Objekten)
    group_df.to_json(file_name, orient="records", force_ascii=False, indent=4)

print("Flache Tabellen pro Competition als JSON gespeichert.")