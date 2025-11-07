"""
GitHub handler for pushing generated files to the repository.
"""
import subprocess
import os


def push_to_github(file_path, team_name, season):
    """
    Push generated file to GitHub.
    
    Args:
        file_path: Path to the generated JSON file (relative to project root)
        team_name: Team name for commit message
        season: Season year
    
    Returns:
        GitHub Pages URL
    """
    try:
        # Get project root (parent of web-ui directory)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Change to project root
        os.chdir(project_root)
        
        # Configure git if not already configured (needed for Render environment)
        git_user_name = os.environ.get('GIT_USER_NAME')
        git_user_email = os.environ.get('GIT_USER_EMAIL')
        
        if not git_user_name or not git_user_email:
            raise Exception(
                "Git user configuration missing. Please set GIT_USER_NAME and GIT_USER_EMAIL "
                "environment variables in Render dashboard."
            )
        
        # Configure git user
        subprocess.run(
            ['git', 'config', 'user.name', git_user_name],
            check=True,
            capture_output=True,
            text=True
        )
        
        subprocess.run(
            ['git', 'config', 'user.email', git_user_email],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Check if remote is configured, if not, add it
        # Get repo URL from environment or use default
        repo_url = os.environ.get('GITHUB_REPO_URL', 'https://github.com/victorres11/college-basketball-data.git')
        
        # Check if origin remote exists
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # No origin remote, add it
            subprocess.run(
                ['git', 'remote', 'add', 'origin', repo_url],
                check=True,
                capture_output=True,
                text=True
            )
        else:
            # Remote exists, but update it to ensure it's correct
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', repo_url],
                check=True,
                capture_output=True,
                text=True
            )
        
        # Ensure we're on the main branch
        current_branch_result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True
        )
        current_branch = current_branch_result.stdout.strip() if current_branch_result.returncode == 0 else 'main'
        
        if current_branch != 'main':
            # Checkout main branch
            subprocess.run(
                ['git', 'checkout', '-b', 'main'] if current_branch_result.returncode != 0 else ['git', 'checkout', 'main'],
                check=False,
                capture_output=True,
                text=True
            )
        
        # Add file
        subprocess.run(
            ['git', 'add', file_path],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Commit
        commit_msg = f"Add {team_name} {season} season data (auto-generated)"
        subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Push to origin main (explicit remote and branch)
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            check=True,
            capture_output=True,
            text=True
        )
        
        # Return GitHub Pages URL
        team_slug = team_name.lower().replace(' ', '_')
        repo = 'college-basketball-data'  # Your repo name
        return f"https://victorres11.github.io/{repo}/data/{season}/{team_slug}_scouting_data_{season}.json"
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if hasattr(e, 'stderr') else str(e)
        raise Exception(f"GitHub push failed: {error_msg}")
    except Exception as e:
        raise Exception(f"GitHub push error: {str(e)}")

