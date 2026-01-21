"""
Flask web application for generating college basketball team data.
"""
from flask import Flask, render_template, jsonify, request
import threading
import json
import os
import sys
import subprocess
from datetime import datetime
from generator import generate_team_data
from s3_handler import upload_to_s3
from email_notifier import send_job_completion_email

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


def get_git_info():
    """Get git commit hash and timestamp"""
    try:
        # Get the project root (parent of web-ui)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Get commit hash
        commit_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            cwd=project_root,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # Get commit timestamp
        commit_timestamp = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ci', 'HEAD'],
            cwd=project_root,
            stderr=subprocess.DEVNULL
        ).decode('utf-8').strip()
        
        # Parse and format timestamp
        if commit_timestamp:
            try:
                dt = datetime.strptime(commit_timestamp.split()[0] + ' ' + commit_timestamp.split()[1], '%Y-%m-%d %H:%M:%S')
                formatted_time = dt.strftime('%Y-%m-%d %I:%M %p').lower().replace('am', 'am').replace('pm', 'pm')
            except:
                formatted_time = commit_timestamp.split()[0] + ' ' + commit_timestamp.split()[1]
        else:
            formatted_time = datetime.now().strftime('%Y-%m-%d %I:%M %p').lower()
        
        return {
            'commit': commit_hash,
            'timestamp': formatted_time
        }
    except Exception as e:
        # Fallback if git is not available
        return {
            'commit': 'unknown',
            'timestamp': datetime.now().strftime('%Y-%m-%d %I:%M %p').lower()
        }


@app.route('/')
def index():
    """Main page"""
    git_info = get_git_info()
    return render_template('index.html', git_info=git_info)


@app.route('/api/teams')
def get_teams():
    """Get list of all teams (cached)"""
    cache_file = os.path.join(os.path.dirname(__file__), 'data', 'teams_cache.json')
    
    # Load from cache if exists
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                teams = json.load(f)
            # Validate cache data
            if isinstance(teams, list) and len(teams) > 0:
                print(f"Returning {len(teams)} teams from cache")
                return jsonify(teams)
            else:
                print(f"Cache file exists but is invalid (empty or wrong format)")
        except json.JSONDecodeError as e:
            print(f"Cache file is corrupted (invalid JSON): {e}")
        except Exception as e:
            print(f"Cache read error: {e}")
    
    # Only fetch from API if cache doesn't exist or is invalid
    # But first, check if we have a backup/fallback
    print("Cache not available, attempting to fetch from API...")
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
        
        # If API call fails (e.g., rate limit), try to return cached data even if it's old
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    teams = json.load(f)
                if isinstance(teams, list) and len(teams) > 0:
                    print(f"API failed, returning stale cache with {len(teams)} teams")
                    return jsonify(teams)
            except Exception as cache_err:
                print(f"Failed to read stale cache: {cache_err}")
        
        # If we still don't have cache, return a helpful error message
        return jsonify({
            'error': error_msg,
            'message': 'Unable to load teams. Please try again later or contact support.'
        }), 500


