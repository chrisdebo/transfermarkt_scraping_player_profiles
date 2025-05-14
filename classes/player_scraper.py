import re
import time
import random

import pandas as pd
import requests
from bs4 import BeautifulSoup


class PlayerScraper:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }

    def __init__(self):
        self.soup_cache = {}
        self.last_request_time = 0
        self.min_request_delay = 1.0  # Minimale Verzögerung in Sekunden
        self.max_request_delay = 3.0  # Maximale Verzögerung in Sekunden

    def _delay_between_requests(self):
        """Fügt eine zufällige Verzögerung zwischen den Anfragen ein, um Rate-Limiting zu vermeiden."""
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

    def fetch_player_page(self, player_url):
        """Fetch and cache the HTML page of the player."""
        if player_url in self.soup_cache:
            return self.soup_cache[player_url]

        # Füge eine Verzögerung ein, bevor die Anfrage gesendet wird
        self._delay_between_requests()
        
        response = requests.get(player_url, headers=self.HEADERS)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            self.soup_cache[player_url] = soup
            return soup
        elif response.status_code == 503:
            # Bei 503-Fehler: Warte und versuche es noch einmal
            print(f"503 Service Unavailable for URL {player_url}. Waiting for 5 seconds before retry...")
            time.sleep(5)
            
            # Noch ein Versuch mit längerer Verzögerung
            self._delay_between_requests()
            response = requests.get(player_url, headers=self.HEADERS)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                self.soup_cache[player_url] = soup
                return soup
            else:
                raise Exception(f"Error fetching the page after retry: {response.status_code}")
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

        # Implementiere Wiederholung mit Pausen für den Fall eines 503-Fehlers
        max_retries = 3
        retry_count = 0
        retry_delay = 5  # Pause in Sekunden
        
        while retry_count < max_retries:
            try:
                # Füge eine Verzögerung ein, bevor die Anfrage gesendet wird
                self._delay_between_requests()
                
                # Fetch the API response
                response = requests.get(url, headers=self.HEADERS)
                
                if response.status_code == 200:
                    break  # Erfolgreiche Antwort, beende Schleife
                elif response.status_code == 503:
                    # Service Unavailable, versuche erneut
                    retry_count += 1
                    print(f"503 Service Unavailable for market value history of player_id {player_id}. Retry {retry_count}/{max_retries} in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    # Erhöhe die Verzögerung für den nächsten Versuch
                    retry_delay *= 2
                else:
                    # Andere Fehler
                    raise Exception(f"Failed to fetch market value history for player_id {player_id}: {response.status_code}")
            except requests.exceptions.RequestException as e:
                # Netzwerkfehler
                retry_count += 1
                print(f"Network error for market value history of player_id {player_id}: {e}. Retry {retry_count}/{max_retries} in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2
        
        # Wenn nach allen Versuchen immer noch kein Erfolg
        if retry_count >= max_retries:
            print(f"Failed to fetch market value history for player_id {player_id} after {max_retries} retries.")
            return pd.DataFrame()  # Leeres DataFrame zurückgeben

        # Parse the JSON response
        data = response.json()

        # Extract relevant information into a DataFrame
        df = pd.DataFrame(data['list'], columns=['y', 'datum_mw', 'verein', 'age'])
        df.rename(columns={'y': 'mw'}, inplace=True)

        return df
    
    def _convert_minutes(self, minutes_str):
        """Konvertiert einen Minuten-String in einen Integer.
        
        Args:
            minutes_str (str): String im Format "227'" oder "1.091'" oder "-"
            
        Returns:
            int: Konvertierte Minuten oder 0 bei "-"
        """
        if minutes_str == "-":
            return 0
            
        # Entferne das Minuten-Zeichen und Punkte
        minutes_str = minutes_str.replace("'", "").replace(".", "")
        
        try:
            return int(minutes_str)
        except ValueError:
            return 0

    def scrape_performance_data(self, player_id, player_url):
        """Scraped die Leistungsdaten eines Spielers."""
        # Extrahiere den Spielernamen aus der URL
        player_name = player_url.split('/')[-4]
        
        # Baue die URL für die Leistungsdaten
        performance_url = f"https://www.transfermarkt.de/{player_name}/leistungsdatendetails/spieler/{player_id}/saison//verein/0/liga/0/wettbewerb//pos/0/trainer_id/0/plus/1"
        
        # Hole zuerst die Stammdaten des Spielers
        self.player_data = {}
        main_position, side_positions = self.scrape_positions(player_url)
        self.player_data['main_position'] = main_position
        self.player_data['side_positions'] = side_positions
        
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                response = requests.get(performance_url, headers=self.HEADERS)
                if response.status_code == 503:
                    print(f"503 Fehler bei {performance_url}. Warte {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                    
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Finde die Tabelle mit den Leistungsdaten
                performance_table = soup.find('table', {'class': 'items'})
                if not performance_table:
                    return None
                
                performance_data = []
                rows = performance_table.find_all('tr', {'class': ['odd', 'even']})
                
                # Hole die Position des Spielers aus den Stammdaten
                is_goalkeeper = False
                if hasattr(self, 'player_data'):
                    # Prüfe zuerst die Hauptposition
                    if 'main_position' in self.player_data:
                        is_goalkeeper = 'Torwart' in self.player_data['main_position']
                    # Falls nicht gefunden, prüfe auch die Nebenpositionen
                    elif 'side_positions' in self.player_data:
                        is_goalkeeper = any('Torwart' in pos for pos in self.player_data['side_positions'])
                

                if not is_goalkeeper:                
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 15:  # Mindestens 15 Spalten für die vollständigen Informationen
                            # Basis-Informationen
                            performance_entry = {
                                'season': cols[0].text.strip(),
                                'competition': cols[2].find('a')['title'] if cols[2].find('a') else cols[2].text.strip(),
                                'club': cols[3].find('a')['title'] if cols[3].find('a') else cols[3].text.strip(),
                                'in_squad': cols[4].text.strip(),
                                'appearances': cols[5].text.strip(),
                                'points_per_game': cols[6].text.strip(),
                                'goals': cols[7].text.strip(),
                                'assists': cols[8].text.strip(),
                                'own_goals': cols[9].text.strip(),
                                'subbed_in': cols[10].text.strip(),
                                'subbed_out': cols[11].text.strip(),
                                'yellow_cards': cols[12].text.strip(),
                                'yellow_red_cards': cols[13].text.strip(),
                                'red_cards': cols[14].text.strip(),
                                'penalty_goals': cols[15].text.strip(),
                                'minutes_per_goal': self._convert_minutes(cols[16].text.strip() if len(cols) > 16 else '-'),
                                'minutes_played': self._convert_minutes(cols[17].text.strip() if len(cols) > 17 else '-')
                            }
                            performance_data.append(performance_entry)

                elif is_goalkeeper:
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 15:  # Mindestens 15 Spalten für die vollständigen Informationen
                            # Basis-Informationen
                            performance_entry = {
                                'season': cols[0].text.strip(),
                                'competition': cols[2].find('a')['title'] if cols[2].find('a') else cols[2].text.strip(),
                                'club': cols[3].find('a')['title'] if cols[3].find('a') else cols[3].text.strip(),
                                'in_squad': cols[4].text.strip(),
                                'appearances': cols[5].text.strip(),
                                'points_per_game': cols[6].text.strip(),
                                'goals': cols[7].text.strip(),
                                'own_goals': cols[8].text.strip(),
                                'subbed_in': cols[9].text.strip(),
                                'subbed_out': cols[10].text.strip(),
                                'yellow_cards': cols[11].text.strip(),
                                'yellow_red_cards': cols[12].text.strip(),
                                'red_cards': cols[13].text.strip(),
                                'goals_against': cols[14].text.strip(),
                                'clean_sheets': cols[15].text.strip() if len(cols) > 15 else '',
                                'minutes_played': self._convert_minutes(cols[16].text.strip() if len(cols) > 16 else '-')
                            }
                            performance_data.append(performance_entry)
                
                return performance_data
                
            except requests.exceptions.RequestException as e:
                print(f"Fehler beim Abrufen der Leistungsdaten für Spieler {player_id}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return None

    def scrape_all_basic_data(self, player_url):
        """
        Scraped alle Stammdaten eines Spielers in einem Durchgang.
        Returns None wenn die Anfrage fehlschlägt.
        """
        retry_count = 0
        retry_delay = 10  # Startwartezeit in Sekunden
        max_retries = 3   # Maximale Anzahl von Wiederholungsversuchen

        while retry_count <= max_retries:
            try:
                soup = self.fetch_player_page(player_url)
                if soup is None:
                    retry_count += 1
                    if retry_count > max_retries:
                        print(f"Maximale Anzahl von Versuchen für {player_url} erreicht. Breche ab.")
                        return None
                    print(f"Stammdaten-Abruf fehlgeschlagen für {player_url}. Versuch {retry_count}/{max_retries}. Warte {retry_delay} Sekunden...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Verdopple die Wartezeit für den nächsten Versuch
                    continue

                data = {}
                
                # Name
                try:
                    data['name'] = soup.select_one('h1[class="data-header__headline-wrapper"]').text.split('\n')[-1].strip()
                except:
                    data['name'] = "Unknown"

                # Geburtstag und Größe
                try:
                    birthday_tag = soup.find('span', string="Geb./Alter:")
                    if birthday_tag:
                        birthday_element = birthday_tag.find_next('span', class_='info-table__content--bold')
                        if birthday_element:
                            birthday = birthday_element.text.strip()
                            data['birthday'] = birthday.split()[0]
                        else:
                            data['birthday'] = "Unknown"
                    else:
                        data['birthday'] = "Unknown"
                except:
                    data['birthday'] = "Unknown"

                # Größe
                try:
                    height_tag = soup.find('span', string="Größe:")
                    if height_tag:
                        height_element = height_tag.find_next('span', class_='info-table__content--bold')
                        if height_element:
                            height = height_element.text.strip().replace('m', '').replace(',', '.').strip()
                            try:
                                data['height'] = int(float(height) * 100)
                            except ValueError:
                                data['height'] = "Unknown"
                        else:
                            data['height'] = "Unknown"
                    else:
                        data['height'] = "Unknown"
                except:
                    data['height'] = "Unknown"

                # Nationalitäten
                try:
                    nationality_element = soup.find('span', string="Staatsbürgerschaft:").find_next('span', class_='info-table__content--bold')
                    if nationality_element:
                        nationality_text = nationality_element.text.strip()
                        nationalities = re.split(r'\s{2,}|&nbsp;', nationality_text)
                        data['nationalities'] = [nat.strip() for nat in nationalities if nat.strip()]
                    else:
                        data['nationalities'] = []
                except:
                    data['nationalities'] = []

                # Positionen
                try:
                    detail_position = soup.find('div', class_='detail-position')
                    if detail_position:
                        main_position_element = detail_position.find('dt', string="Hauptposition:")
                        data['main_position'] = main_position_element.find_next('dd').text.strip() if main_position_element else "Unknown"
                        
                        side_position_element = detail_position.find('dt', string="Nebenposition:")
                        if side_position_element:
                            side_positions_elements = side_position_element.find_next_siblings('dd')
                            data['side_positions'] = [pos.text.strip() for pos in side_positions_elements]
                        else:
                            data['side_positions'] = []
                    else:
                        data['main_position'] = "Unknown"
                        data['side_positions'] = []
                except:
                    data['main_position'] = "Unknown"
                    data['side_positions'] = []

                # Bevorzugter Fuß
                try:
                    foot_element = soup.find('span', string="Fuß:")
                    if foot_element:
                        foot_detail = foot_element.find_next('span', class_='info-table__content--bold')
                        data['preferred_foot'] = foot_detail.text.strip() if foot_detail else "Unknown"
                    else:
                        data['preferred_foot'] = "Unknown"
                except:
                    data['preferred_foot'] = "Unknown"

                # Social Media
                try:
                    social_media_section = soup.find('span', string="Social Media:")
                    if social_media_section:
                        data['social_media'] = [a['href'] for a in social_media_section.find_next('div').find_all('a')]
                    else:
                        data['social_media'] = []
                except:
                    data['social_media'] = []

                # Vertragsinformationen
                try:
                    current_club_element = soup.find('span', text=re.compile(r"\s*Aktueller Verein:\s*"))
                    if current_club_element:
                        current_club_info = current_club_element.find_next('span', class_='info-table__content--flex')
                        if current_club_info:
                            club_link = current_club_info.find('a', title=True)
                            data['current_club'] = club_link.get('title').strip() if club_link else "Unknown"
                        else:
                            data['current_club'] = "Unknown"
                    else:
                        data['current_club'] = "Unknown"
                except:
                    data['current_club'] = "Unknown"

                # Im Team seit
                try:
                    in_team_since_element = soup.find('span', text=re.compile(r"\s*Im Team seit:\s*"))
                    data['in_team_since'] = in_team_since_element.find_next_sibling('span', class_='info-table__content--bold').text.strip() if in_team_since_element else None
                except:
                    data['in_team_since'] = None

                # Vertrag bis
                try:
                    contract_until_element = soup.find('span', text=re.compile(r"\s*Vertrag bis:\s*"))
                    data['contract_until'] = contract_until_element.find_next_sibling('span', class_='info-table__content--bold').text.strip() if contract_until_element else None
                except:
                    data['contract_until'] = None

                # Letzte Verlängerung
                try:
                    last_extension_element = soup.find('span', text=re.compile(r"\s*Letzte Verlängerung:\s*"))
                    data['last_extension'] = last_extension_element.find_next_sibling('span', class_='info-table__content--bold').text.strip() if last_extension_element else "Unknown"
                except:
                    data['last_extension'] = "Unknown"

                # Spielerberater
                try:
                    agency_label = soup.find('span', string="Spielerberater:")
                    if agency_label:
                        agency_info = agency_label.find_next('span', class_='info-table__content--bold')
                        data['player_agent'] = agency_info.text.strip() if agency_info else "Unknown"
                    else:
                        data['player_agent'] = "Unknown"
                except:
                    data['player_agent'] = "Unknown"

                # Geburtsort
                try:
                    birth_place_label = soup.find('span', string="Geburtsort:")
                    if birth_place_label:
                        birth_place_element = birth_place_label.find_next('span', class_='info-table__content--bold')
                        data['birth_place'] = birth_place_element.text.strip() if birth_place_element else "Unknown"
                    else:
                        data['birth_place'] = "Unknown"
                except:
                    data['birth_place'] = "Unknown"

                return data

            except Exception as e:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"Maximale Anzahl von Versuchen für {player_url} erreicht. Fehler: {e}")
                    return None
                
                print(f"Fehler beim Abrufen der Stammdaten für {player_url}: {e}. Versuch {retry_count}/{max_retries}. Warte {retry_delay} Sekunden...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Verdopple die Wartezeit für den nächsten Versuch

