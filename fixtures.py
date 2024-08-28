from flask import Flask, jsonify, render_template
import os
import requests
from collections import defaultdict
from datetime import datetime

app = Flask(__name__)

# Get base URL from environment variable
base_url = os.environ.get('FOOTBALL_DATA_API_URL', 'https://api.football-data.org/v4/')
api_key = os.environ.get('api_key', '744d0e43ac2840589c3b6d75996ed50b')

# Route to render the main index page
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch fixtures
@app.route('/fixtures')
def get_fixtures():
    def fetch_fixtures_from_api(url):
        headers = {'X-Auth-Token': api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('matches', [])
        else:
            return []

    api_endpoint = f"{base_url}/competitions/ELC/matches?status=FINISHED"
    fixtures = fetch_fixtures_from_api(api_endpoint)

    return jsonify(fixtures)

# Route to fetch recent results
@app.route('/recent-results')
def get_recent_results():
    def fetch_fixtures_from_api(url):
        headers = {'X-Auth-Token': api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get('matches', [])
        else:
            return []

    api_endpoint = f"{base_url}/competitions/ELC/matches?status=FINISHED"
    fetched_fixtures = fetch_fixtures_from_api(api_endpoint)

    # Function to calculate recent results and statistics
    def calculate_recent_results(fixtures):
        # Sort fixtures by date (oldest to most recent)
        fixtures.sort(key=lambda x: datetime.strptime(x['utcDate'], '%Y-%m-%dT%H:%M:%SZ'))

        team_stats = defaultdict(list)

        # Process each match
        for match in fixtures:
            home_team_id = match['homeTeam']['id']
            away_team_id = match['awayTeam']['id']

            home_team_name = match['homeTeam']['name']
            away_team_name = match['awayTeam']['name']

            home_team_goals = match['score']['fullTime']['home']
            away_team_goals = match['score']['fullTime']['away']

            home_team_overall_conceded = away_team_goals
            away_team_overall_conceded = home_team_goals

            # Determine the result (W, D, L)
            home_result = 'D'
            away_result = 'D'
            if home_team_goals > away_team_goals:
                home_result = 'W'
                away_result = 'L'
            elif home_team_goals < away_team_goals:
                home_result = 'L'
                away_result = 'W'

            # Add match result to the team's recent match history
            team_stats[home_team_id].append({
                'team_name': home_team_name,
                'result': home_result,
                'goals_scored': home_team_goals,
                'goals_conceded': away_team_goals,
                'opp_goals_conceded': away_team_overall_conceded
            })

            team_stats[away_team_id].append({
                'team_name': away_team_name,
                'result': away_result,
                'goals_scored': away_team_goals,
                'goals_conceded': home_team_goals,
                'opp_goals_conceded': home_team_overall_conceded
            })

            # Keep only the last 5 matches for each team
            if len(team_stats[home_team_id]) > 5:
                team_stats[home_team_id].pop(0)
            if len(team_stats[away_team_id]) > 5:
                team_stats[away_team_id].pop(0)

        # Create a summary of recent results and goals contrast
        recent_results_and_stats = {}
        for team_id, matches in team_stats.items():
            results = ''.join(m['result'] for m in matches)
            goals_scored = sum(m['goals_scored'] for m in matches)
            opponents_goals_conceded = sum(m['goals_conceded'] for m in matches)
            opp_goals_conceded = sum(m['opp_goals_conceded'] for m in matches)

            # Calculate the goals ratio (goals scored divided by opponents' goals conceded)
            goals_ratio = goals_scored / opponents_goals_conceded if opponents_goals_conceded > 0 else 0

            # Calculate the overall goals ratio
            overall_goals_ratio = goals_scored / opp_goals_conceded if opp_goals_conceded > 0 else 0

            # Use the team name from the first match (consistent for the same team)
            team_name = matches[0]['team_name']

            # Store the data in the dictionary
            recent_results_and_stats[team_name] = {
                'team_id': team_id,
                'recent_results': results,
                'goals_scored': goals_scored,
                'opponents_goals_conceded': opponents_goals_conceded,
                'goals_ratio': goals_ratio,
                'overall_opponents_goals_conceded': opp_goals_conceded,
                'overall_goals_ratio': overall_goals_ratio
            }

        return recent_results_and_stats

    # Compute and return the recent results statistics
    recent_results = calculate_recent_results(fetched_fixtures)
    return jsonify(recent_results)

if __name__ == '__main__':
    app.run(debug=True)