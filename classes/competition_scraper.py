import requests
from bs4 import BeautifulSoup

class CompetitionScraper:
    def __init__(self, competitions):
        self.competitions = competitions if isinstance(competitions, list) else [competitions]

    @staticmethod
    def fetch_team_urls(competition):
        # Nutze jetzt competition.get_season_url() anstatt competition.base_url
        season_url = competition.get_season_url()
        response = requests.get(season_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })

        if response.status_code != 200:
            raise Exception(f"Failed to fetch competition page for {competition.name}: {response.status_code}")

        soup = BeautifulSoup(response.text, 'html.parser')
        team_table = soup.find('div', class_='responsive-table')
        if team_table:
            for row in team_table.find_all('tr')[1:]:
                team_cell = row.find('td', class_='hauptlink')
                if team_cell and team_cell.find('a'):
                    team_name = team_cell.get_text(strip=True)
                    team_url = "https://www.transfermarkt.de" + team_cell.find('a')['href']
                    competition.teams[team_name] = team_url

    def scrape_all(self):
        for competition in self.competitions:
            self.fetch_team_urls(competition)
            print(f"Scraped teams for {competition.name} ({competition.season})")

    def scrape_one(self, competition):
        self.fetch_team_urls(competition)
        print(f"Scraped teams for {competition.name} ({competition.season})")