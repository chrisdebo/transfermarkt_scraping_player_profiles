import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random

# Anpassung am TeamScraper, damit wir die team_id mitgeben:
class TeamScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/129.0.0.0 Safari/537.36"
    }

    def __init__(self, team):
        self.team = team
        self.last_request_time = 0
        self.min_request_delay = 3.0  # Minimale Verzögerung in Sekunden
        self.max_request_delay = 7.0  # Maximale Verzögerung in Sekunden

    def _delay_between_requests(self):
        """Fügt eine zufällige Verzögerung zwischen den Anfragen ein."""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Berechne eine zufällige Verzögerung zwischen min und max
        random_delay = random.uniform(self.min_request_delay, self.max_request_delay)
        
        # Wenn seit der letzten Anfrage weniger Zeit als die zufällige Verzögerung vergangen ist
        if elapsed < random_delay:
            # Warte die restliche Zeit
            time.sleep(random_delay - elapsed)
        
        # Aktualisiere die Zeit der letzten Anfrage
        self.last_request_time = time.time()

    def fetch_player_urls(self):
        max_retries = 5
        retry_delay = 10  # Basis-Wartezeit in Sekunden
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Verzögerung zwischen Anfragen
                self._delay_between_requests()
                
                response = requests.get(self.team.url, headers=self.HEADERS)
                if response.status_code == 200:
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
                
                elif response.status_code == 503:
                    retry_count += 1
                    print(f"503 Service Unavailable für Team {self.team.name}. Versuch {retry_count}/{max_retries}. Warte {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentielles Backoff
                    continue
                    
                else:
                    raise Exception(f"Unerwarteter Status-Code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"Netzwerkfehler für Team {self.team.name}: {str(e)}. Versuch {retry_count}/{max_retries}. Warte {retry_delay} Sekunden...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue
                
        # Wenn nach allen Versuchen immer noch kein Erfolg
        raise Exception(f"Konnte nach {max_retries} Versuchen keine Spieler für Team {self.team.name} abrufen")