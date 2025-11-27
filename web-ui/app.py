"""
Flask web application for generating college basketball team data.
"""
from flask import Flask, render_template, jsonify, request
import threading
import json
import os
import sys
from datetime import datetime
from generator import generate_team_data
from s3_handler import upload_to_s3

# Load API key at startup
config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.txt')
if os.path.exists(config_path):
    try:
        with open(config_path, 'r') as f:
            for line in f:
                if line.startswith('CBB_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    os.environ['CBB_API_KEY'] = api_key
                    print(f"API key loaded from {config_path}")
                    break
    except Exception as e:
        print(f"Warning: Could not load API key from config: {e}")
else:
    print(f"Warning: Config file not found at {config_path}")

app = Flask(__name__)

# In-memory job storage (simple for MVP)
# In production, consider using Redis or a database
jobs = {}


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/teams')
def get_teams():
    """Get list of all teams (cached)"""
    cache_file = os.path.join(os.path.dirname(__file__), 'data', 'teams_cache.json')
    
    # Load from cache if exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                teams = json.load(f)
            return jsonify(teams)
        except Exception as e:
            print(f"Cache read error: {e}")
            pass  # If cache is corrupted, fetch fresh
    
    # Fetch from API and cache
    try:
        # Add scripts directory to path
        scripts_path = os.path.join(os.path.dirname(__file__), '..', 'scripts')
        scripts_path = os.path.abspath(scripts_path)
        if scripts_path not in sys.path:
            sys.path.insert(0, scripts_path)
        
        # Also check for config in parent config/ directory
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'api_config.txt')
        if os.path.exists(config_path):
            # Load API key from config file and set as environment variable
            try:
                with open(config_path, 'r') as f:
                    for line in f:
                        if line.startswith('CBB_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            os.environ['CBB_API_KEY'] = api_key
                            break
            except:
                pass
        
        from cbb_api_wrapper import CollegeBasketballAPI
        
        api = CollegeBasketballAPI()
        teams_data = api.get_teams()
        
        if not teams_data:
            return jsonify({'error': 'No teams returned from API'}), 500
        
        # Format for dropdown
        # API returns 'school' field, not 'name'
        teams = []
        for t in teams_data:
            team_name = t.get('school') or t.get('name') or t.get('displayName', '')
            if team_name:
                teams.append({'id': t.get('id'), 'name': team_name})
        teams.sort(key=lambda x: x['name'])
        
        # Cache it
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(teams, f)
        
        return jsonify(teams)
    except ImportError as e:
        error_msg = f'Import error: {str(e)}. Check that scripts/cbb_api_wrapper.py exists.'
        print(error_msg)
        return jsonify({'error': error_msg}), 500
    except Exception as e:
        error_msg = f'Failed to fetch teams: {str(e)}'
        print(f"Error in get_teams: {error_msg}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500


@app.route('/api/generate', methods=['POST'])
def generate_data():
    """Start data generation job"""
    try:
        data = request.json
        team_name = data.get('team_name')
        # Fixed to 2026 season
        season = 2026
        
        if not team_name:
            return jsonify({'error': 'Team name required'}), 400
        
        # Create job ID
        job_id = f"{team_name.lower().replace(' ', '_')}_{season}_{int(datetime.now().timestamp())}"
        
        # Initialize job status
        jobs[job_id] = {
            'status': 'queued',
            'team_name': team_name,
            'season': season,
            'progress': 0,
            'message': 'Job queued...',
            'url': None,
            'error': None,
            'gameDates': None
        }
        
        # Start background thread
        thread = threading.Thread(
            target=run_generation,
            args=(job_id, team_name, season)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>')
def get_status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])


def run_generation(job_id, team_name, season):
    """Background job runner"""
    try:
        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting data generation...'
        jobs[job_id]['progress'] = 0
        
        # Generate data (with progress updates)
        output_file = generate_team_data(team_name, season, jobs[job_id])
        
        # Upload to S3
        jobs[job_id]['message'] = 'Uploading to S3...'
        jobs[job_id]['progress'] = 95
        
        # Convert relative path to absolute path for S3 upload
        if not os.path.isabs(output_file):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_file = os.path.join(project_root, output_file)
        
        s3_url = upload_to_s3(output_file, team_name, season)
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['url'] = s3_url
        jobs[job_id]['message'] = 'Complete!'
        jobs[job_id]['progress'] = 100
        # Get game dates from progress callback (set by generator)
        jobs[job_id]['gameDates'] = jobs[job_id].get('gameDates', [])
        
    except Exception as e:
        jobs[job_id]['status'] = 'failed'
        jobs[job_id]['error'] = str(e)
        jobs[job_id]['message'] = f'Error: {str(e)}'
        jobs[job_id]['progress'] = 0


if __name__ == '__main__':
    import sys
    # Use port 5001 to avoid conflict with AirPlay Receiver on macOS
    app.run(debug=True, port=5001, host='0.0.0.0')

