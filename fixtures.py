from flask import Flask, jsonify, render_template  
import os  # To access environment variables
import requests

app = Flask(__name__)

# Get base URL from environment variable (replace with your actual value)
base_url = os.environ.get('FOOTBALL_DATA_API_URL', 'https://api.football-data.org/v4/')

@app.route('/') 
def index():
    return render_template('index.html')  # Assuming the HTML file is named index.html


@app.route('/fixtures')
def get_fixtures():
    def fetch_fixtures_from_api(url):
        headers = {
            'X-Auth-Token': '744d0e43ac2840589c3b6d75996ed50b'  
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

    # Update the fixtures array with fetched data
    fixtures = fetched_fixtures

    return jsonify(fixtures)  # Return the updated fixtures data

if __name__ == '__main__':
    app.run(debug=True)