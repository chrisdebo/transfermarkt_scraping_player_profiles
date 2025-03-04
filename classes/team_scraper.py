import requests
from bs4 import BeautifulSoup

# Anpassung am TeamScraper, damit wir die team_id mitgeben:
class TeamScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/129.0.0.0 Safari/537.36"
    }

    def __init__(self, team):
        self.team = team

    def fetch_player_urls(self):
        response = requests.get(self.team.url, headers=self.HEADERS)
        if response.status_code != 200:
            raise Exception(f"Fehler beim Laden der Team-Seite: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        players_table = soup.find("table", class_="items")

        players = []
        if players_table:
            for row in players_table.find_all("tr", class_=["odd", "even"]):
                main_link_td = row.find("td", class_="hauptlink")
                if main_link_td and main_link_td.find('a'):
                    player_name = main_link_td.find('a').get_text(strip=True)
                    player_url = main_link_td.find('a')['href']
                    player_url = "https://www.transfermarkt.de" + player_url
                    # player_id aus URL extrahieren:
                    # "https://www.transfermarkt.de/manuel-neuer/profil/spieler/27004"
                    # player_id = letzter Teil der URL
                    player_id = player_url.split("/")[-1]
                    players.append({"player_name": player_name, "player_url": player_url, "player_id": player_id})
        return players