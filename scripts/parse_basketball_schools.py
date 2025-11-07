#!/usr/bin/env python3
"""
Scalable College Basketball Roster Parser

This script automates the process of extracting basketball roster data from
multiple college athletics websites. It searches for roster pages, navigates
to print versions for cleaner extraction, and uses LLM to parse structured
player data.

Usage:
    python3 parse_basketball_rosters.py schools.txt
    
Where schools.txt contains one school name per line, e.g.:
    Oregon
    Duke
    UCLA
"""

import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI


def parse_roster_from_text(roster_text: str, school_name: str) -> List[Dict[str, Any]]:
    """
    Use LLM to parse roster text into structured JSON data.
    
    Args:
        roster_text: The raw text content from the roster page
        school_name: Name of the school for context
        
    Returns:
        List of player dictionaries with standardized fields
    """
    client = OpenAI()
    
    prompt = """This is a basketball roster.

Could you give me the:
- Name
- Jersey #
- Hometown
- Height
- Year
- Previous School

For each player in a JSON object. Return ONLY the JSON array, no other text or explanation."""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "user", "content": f"{prompt}\n\n{roster_text}"}
            ],
            temperature=0
        )
        
        result = response.choices[0].message.content
        
        # Extract JSON if wrapped in markdown code blocks
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0].strip()
        elif "```" in result:
            result = result.split("```")[1].split("```")[0].strip()
        
        roster_data = json.loads(result)
        return roster_data
        
    except Exception as e:
        print(f"Error parsing roster for {school_name}: {e}")
        return []


def process_school(school_name: str, output_dir: Path) -> Dict[str, Any]:
    """
    Process a single school's roster.
    
    This is a placeholder that demonstrates the workflow. In practice, you would
    need browser automation here to:
    1. Search for the roster page
    2. Navigate to the print version
    3. Extract the content
    
    Args:
        school_name: Name of the school to process
        output_dir: Directory to save output files
        
    Returns:
        Dictionary with school name, player count, and status
    """
    print(f"\n{'='*60}")
    print(f"Processing: {school_name}")
    print(f"{'='*60}")
    
    # Create safe filename
    safe_name = school_name.lower().replace(' ', '_').replace('&', 'and')
    
    result = {
        "school": school_name,
        "status": "pending",
        "player_count": 0,
        "output_file": None,
        "error": None
    }
    
    try:
        # NOTE: In a full implementation, you would:
        # 1. Use browser automation to search and navigate
        # 2. Extract the roster page content
        # 3. Parse with LLM
        
        # For now, this is a template that shows the structure
        print(f"⚠ Browser automation required for: {school_name}")
        print(f"  Manual steps:")
        print(f"  1. Search: '{school_name} basketball roster'")
        print(f"  2. Navigate to official athletics site")
        print(f"  3. Find and click 'Print Roster' button")
        print(f"  4. Extract content and save to: {output_dir}/{safe_name}_roster_content.txt")
        
        # Check if content file already exists
        content_file = output_dir / f"{safe_name}_roster_content.txt"
        if content_file.exists():
            print(f"✓ Found existing content file: {content_file}")
            
            with open(content_file, 'r') as f:
                roster_text = f.read()
            
            # Parse with LLM
            print(f"  Parsing roster with LLM...")
            roster_data = parse_roster_from_text(roster_text, school_name)
            
            if roster_data:
                # Save parsed data
                output_file = output_dir / f"{safe_name}_roster.json"
                with open(output_file, 'w') as f:
                    json.dump({
                        "school": school_name,
                        "player_count": len(roster_data),
                        "players": roster_data
                    }, f, indent=2)
                
                result["status"] = "success"
                result["player_count"] = len(roster_data)
                result["output_file"] = str(output_file)
                
                print(f"✓ Successfully parsed {len(roster_data)} players")
                print(f"✓ Saved to: {output_file}")
            else:
                result["status"] = "error"
                result["error"] = "Failed to parse roster data"
        else:
            result["status"] = "needs_content"
            result["error"] = f"Content file not found: {content_file}"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"✗ Error: {e}")
    
    return result


def main():
    """Main execution function."""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 parse_basketball_rosters.py schools.txt")
        print("\nOr provide school names as arguments:")
        print("  python3 parse_basketball_rosters.py Oregon Duke UCLA")
        sys.exit(1)
    
    # Determine input source
    input_arg = sys.argv[1]
    
    if Path(input_arg).exists():
        # Read from file
        with open(input_arg, 'r') as f:
            schools = [line.strip() for line in f if line.strip()]
    else:
        # Use command line arguments as school names
        schools = sys.argv[1:]
    
    if not schools:
        print("Error: No schools provided")
        sys.exit(1)
    
    print(f"Processing {len(schools)} school(s):")
    for i, school in enumerate(schools, 1):
        print(f"  {i}. {school}")
    
    # Create output directory
    output_dir = Path("/home/ubuntu/roster_outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Process each school
    results = []
    for school in schools:
        result = process_school(school, output_dir)
        results.append(result)
        time.sleep(1)  # Brief pause between schools
    
    # Summary report
    print(f"\n{'='*60}")
    print("SUMMARY REPORT")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")
    pending_count = sum(1 for r in results if r["status"] in ["pending", "needs_content"])
    
    print(f"\nTotal schools: {len(results)}")
    print(f"  ✓ Success: {success_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"  ⚠ Needs content: {pending_count}")
    
    if success_count > 0:
        print(f"\nSuccessfully parsed schools:")
        for r in results:
            if r["status"] == "success":
                print(f"  • {r['school']}: {r['player_count']} players")
    
    # Save summary
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w') as f:
        json.dump({
            "total_schools": len(results),
            "success_count": success_count,
            "error_count": error_count,
            "pending_count": pending_count,
            "results": results
        }, f, indent=2)
    
    print(f"\n✓ Summary saved to: {summary_file}")
    print(f"✓ All outputs in: {output_dir}")


if __name__ == "__main__":
    main()