# Wikipedia Infobox Data Extraction

This module extracts infobox data from Wikipedia pages for college basketball teams using the MediaWiki API.

## Features

- Extracts team information from Wikipedia infoboxes
- Uses MediaWiki API (not web scraping)
- Handles wikitext templates reliably
- Returns structured JSON data
- Supports multiple team pages

## Installation

Install the required dependency:

```bash
pip install mwparserfromhell
```

Or install from the project root:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from misc_data_sources.wikipedia.scripts.wikipedia_data import get_wikipedia_team_data

# Extract data for UCLA
data = get_wikipedia_team_data("UCLA_Bruins_men's_basketball")

print(data['university_name'])  # University of California, Los Angeles
print(data['head_coach'])        # Mick Cronin
print(data['conference'])        # Big Ten
print(data['arena'])             # Pauley Pavilion
print(data['capacity'])          # 13800
print(data['all_time_record'])   # 2007-906
```

### Command Line Usage

```bash
python misc_data_sources/wikipedia/scripts/wikipedia_data.py "UCLA_Bruins_men's_basketball"
```

### Test Multiple Teams

```bash
python misc_data_sources/wikipedia/scripts/test_wikipedia_teams.py
```

## Extracted Fields

The function returns a dictionary with the following fields:

- `page_title`: The Wikipedia page title
- `university_name`: Name of the university
- `head_coach`: Current head coach
- `conference`: Conference name
- `arena`: Arena name
- `capacity`: Arena capacity (integer)
- `all_time_record`: All-time win-loss record (W-L format)
- `championships`: Dictionary containing:
  - `ncaa_tournament`: List of NCAA tournament championship years
  - `conference_tournament`: List of conference tournament championship years
  - `regular_season`: List of regular season championship years
  - `ncaa_final_four`: List of Final Four appearance years
  - `ncaa_elite_eight`: List of Elite Eight appearance years
  - `ncaa_sweet_sixteen`: List of Sweet Sixteen appearance years
- `tournament_appearances`: Dictionary containing:
  - `ncaa_tournament`: Total number of NCAA tournament appearances
  - `final_four`: Total number of Final Four appearances
  - `elite_eight`: Total number of Elite Eight appearances
  - `sweet_sixteen`: Total number of Sweet Sixteen appearances
- `raw_template_data`: All raw template parameters (for debugging)

## Supported Infobox Templates

The module supports:
- `Infobox college basketball team`
- `Infobox CBB Team`
- Other infobox variations with "basketball" or "CBB" in the name

## Error Handling

The function includes error handling for:
- Missing pages
- Missing infobox templates
- Missing fields (returns None)
- Invalid parameter access

## Example Output

```json
{
  "page_title": "UCLA Bruins men's basketball",
  "university_name": "University of California, Los Angeles",
  "head_coach": "Mick Cronin",
  "conference": "Big Ten",
  "arena": "Pauley Pavilion",
  "capacity": 13800,
  "all_time_record": "2007-906",
  "championships": {
    "ncaa_tournament": ["1995", "1975", "1973", "1972", "1971", "1970", "1969", "1968", "1967", "1965", "1964"],
    "conference_tournament": ["2014", "2008", "2006", "1987"],
    "regular_season": ["2023", "2013", "2008", "2007", "2006", ...],
    "ncaa_final_four": ["2021", "2008", "2007", "2006", "1995", ...],
    "ncaa_elite_eight": ["2021", "2008", "2007", "2006", "1997", ...],
    "ncaa_sweet_sixteen": ["2023", "2022", "2021", "2017", "2015", ...]
  },
  "tournament_appearances": {
    "ncaa_tournament": 53,
    "final_four": 19,
    "elite_eight": 23,
    "sweet_sixteen": 37
  }
}
```

## Testing

Test results are saved to `test_data/wikipedia_test_results.json` after running the test script.

Tested teams:
- UCLA Bruins
- Michigan State Spartans
- Michigan Wolverines
- Indiana Hoosiers
- Ohio State Buckeyes
- Purdue Boilermakers
- Wisconsin Badgers
- Illinois Fighting Illini

