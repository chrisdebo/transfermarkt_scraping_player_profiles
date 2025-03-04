# Transfermarkt Scraping Tool

A Python application for scraping football (soccer) player data from [Transfermarkt.de](https://www.transfermarkt.de/),
a widely used website for football statistics, market values, and player information.

## Features

- Scrapes comprehensive player information from Transfermarkt including:
    - Basic player details (name, birthday, height, nationality)
    - Current team and contract information
    - Position data (main and side positions)
    - Market value history
    - Player agent information
    - Social media profiles
    - And more

- Organizes data by competitions, teams, and individual players
- Exports data to structured JSON files for further analysis
- Handles German football leagues by default (Bundesliga through Regionalliga)

## Requirements

- Python 3.x
- Required packages:
    - beautifulsoup4
    - pandas
    - requests
    - tqdm
    - (see requirements.txt for complete list)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/chrisdebo/transfermarkt_scraping_player_profiles.git
   cd transfermarkt_scraping_player_profiles
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

The scraper uses a multi-level approach to gather data:

1. Competitions → Teams → Players

2. Run the main script to start scraping:
   ```
   python app.py
   ```

3. The script will:
    - Load competition data from `competitions_tm_germany.json`
    - Scrape teams from each competition
    - Scrape detailed player information from each team
    - Save results to JSON files named after each competition

## Customization

- Edit `competitions_tm_germany.json` to scrape different competitions
- Modify the scraper classes to extract additional data points
- Adjust the output format in `app.py` to meet your specific needs

## Notes

- This tool includes rate limiting and proper headers to respect Transfermarkt's servers
- The scraper is designed for educational and personal use
- Be mindful of Transfermarkt's terms of service when using this tool

## Disclaimer

This project is for educational purposes only. Use responsibly and respect Transfermarkt's terms of service and
robots.txt rules. The authors are not responsible for any misuse of this tool.