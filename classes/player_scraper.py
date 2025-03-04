import re

import pandas as pd
import requests
from bs4 import BeautifulSoup


class PlayerScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    def __init__(self):
        self.soup_cache = {}

    def fetch_player_page(self, player_url):
        """Fetch and cache the HTML page of the player."""
        if player_url in self.soup_cache:
            return self.soup_cache[player_url]

        response = requests.get(player_url, headers=self.HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            self.soup_cache[player_url] = soup
            return soup
        else:
            raise Exception(f"Error fetching the page: {response.status_code}")

    def parse_html(self, html_text):
        """Parsen des HTML-Textes mit BeautifulSoup und Rückgabe des BeautifulSoup-Objekts."""
        soup = BeautifulSoup(html_text, "html.parser")
        return soup

    def get_player_id(self, player_url):
        player_id = player_url.split("/")[-1]
        return player_id

    def scrape_name(self, player_url):
        # Füge hier die Logik zum Scrapen des Namens hinzu
        soup = self.fetch_player_page(player_url)
        name = soup.select_one('h1[class="data-header__headline-wrapper"]').text.split('\n')[-1].strip()
        return name

    def scrape_birthday_height(self, player_url):
        # Logik zum Scrapen von Geburtsdatum und Größe
        soup = self.fetch_player_page(player_url)

        # Scraping birthday
        birthday_tag = soup.find('span', string="Geb./Alter:")
        if birthday_tag:
            birthday_element = birthday_tag.find_next('span', class_='info-table__content--bold')
            if birthday_element:
                birthday = birthday_element.text.strip()
                birthday = birthday.split()[0]  # Extract the date part before the age
            else:
                birthday = "Unknown"  # Rückgabe eines Standardwerts
        else:
            birthday = "Unknown"

        # Scraping height
        height_tag = soup.find('span', string="Größe:")
        if height_tag:
            height_element = height_tag.find_next('span', class_='info-table__content--bold')
            if height_element:
                # Extraktion des Texts und Umwandlung in Zentimeter
                height = height_element.text.strip().replace('m', '').replace(',', '.').strip()
                try:
                    height = int(float(height) * 100)  # Konvertieren zu Zentimetern
                except ValueError:
                    height = "Unknown"  # Für den Fall, dass die Umwandlung fehlschlägt
            else:
                height = "Unknown"
        else:
            height = "Unknown"

        return birthday, height

    def scrape_current_club(self, player_url):
        # Logik zum Scrapen des aktuellen Vereins
        soup = self.fetch_player_page(player_url)
        # Scraping current club
        current_club = soup.find('span', string="Aktueller Verein:").find_next('span',
                                                                               class_='info-table__content--bold').text.strip()
        return current_club

    def scrape_contract_info(self, player_url):
        """
        Scrapes contract-related information from a player's Transfermarkt profile.

        Args:
        - player_url (str): URL of the player's Transfermarkt profile.

        Returns:
        - tuple: Current club, start date at the team, contract end date, and last extension date.
        """
        soup = self.fetch_player_page(player_url)

        # Aktueller Verein
        current_club = "Unknown"
        try:
            current_club_element = soup.find('span', text=re.compile(r"\s*Aktueller Verein:\s*"))
            if current_club_element:
                current_club_info = current_club_element.find_next('span', class_='info-table__content--flex')
                if current_club_info:
                    club_link = current_club_info.find('a', title=True)
                    current_club = club_link.get('title').strip() if club_link else "Unknown"
        except Exception as e:
            print(f"Error scraping current club: {e}")

        # Im Team seit
        in_team_since = None
        try:
            in_team_since_element = soup.find('span', text=re.compile(r"\s*Im Team seit:\s*"))
            if in_team_since_element:
                in_team_since = in_team_since_element.find_next_sibling('span', class_='info-table__content--bold').text.strip()
        except Exception as e:
            print(f"Error scraping 'Im Team seit': {e}")

        # Vertrag bis
        contract_until = None
        try:
            contract_until_element = soup.find('span', text=re.compile(r"\s*Vertrag bis:\s*"))
            if contract_until_element:
                contract_until = contract_until_element.find_next_sibling('span', class_='info-table__content--bold').text.strip()
        except Exception as e:
            print(f"Error scraping 'Vertrag bis': {e}")

        # Letzte Verlängerung
        last_extension = "Unknown"
        try:
            last_extension_element = soup.find('span', text=re.compile(r"\s*Letzte Verlängerung:\s*"))
            if last_extension_element:
                last_extension = last_extension_element.find_next_sibling('span', class_='info-table__content--bold').text.strip()
        except Exception as e:
            print(f"Error scraping 'Letzte Verlängerung': {e}")

        return current_club, in_team_since, contract_until, last_extension

    def scrape_nationalities(self, player_url):
        """
        Scrapes the nationalities of a player from the Transfermarkt profile.

        Args:
        - player_url (str): URL of the player's Transfermarkt profile.

        Returns:
        - list: List of nationalities.
        """
        soup = self.fetch_player_page(player_url)

        # Find the nationality section
        nationality_element = soup.find('span', string="Staatsbürgerschaft:").find_next('span', class_='info-table__content--bold')
        if not nationality_element:
            return []

        # Extract the text and split by non-breaking spaces and regular spaces
        nationality_text = nationality_element.text.strip()
        # Split on two spaces (as used in the HTML) and also handle non-breaking spaces
        nationalities = re.split(r'\s{2,}|&nbsp;', nationality_text)

        # Clean up and return the list
        return [nat.strip() for nat in nationalities if nat.strip()]

    def scrape_positions(self, player_url):
        soup = self.fetch_player_page(player_url)

        # Scraping main and side positions
        detail_position = soup.find('div', class_='detail-position')

        if not detail_position:
            # Return default values when `detail-position` is not found
            return "Unknown", []

        # Check for main position
        main_position_element = detail_position.find('dt', string="Hauptposition:")
        main_position = main_position_element.find_next('dd').text.strip() if main_position_element else "Unknown"

        # Check for side positions
        side_position_element = detail_position.find('dt', string="Nebenposition:")
        if side_position_element:
            side_positions_elements = side_position_element.find_next_siblings('dd')
            side_positions = [pos.text.strip() for pos in side_positions_elements]
        else:
            side_positions = []

        return main_position, side_positions

    def scrape_social_media(self, player_url):
        # Logik zum Scrapen von Social Media Profilen
        soup = self.fetch_player_page(player_url)
        # Scraping social media links
        social_media_section = soup.find('span', string="Social Media:")
        social_media_links = []
        if social_media_section:
            social_media_links = [a['href'] for a in social_media_section.find_next('div').find_all('a')]
        return social_media_links

    def scrape_player_agency(self, player_url):
        """
        Scrapes the player's agency information from their profile.

        Args:
        - player_url (str): URL of the player's profile.

        Returns:
        - str: Player agency or 'Unknown' if not found.
        """
        soup = self.fetch_player_page(player_url)

        # Attempt to find the "Spielerberater" label
        agency_label = soup.find('span', string="Spielerberater:")

        if not agency_label:
            # Return a default value if the label is not found
            return "Unknown"

        # Check for the next span with the specific class
        agency_info = agency_label.find_next('span', class_='info-table__content--bold')
        if not agency_info:
            return "Unknown"

        # Extract and return text, stripping any surrounding white spaces
        return agency_info.text.strip()

    def scrape_foot(self, player_url):
        # Logik zum Scrapen des bevorzugten Fußes
        soup = self.fetch_player_page(player_url)

        # Scraping preferred foot
        foot_element = soup.find('span', string="Fuß:")  # Versucht, 'Fuß:' zu finden
        if foot_element:
            # Versuche, das nächste relevante Element zu finden
            foot_detail = foot_element.find_next('span', class_='info-table__content--bold')
            if foot_detail:
                return foot_detail.text.strip()  # Gib den Fuß (z. B. "Rechtsfuß") zurück
            else:
                return "Unknown"  # Kein nächstes Element gefunden
        else:
            return "Unknown"  # 'Fuß:'-Element nicht gefunden

    def scrape_birth_place(self, player_url):
        """
        Scrape the birthplace of the player from the Transfermarkt profile.

        Args:
        - player_url (str): URL of the player's profile.

        Returns:
        - str: The birthplace of the player or "Unknown" if not found.
        """
        soup = self.fetch_player_page(player_url)
        # Attempt to find the "Geburtsort" label
        birth_place_label = soup.find('span', string="Geburtsort:")

        if not birth_place_label:
            # Return a default value and possibly log the issue
            return "Unknown"

        # Attempt to find the next relevant span element
        birth_place_element = birth_place_label.find_next('span', class_='info-table__content--bold')
        if not birth_place_element:
            # Return a default value if the element is not found
            return "Unknown"

        # Extract and return the text, stripping any surrounding spaces
        return birth_place_element.text.strip()

    def scrape_market_value_history(self, player_id):
        """
        Fetches the market value history of a player from the Transfermarkt API.

        Parameters:
        - player_id (int): The unique ID of the player on Transfermarkt.

        Returns:
        - pd.DataFrame: A DataFrame containing the market value ('mw'), date ('datum_mw'),
          club ('verein'), and age ('age') for each entry.
        """
        # Define the API URL
        url = f"https://www.transfermarkt.de/ceapi/marketValueDevelopment/graph/{player_id}"

        # Simulate fetching the API response (replace this with the actual request when available)
        response = requests.get(url, headers=self.HEADERS)

        # Check for a successful request
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data for player_id {player_id}: {response.status_code}")

        # Parse the JSON response
        data = response.json()

        # Extract relevant information into a DataFrame
        df = pd.DataFrame(data['list'], columns=['y', 'datum_mw', 'verein', 'age'])
        df.rename(columns={'y': 'mw'}, inplace=True)

        return df
