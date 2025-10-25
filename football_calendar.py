#!/usr/bin/env python3
"""
Football Calendar Sync
Automatically adds your favorite football team's fixtures to Google Calendar
"""

import os
import sys
import datetime
import requests
from typing import List, Dict, Optional
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Google Calendar API scope
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Football-data.org API configuration
FOOTBALL_API_BASE_URL = 'https://api.football-data.org/v4'

# Popular teams mapping (team name -> team ID)
POPULAR_TEAMS = {
    'dortmund': {'id': 4, 'name': 'Borussia Dortmund', 'competition': 'BL1'},
    'bayern': {'id': 5, 'name': 'FC Bayern München', 'competition': 'BL1'},
    'barcelona': {'id': 81, 'name': 'FC Barcelona', 'competition': 'PD'},
    'real madrid': {'id': 86, 'name': 'Real Madrid CF', 'competition': 'PD'},
    'manchester united': {'id': 66, 'name': 'Manchester United FC', 'competition': 'PL'},
    'liverpool': {'id': 64, 'name': 'Liverpool FC', 'competition': 'PL'},
    'arsenal': {'id': 57, 'name': 'Arsenal FC', 'competition': 'PL'},
    'chelsea': {'id': 61, 'name': 'Chelsea FC', 'competition': 'PL'},
    'manchester city': {'id': 65, 'name': 'Manchester City FC', 'competition': 'PL'},
    'psg': {'id': 524, 'name': 'Paris Saint-Germain FC', 'competition': 'FL1'},
    'juventus': {'id': 109, 'name': 'Juventus FC', 'competition': 'SA'},
    'inter': {'id': 108, 'name': 'FC Internazionale Milano', 'competition': 'SA'},
    'milan': {'id': 98, 'name': 'AC Milan', 'competition': 'SA'},
}


def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ[key] = value


class FootballCalendarSync:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.calendar_service = None
        
    def authenticate_google_calendar(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("\n❌ Error: credentials.json not found!")
                    print("Please follow the setup instructions in README.md")
                    sys.exit(1)
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        try:
            self.calendar_service = build('calendar', 'v3', credentials=creds)
            print("✅ Successfully authenticated with Google Calendar")
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            sys.exit(1)
    
    def get_team_fixtures(self, team_id: int, days_ahead: int = 90) -> List[Dict]:
        """Fetch upcoming fixtures for a team"""
        headers = {'X-Auth-Token': self.api_key}
        
        # Calculate date range
        date_from = datetime.date.today().isoformat()
        date_to = (datetime.date.today() + datetime.timedelta(days=days_ahead)).isoformat()
        
        url = f"{FOOTBALL_API_BASE_URL}/teams/{team_id}/matches"
        params = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'status': 'SCHEDULED'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('matches', [])
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching fixtures: {e}")
            return []
    
    def create_calendar_event(self, match: Dict, calendar_id: str = 'primary') -> bool:
        """Create a calendar event for a match"""
        try:
            # Parse match data
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            competition = match['competition']['name']
            match_date = match['utcDate']
            
            # Create event
            event = {
                'summary': f"⚽ {home_team} vs {away_team}",
                'description': f"{competition}\n\nHome: {home_team}\nAway: {away_team}",
                'start': {
                    'dateTime': match_date,
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (datetime.datetime.fromisoformat(match_date.replace('Z', '+00:00')) + 
                               datetime.timedelta(hours=2)).isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},
                        {'method': 'popup', 'minutes': 15},
                    ],
                },
            }
            
            # Check if event already exists
            existing_events = self.calendar_service.events().list(
                calendarId=calendar_id,
                timeMin=match_date,
                timeMax=(datetime.datetime.fromisoformat(match_date.replace('Z', '+00:00')) + 
                        datetime.timedelta(minutes=1)).isoformat(),
                q=f"{home_team} vs {away_team}",
                singleEvents=True
            ).execute()
            
            if existing_events.get('items'):
                print(f"⏭️  Skipping (already exists): {home_team} vs {away_team}")
                return False
            
            # Create the event
            event = self.calendar_service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            print(f"✅ Added: {home_team} vs {away_team} on {match_date[:10]}")
            return True
            
        except HttpError as error:
            print(f"❌ Error creating event: {error}")
            return False
    
    def sync_team_fixtures(self, team_id: int, team_name: str, days_ahead: int = 90):
        """Main function to sync team fixtures to calendar"""
        print(f"\n🔄 Fetching fixtures for {team_name}...")
        
        fixtures = self.get_team_fixtures(team_id, days_ahead)
        
        if not fixtures:
            print("❌ No upcoming fixtures found or API error")
            return
        
        print(f"\n📅 Found {len(fixtures)} upcoming matches")
        print("\n" + "="*60)
        
        added_count = 0
        for match in fixtures:
            if self.create_calendar_event(match):
                added_count += 1
        
        print("="*60)
        print(f"\n✨ Successfully added {added_count} new matches to your calendar!")


def display_team_selection():
    """Display available teams for selection"""
    print("\n⚽ Football Calendar Sync")
    print("="*60)
    print("\nAvailable teams:")
    print()
    
    for idx, (key, team) in enumerate(sorted(POPULAR_TEAMS.items()), 1):
        print(f"  {idx:2d}. {team['name']}")
    
    print(f"\n  Or type a team name to search\n")


def get_user_team_choice() -> Optional[Dict]:
    """Get team selection from user"""
    display_team_selection()
    
    choice = input("Enter team number or name: ").strip().lower()
    
    # Check if it's a number
    if choice.isdigit():
        idx = int(choice) - 1
        teams_list = sorted(POPULAR_TEAMS.items())
        if 0 <= idx < len(teams_list):
            key, team = teams_list[idx]
            return team
    
    # Check if it's a team name
    if choice in POPULAR_TEAMS:
        return POPULAR_TEAMS[choice]
    
    # Search for partial match
    for key, team in POPULAR_TEAMS.items():
        if choice in key or choice in team['name'].lower():
            print(f"\n✅ Found: {team['name']}")
            return team
    
    print(f"\n❌ Team '{choice}' not found in the list")
    return None


def main():
    """Main entry point"""
    # Load .env file if it exists
    load_env_file()
    
    # Check for API key
    api_key = os.environ.get('FOOTBALL_API_KEY')
    
    if not api_key:
        print("\n❌ Error: FOOTBALL_API_KEY environment variable not set!")
        print("\nPlease follow these steps:")
        print("1. Get a free API key from https://www.football-data.org/")
        print("2. Set the environment variable:")
        print("   export FOOTBALL_API_KEY='your_api_key_here'")
        print("\nOr add it to your .env file (see README.md)\n")
        sys.exit(1)
    
    # Get team selection
    team = get_user_team_choice()
    
    if not team:
        sys.exit(1)
    
    # Initialize sync
    sync = FootballCalendarSync(api_key)
    
    # Authenticate with Google Calendar
    sync.authenticate_google_calendar()
    
    # Sync fixtures
    sync.sync_team_fixtures(team['id'], team['name'])
    
    print("\n🎉 Done! Check your Google Calendar.\n")


if __name__ == '__main__':
    main()
