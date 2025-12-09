"""
S3 handler for storing generated JSON files.
"""
import boto3
import os
import requests
import json
from botocore.exceptions import ClientError


def upload_to_s3(file_path, team_name, season):
    """
    Upload generated file to S3.
    
    Args:
        file_path: Path to the generated JSON file (absolute path)
        team_name: Team name for S3 key
        season: Season year
    
    Returns:
        Public S3 URL
    """
    # Get S3 configuration from environment
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not bucket_name or not aws_access_key_id or not aws_secret_access_key:
        raise Exception(
            "S3 configuration missing. Please set S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, "
            "and AWS_SECRET_ACCESS_KEY environment variables."
        )
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        region_name=aws_region
    )
    
    # Generate S3 key (path in bucket)
    team_slug = team_name.lower().replace(' ', '_')
    s3_key = f"data/{season}/{team_slug}_scouting_data_{season}.json"
    
    try:
        # Upload file
        # Note: ACLs are disabled on this bucket, public access is handled by bucket policy
        # Set CORS headers to allow Google Sheets to fetch the file
        s3_client.upload_file(
            file_path,
            bucket_name,
            s3_key,
            ExtraArgs={
                'ContentType': 'application/json',
                'CacheControl': 'public, max-age=3600'
            }
        )
        
        # Ensure CORS is configured on the bucket (this is a one-time setup)
        # The bucket policy should allow GET requests from any origin
        # This is typically done via AWS Console or CLI, not in code
        
        # Verify the file exists and is accessible
        try:
            s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        except ClientError as e:
            print(f"Warning: Could not verify uploaded file: {e}")
        
        # Return public URL
        # Format: https://bucket-name.s3.region.amazonaws.com/key
        url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{s3_key}"
        
        return url
        
    except ClientError as e:
        raise Exception(f"S3 upload failed: {str(e)}")
    except Exception as e:
        raise Exception(f"S3 error: {str(e)}")


def get_existing_s3_file_url(team_name, season):
    """
    Generate the S3 URL for an existing file (without uploading).
    
    Args:
        team_name: Team name
        season: Season year
    
    Returns:
        Public S3 URL or None if configuration is missing
    """
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    aws_region = os.environ.get('AWS_REGION', 'us-east-1')
    
    if not bucket_name:
        return None
    
    team_slug = team_name.lower().replace(' ', '_')
    s3_key = f"data/{season}/{team_slug}_scouting_data_{season}.json"
    url = f"https://{bucket_name}.s3.{aws_region}.amazonaws.com/{s3_key}"
    
    return url


def load_historical_stats_from_s3(team_name, season):
    """
    Load historical stats (previousSeasons) from an existing S3 file.
    
    Args:
        team_name: Team name
        season: Season year
    
    Returns:
        Dictionary mapping player names to their previousSeasons data, or None if not available
    """
    try:
        url = get_existing_s3_file_url(team_name, season)
        if not url:
            return None
        
        # Fetch the existing file
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None
        
        existing_data = response.json()
        
        # Extract historical stats for each player
        historical_stats = {}
        if existing_data.get('players'):
            for player in existing_data['players']:
                player_name = player.get('name')
                if player_name and player.get('previousSeasons'):
                    historical_stats[player_name.lower()] = player['previousSeasons']
        
        return historical_stats if historical_stats else None
        
    except Exception as e:
        print(f"[S3] Could not load historical stats from existing file: {e}")
        return None

