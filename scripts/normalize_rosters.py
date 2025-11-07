#!/usr/bin/env python3
"""
Normalize cached roster files to consistent formats.
Run this once to clean up all roster data, then the generator can use simple .get() calls.
"""
import json
import os
from pathlib import Path

def normalize_year(year_str):
    """
    Normalize year field to consistent format:
    FR, SO, JR, SR, R-FR, R-SO, R-JR, R-SR
    """
    if not year_str:
        return None
    
    year_upper = year_str.upper().strip()
    
    # Handle redshirt variations first
    if "REDSHIRT" in year_upper or year_upper.startswith("R-") or year_upper.startswith("R "):
        if "FRESHMAN" in year_upper or "FR" in year_upper:
            return "R-FR"
        elif "SOPHOMORE" in year_upper or "SO" in year_upper:
            return "R-SO"
        elif "JUNIOR" in year_upper or "JR" in year_upper:
            return "R-JR"
        elif "SENIOR" in year_upper or "SR" in year_upper:
            return "R-SR"
        else:
            # Try to infer from context
            if "SO" in year_upper:
                return "R-SO"
            elif "JR" in year_upper:
                return "R-JR"
            elif "SR" in year_upper:
                return "R-SR"
            elif "FR" in year_upper:
                return "R-FR"
    
    # Handle non-redshirt variations
    if "FRESHMAN" in year_upper or year_upper.startswith("FR") or year_upper == "FR.":
        return "FR"
    elif "SOPHOMORE" in year_upper or year_upper.startswith("SO") or year_upper == "SO.":
        return "SO"
    elif "JUNIOR" in year_upper or year_upper.startswith("JR") or year_upper == "JR.":
        return "JR"
    elif "SENIOR" in year_upper or year_upper.startswith("SR") or year_upper == "SR.":
        return "SR"
    elif "5TH" in year_upper or year_upper == "5":
        return "SR"  # 5th year treated as Senior
    
    # If we can't parse it, return None (will be skipped)
    print(f"  Warning: Could not normalize year '{year_str}'")
    return None

def normalize_roster_file(file_path):
    """Normalize a single roster file."""
    print(f"Processing: {file_path.name}")
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        updated_count = 0
        for player in data.get('players', []):
            original_year = player.get('year')
            normalized_year = normalize_year(original_year)
            
            if normalized_year and normalized_year != original_year:
                player['year'] = normalized_year
                updated_count += 1
                print(f"  {player.get('name')}: '{original_year}' → '{normalized_year}'")
            elif normalized_year is None and original_year:
                # Couldn't normalize - might want to keep original or set to None
                print(f"  {player.get('name')}: Could not normalize '{original_year}'")
        
        # Save normalized data back
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  ✓ Updated {updated_count} players\n")
        return updated_count
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return 0

def main():
    """Normalize all roster files in data/rosters/2026/"""
    project_root = Path(__file__).parent.parent
    rosters_dir = project_root / 'data' / 'rosters' / '2026'
    
    if not rosters_dir.exists():
        print(f"Error: Directory not found: {rosters_dir}")
        return
    
    roster_files = list(rosters_dir.glob('*_roster.json'))
    
    if not roster_files:
        print(f"No roster files found in {rosters_dir}")
        return
    
    print(f"Found {len(roster_files)} roster files to normalize\n")
    print("=" * 60)
    
    total_updated = 0
    for roster_file in sorted(roster_files):
        updated = normalize_roster_file(roster_file)
        total_updated += updated
    
    print("=" * 60)
    print(f"\n✓ Normalization complete!")
    print(f"  Total files processed: {len(roster_files)}")
    print(f"  Total players updated: {total_updated}")

if __name__ == "__main__":
    main()