@app.route('/api/generate', methods=['POST'])
def generate_data():
    """Start data generation job"""
    try:
        data = request.json
        print(f"[API] /api/generate received: {data}")  # Debug: log full request
        team_name = data.get('team_name')
        # Fixed to 2026 season
        season = 2026

        # Smart historical stats handling:
        # - New param: force_historical_refresh (default: False) - force re-fetch all
        # - Legacy param: include_historical_stats - for backward compatibility
        # If neither is provided, uses smart auto-detection (include_historical_stats=None)
        force_historical_refresh = data.get('force_historical_refresh', False)

        # Backward compatibility: check if legacy param was explicitly provided
        if 'include_historical_stats' in data:
            include_historical_stats = data.get('include_historical_stats')
            print(f"[API] Legacy mode: include_historical_stats={include_historical_stats}")
        else:
            include_historical_stats = None  # Triggers smart auto-detection
            print(f"[API] Smart mode: force_historical_refresh={force_historical_refresh}")

        notify_email = data.get('notify_email')  # Optional email for completion notification
        print(f"[API] notify_email extracted: '{notify_email}'")  # Debug: log notify_email

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
            'gameDates': None,
            'cancelled': False,  # Cancellation flag
            'notify_email': notify_email  # Email to notify on completion
        }

        # Start background thread
        thread = threading.Thread(
            target=run_generation,
            args=(job_id, team_name, season, include_historical_stats, force_historical_refresh)
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


@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404
    
    job = jobs[job_id]
    
    # Only allow cancellation if job is queued or running
    if job['status'] in ['queued', 'running']:
        job['cancelled'] = True
        job['status'] = 'cancelled'
        job['message'] = 'Generation cancelled by user'
        job['progress'] = 0
        return jsonify({'success': True, 'message': 'Job cancelled'})
    else:
        return jsonify({'error': 'Job cannot be cancelled (already completed or failed)'}), 400


def run_generation(job_id, team_name, season, include_historical_stats=None, force_historical_refresh=False):
    """Background job runner"""
    try:
        # Check if cancelled before starting
        if jobs[job_id].get('cancelled', False):
            jobs[job_id]['status'] = 'cancelled'
            jobs[job_id]['message'] = 'Generation cancelled by user'
            return

        jobs[job_id]['status'] = 'running'
        jobs[job_id]['message'] = 'Starting data generation...'
        jobs[job_id]['progress'] = 0

        # Check for cancellation before generating
        if jobs[job_id].get('cancelled', False):
            jobs[job_id]['status'] = 'cancelled'
            jobs[job_id]['message'] = 'Generation cancelled by user'
            return

        # Generate data (with progress updates)
        output_file = generate_team_data(
            team_name, season, jobs[job_id],
            include_historical_stats=include_historical_stats,
            force_historical_refresh=force_historical_refresh
        )
        
        # Check for cancellation after generation
        if jobs[job_id].get('cancelled', False):
            jobs[job_id]['status'] = 'cancelled'
            jobs[job_id]['message'] = 'Generation cancelled by user'
            return
        
        # Upload to S3
        jobs[job_id]['message'] = 'Uploading to S3...'
        jobs[job_id]['progress'] = 95
        
        # Convert relative path to absolute path for S3 upload
        if not os.path.isabs(output_file):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            output_file = os.path.join(project_root, output_file)
        
        s3_url = upload_to_s3(output_file, team_name, season)
        
        # Final cancellation check
        if jobs[job_id].get('cancelled', False):
            jobs[job_id]['status'] = 'cancelled'
            jobs[job_id]['message'] = 'Generation cancelled by user'
            return
        
        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['url'] = s3_url
        jobs[job_id]['message'] = 'Complete!'
        jobs[job_id]['progress'] = 100
        # Status list is already in jobs[job_id] from progress_callback
        # Get game dates from progress callback (set by generator)
        jobs[job_id]['gameDates'] = jobs[job_id].get('gameDates', [])
        
        # Send email notification
        print(f"[API] Sending email notification. notify_email in job: '{jobs[job_id].get('notify_email')}'")
        send_job_completion_email(jobs[job_id])
        
    except Exception as e:
        # Don't set error if it was cancelled
        if not jobs[job_id].get('cancelled', False):
            jobs[job_id]['status'] = 'failed'
            jobs[job_id]['error'] = str(e)
            jobs[job_id]['message'] = f'Error: {str(e)}'
            jobs[job_id]['progress'] = 0
            
            # Send email notification for failures too
            send_job_completion_email(jobs[job_id])


if __name__ == '__main__':
    import sys
    # Use port 5001 to avoid conflict with AirPlay Receiver on macOS
    app.run(debug=True, port=5001, host='0.0.0.0')

