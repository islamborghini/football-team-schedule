# ⚽ Football Calendar Sync

Automatically sync your favorite football team's fixtures to Google Calendar!

## Features

- 🎯 Select from popular teams (Dortmund, Bayern, Barcelona, Real Madrid, etc.)
- 📅 Automatically adds upcoming matches to your Google Calendar
- 🔔 Sets reminders (1 hour and 15 minutes before each match)
- ✅ Avoids duplicate events
- 🆓 Uses free APIs (football-data.org)

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get Football Data API Key

1. Go to [football-data.org](https://www.football-data.org/client/register)
2. Register for a free account
3. Copy your API key
4. Create a `.env` file (or set environment variable):

```bash
cp .env.example .env
# Edit .env and add your API key
```

Or export it directly:
```bash
export FOOTBALL_API_KEY='your_api_key_here'
```

### 3. Set Up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials
   - Save the file as `credentials.json` in this directory

**Important:** The `credentials.json` file must be in the same directory as `football_calendar.py`

### 4. Run the Script

```bash
python football_calendar.py
```

On first run:
- A browser window will open asking you to authorize the app
- Sign in with your Google account
- Grant calendar access permissions
- The script will save a `token.json` file for future runs

## Usage

When you run the script, you'll see a list of available teams:

```
⚽ Football Calendar Sync
============================================================

Available teams:

   1. Arsenal FC
   2. Borussia Dortmund
   3. Chelsea FC
   4. FC Barcelona
   ...

  Or type a team name to search

Enter team number or name:
```

You can:
- Enter a number (e.g., `2` for Dortmund)
- Type the team name (e.g., `dortmund`)
- Type a partial match (e.g., `barca` for Barcelona)

The script will:
1. Fetch all upcoming fixtures for the next 90 days
2. Add them to your Google Calendar
3. Skip any matches that already exist
4. Show you a summary of what was added

## Available Teams

- **Bundesliga:** Dortmund, Bayern München
- **Premier League:** Arsenal, Chelsea, Liverpool, Manchester City, Manchester United
- **La Liga:** Barcelona, Real Madrid
- **Serie A:** AC Milan, Inter Milan, Juventus
- **Ligue 1:** PSG

## Customization

### Add More Teams

Edit the `POPULAR_TEAMS` dictionary in `football_calendar.py`:

```python
POPULAR_TEAMS = {
    'your_team': {'id': TEAM_ID, 'name': 'Team Name', 'competition': 'COMP_CODE'},
}
```

To find team IDs, use the football-data.org API documentation.

### Change Date Range

Modify the `days_ahead` parameter (default is 90 days):

```python
sync.sync_team_fixtures(team['id'], team['name'], days_ahead=180)  # 6 months
```

### Customize Reminders

Edit the `reminders` section in the `create_calendar_event` method:

```python
'reminders': {
    'useDefault': False,
    'overrides': [
        {'method': 'popup', 'minutes': 120},  # 2 hours before
        {'method': 'popup', 'minutes': 30},   # 30 minutes before
    ],
},
```

## Troubleshooting

### "credentials.json not found"
- Make sure you've downloaded the OAuth credentials from Google Cloud Console
- Save it as `credentials.json` in the project directory

### "FOOTBALL_API_KEY environment variable not set"
- Create a `.env` file with your API key
- Or export it: `export FOOTBALL_API_KEY='your_key'`

### "No upcoming fixtures found"
- Check your API key is valid
- The team might not have scheduled matches in the next 90 days
- Free tier has rate limits (10 requests/minute)

### Rate Limits
The free tier of football-data.org allows:
- 10 requests per minute
- Limited competitions access

If you need more, consider upgrading to a paid plan.

## Files

- `football_calendar.py` - Main script
- `requirements.txt` - Python dependencies
- `credentials.json` - Google OAuth credentials (you create this)
- `token.json` - Google auth token (auto-generated)
- `.env` - Your API keys (you create this)

## License

Free to use and modify!

## Credits

- Football data from [football-data.org](https://www.football-data.org/)
- Google Calendar API from Google
