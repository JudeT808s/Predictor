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

    def calculate_recent_results(fixtures):
        fixtures.sort(key=lambda x: datetime.strptime(x['utcDate'], '%Y-%m-%dT%H:%M:%SZ'))

        team_stats = defaultdict(lambda: {
            'recent_matches': [],
            'total_goals_scored': 0,
            'total_opponents_goals_conceded': 0,
            'matches_played': 0,
            'goals_against_opponents': []
        })

        for match in fixtures:
            home_team_id = match['homeTeam']['id']
            away_team_id = match['awayTeam']['id']

            home_team_name = match['homeTeam']['name']
            away_team_name = match['awayTeam']['name']

            home_team_goals = match['score']['fullTime']['home']
            away_team_goals = match['score']['fullTime']['away']

            # Update total goals and goals conceded
            team_stats[home_team_id]['total_goals_scored'] += home_team_goals
            team_stats[away_team_id]['total_goals_scored'] += away_team_goals

            team_stats[home_team_id]['total_opponents_goals_conceded'] += away_team_goals
            team_stats[away_team_id]['total_opponents_goals_conceded'] += home_team_goals

            team_stats[home_team_id]['matches_played'] += 1
            team_stats[away_team_id]['matches_played'] += 1

            # Calculate goals_against_opp_goals_conceded for the home and away team
            home_goals_against_opp_goals_conceded = (
                home_team_goals / away_team_goals if away_team_goals > 0 else 0
            )
            away_goals_against_opp_goals_conceded = (
                away_team_goals / home_team_goals if home_team_goals > 0 else 0
            )

            # Append the calculated ratio for each team
            team_stats[home_team_id]['goals_against_opponents'].append(home_goals_against_opp_goals_conceded)
            team_stats[away_team_id]['goals_against_opponents'].append(away_goals_against_opp_goals_conceded)

            # Determine match result
            home_result = 'D'
            away_result = 'D'
            if home_team_goals > away_team_goals:
                home_result = 'W'
                away_result = 'L'
            elif home_team_goals < away_team_goals:
                home_result = 'L'
                away_result = 'W'

            # Add match result to the team's recent match history (keeping last 5)
            team_stats[home_team_id]['recent_matches'].append({
                'team_name': home_team_name,
                'result': home_result,
                'goals_scored': home_team_goals,
                'goals_conceded': away_team_goals
            })

            team_stats[away_team_id]['recent_matches'].append({
                'team_name': away_team_name,
                'result': away_result,
                'goals_scored': away_team_goals,
                'goals_conceded': home_team_goals
            })

            if len(team_stats[home_team_id]['recent_matches']) > 5:
                team_stats[home_team_id]['recent_matches'].pop(0)
            if len(team_stats[away_team_id]['recent_matches']) > 5:
                team_stats[away_team_id]['recent_matches'].pop(0)

        recent_results_and_stats = {}
        for team_id, stats in team_stats.items():
            matches = stats['recent_matches']
            results = ''.join(m['result'] for m in matches)
            goals_scored = sum(m['goals_scored'] for m in matches)
            goals_conceded = sum(m['goals_conceded'] for m in matches)

            avg_opponents_goals_conceded = (
                stats['total_opponents_goals_conceded'] / stats['matches_played']
                if stats['matches_played'] > 0 else 0
            )

            team_name = matches[0]['team_name'] if matches else "Unknown"

            # Calculate the average goals_against_opponents
            avg_goals_against_opponents = (
                sum(stats['goals_against_opponents']) / len(stats['goals_against_opponents'])
                if stats['goals_against_opponents'] else 0
            )
            #Goals ratio according to defence difficulty
            goals_scored_ratio = home_team_goals / avg_opponents_goals_conceded

            #Need to loop through with above calculation to get form

            recent_results_and_stats[team_name] = {
                'team_id': team_id,
                'recent_results': results,
                'goals_scored': goals_scored,
                'goals_conceded': goals_conceded,
                #Average goals conceded by opponents accross all matches
                'avg_opponents_goals_conceded': avg_opponents_goals_conceded,
                #Average amount of goals scored i think
                'avg_goals_against_opponents': avg_goals_against_opponents
            }

        return recent_results_and_stats

    recent_results = calculate_recent_results(fetched_fixtures)

    # Add debug print statements if needed
    # print(recent_results)  # For debugging

    return jsonify(recent_results)


if __name__ == '__main__':
    app.run(debug=True)