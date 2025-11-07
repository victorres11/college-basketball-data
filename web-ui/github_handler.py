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
        
        # Push
        subprocess.run(
            ['git', 'push'],
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

