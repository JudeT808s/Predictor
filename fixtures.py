from flask import Flask, jsonify, render_template
import os
import requests
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# Get base URL from environment variable
base_url = os.environ.get('FOOTBALL_DATA_API_URL', 'https://api.football-data.org/v4/')
api_key = os.environ.get('api_key', '744d0e43ac2840589c3b6d75996ed50b')

@app.route('/')
def index():
    return render_template('index.html')  

@app.route('/fixtures')
def get_fixtures():
    def fetch_fixtures_from_api(url):
        headers = {
            'X-Auth-Token': api_key
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('matches', [])  # Ensure it returns an array of matches
        else:
            return []  # Handle error or return an empty list
    
    api_endpoint = f"{base_url}/competitions/ELC/matches?status=FINISHED"
    fixtures = fetch_fixtures_from_api(api_endpoint)
    
    return jsonify(fixtures)  # Ensure this returns a list/array of matches


@app.route('/recent-results')
def get_recent_results():
    def fetch_fixtures_from_api(url):
        headers = {
            'X-Auth-Token': api_key  
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()['matches']  # Extract matches from response
        else:
            return []  # Handle error

    # Use the base URL to construct the API endpoint
    api_endpoint = f"{base_url}/competitions/ELC/matches?status=FINISHED"

    # Fetch data from API
    fetched_fixtures = fetch_fixtures_from_api(api_endpoint)

    # Calculate goals scored contrasted by opponents' goals conceded in the last 5 matches
    def calculate_recent_results(fixtures):
        # Sort fixtures by date (oldest to most recent)
        fixtures.sort(key=lambda x: datetime.strptime(x['utcDate'], '%Y-%m-%dT%H:%M:%SZ'))

        team_stats = defaultdict(list)  # To store the last 5 matches per team

        # Process each match
        for match in fixtures:
            home_team_id = match['homeTeam']['id']
            away_team_id = match['awayTeam']['id']

            home_team_name = match['homeTeam']['name']
            away_team_name = match['awayTeam']['name']

            home_team_goals = match['score']['fullTime']['home']
            away_team_goals = match['score']['fullTime']['away']

            # Determine the result (W, D, L)
            home_result = 'D'  # Default to Draw
            away_result = 'D'  # Default to Draw

            if home_team_goals > away_team_goals:
                home_result = 'W'
                away_result = 'L'
            elif home_team_goals < away_team_goals:
                home_result = 'L'
                away_result = 'W'

            # Add this match result to the team's recent match history
            team_stats[home_team_id].append({'team_name': home_team_name, 'result': home_result, 'goals_scored': home_team_goals, 'goals_conceded': away_team_goals})
            team_stats[away_team_id].append({'team_name': away_team_name, 'result': away_result, 'goals_scored': away_team_goals, 'goals_conceded': home_team_goals})

            # Keep only the last 5 matches for each team
            if len(team_stats[home_team_id]) > 5:
                team_stats[home_team_id].pop(0)
            if len(team_stats[away_team_id]) > 5:
                team_stats[away_team_id].pop(0)

        # Create a summary of recent results and goals contrast
        recent_results_and_stats = {}
        for team_id, matches in team_stats.items():
            results = ''.join(m['result'] for m in matches)  # Concatenate results like "WWLWL"
            goals_scored = sum(m['goals_scored'] for m in matches)  # Total goals scored
            opponents_goals_conceded = sum(m['goals_conceded'] for m in matches)  # Total goals conceded by opponents

            # Calculate the goals ratio (goals scored divided by opponents' goals conceded)
            if opponents_goals_conceded > 0:  # Prevent division by zero
                goals_ratio = goals_scored / opponents_goals_conceded
            else:
                goals_ratio = 0  # Set ratio to 0 if opponents' goals conceded is zero

            # Use the team name from the first match in the list (as it's consistent across all matches for that team)
            team_name = matches[0]['team_name']

            # Store the data in the dictionary
            recent_results_and_stats[team_name] = {
                'team_id': team_id,
                'recent_results': results,
                'goals_scored': goals_scored,
                'opponents_goals_conceded': opponents_goals_conceded,
                'goals_ratio': goals_ratio
            }

        return recent_results_and_stats

    # Compute the statistics
    recent_results = calculate_recent_results(fetched_fixtures)

    return jsonify(recent_results)

if __name__ == '__main__':
    app.run(debug=True)
