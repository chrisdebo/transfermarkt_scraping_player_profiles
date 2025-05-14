import time
import random
import requests
from bs4 import BeautifulSoup

class CompetitionScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    def __init__(self, competitions):
        self.competitions = competitions if isinstance(competitions, list) else [competitions]
        self.last_request_time = 0
        self.min_request_delay = 3.0  # Minimale Verzögerung in Sekunden
        self.max_request_delay = 7.0  # Maximale Verzögerung in Sekunden
        self.max_retries = 5  # Maximale Anzahl von Wiederholungsversuchen
        self.base_retry_delay = 10  # Basis-Wartezeit für Wiederholungsversuche in Sekunden

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

    def fetch_team_urls(self, competition):
        """Fetch team URLs for a competition with retry mechanism."""
        url = competition.get_season_url()
        retry_count = 0
        retry_delay = self.base_retry_delay

        while retry_count < self.max_retries:
            try:
                self._delay_between_requests()
                response = requests.get(url, headers=self.HEADERS)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    team_table = soup.find("table", {"class": "items"})
                    if team_table:
                        team_rows = team_table.find_all("tr", {"class": ["odd", "even"]})
                        for row in team_rows:
                            team_cell = row.find("td", {"class": "hauptlink"})
                            if team_cell and team_cell.find("a"):
                                team_name = team_cell.find("a").text.strip()
                                team_url = "https://www.transfermarkt.de" + team_cell.find("a")["href"]
                                competition.teams[team_name] = team_url
                        return
                    else:
                        print(f"Warnung: Keine Team-Tabelle gefunden für {competition.name}")
                        return
                        
                elif response.status_code == 503:
                    retry_count += 1
                    print(f"503 Service Unavailable für {competition.name}. Versuch {retry_count}/{self.max_retries}. Warte {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponentielles Backoff
                    continue
                    
                else:
                    raise Exception(f"Unerwarteter Status-Code: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                retry_count += 1
                print(f"Netzwerkfehler für {competition.name}: {str(e)}. Versuch {retry_count}/{self.max_retries}. Warte {retry_delay} Sekunden...")
                time.sleep(retry_delay)
                retry_delay *= 2
                continue

        raise Exception(f"Konnte nach {self.max_retries} Versuchen keine Teams für {competition.name} abrufen")

    def scrape_all(self):
        """Scrape all competitions."""
        for competition in self.competitions:
            print(f"Scraping teams for {competition.name}...")
            self.fetch_team_urls(competition)
            print(f"Found {len(competition.teams)} teams for {competition.name}")

    def scrape_one(self, competition):
        self.fetch_team_urls(competition)
        print(f"Scraped teams for {competition.name} ({competition.season})")