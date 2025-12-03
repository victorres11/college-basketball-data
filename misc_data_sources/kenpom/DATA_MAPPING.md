# KenPom Data Mapping: Scraping → API

## Summary

Successfully migrated from web scraping to KenPom API. All major data points are available except one.

## ✅ Data Successfully Retrieved (24 categories)

### Core Ratings
- **Adj. Efficiency** - Offense and Defense with rankings and D-1 avg
- **Adj. Tempo** - Combined tempo with ranking and D-1 avg
- **Avg. Poss. Length** - Offense and Defense with rankings

### Four Factors
- **Effective FG%** - Offense and Defense with rankings
- **Turnover %** - Offense and Defense with rankings
- **Off. Reb. %** - Offense and Defense with rankings
- **FTA/FGA** - Offense and Defense with rankings

### Miscellaneous Stats
- **3P%** - Offense and Defense with rankings
- **2P%** - Offense and Defense with rankings
- **FT%** - Offense and Defense with rankings
- **Block%** - Offense and Defense with rankings
- **Steal%** - Offense and Defense with rankings
- **Non-Stl TO%** - Offense and Defense with rankings

### Style Components
- **3PA/FGA** - Offense and Defense with rankings
- **A/FGM** - Offense and Defense with rankings

### Point Distribution
- **3-Pointers** - Offense and Defense with rankings
- **2-Pointers** - Offense and Defense with rankings
- **Free Throws** - Offense and Defense with rankings

### Strength of Schedule
- **Strength of Schedule** - Overall and Non-conference with rankings
- **Strength of Schedule Components** - Overall, Offense, and Defense with rankings

### Personnel
- **Bench Minutes** - Value and ranking
- **D-1 Experience** - Value and ranking
- **Minutes Continuity** - Value and ranking
- **Average Height** - Value and ranking

## ❌ Missing Data (1 category)

### Not Available in API
- **2-Foul Participation** - This statistic is not provided by the KenPom API. It was available in the web scraping but is not part of the official API endpoints.

## API Endpoints Used

1. **ratings** - Core team ratings, efficiency, tempo, strength of schedule
2. **four-factors** - Four Factors statistics
3. **misc-stats** - Miscellaneous shooting and defensive stats
4. **pointdist** - Point distribution percentages
5. **height** - Personnel statistics (height, experience, continuity, bench)
6. **teams** - Team lookup (name to ID mapping)

## Data Format

The API implementation maintains the same output format as the original scraping:
- Same dictionary structure (`report_table_structured`)
- Same field names and organization
- Same value/ranking separation
- D-1 averages calculated where applicable

## Advantages

- ✅ No IP blocking issues
- ✅ No cookie management
- ✅ Faster and more reliable
- ✅ Official API support
- ✅ Structured JSON responses
- ✅ No HTML parsing required
- ✅ Works in production without proxy

