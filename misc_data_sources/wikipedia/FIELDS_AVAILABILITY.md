# Wikipedia Data Fields Availability

## ✅ All Requested Fields Now Available

| Field | Status | Location | Format |
|-------|--------|----------|--------|
| **NCAA CHAMPIONSHIPS** | ✅ Available | `championships['ncaa_tournament']` | Array of years |
| **NCAA RUNNER UP** | ✅ Available | `championships['ncaa_runner_up']` | Array of years |
| **FINAL 4 Appearances** | ✅ Available | `tournament_appearances['final_four']` (count)<br>`tournament_appearances['recent_final_four']` (last 5 years) | Count + Array of recent years |
| **ELITE 8 Appearances** | ✅ Available | `tournament_appearances['elite_eight']` (count)<br>`tournament_appearances['recent_elite_eight']` (last 5 years) | Count + Array of recent years |
| **SWEET 16 Appearances** | ✅ Available | `tournament_appearances['sweet_sixteen']` (count)<br>`tournament_appearances['recent_sweet_sixteen']` (last 5 years) | Count + Array of recent years |
| **CONF TOURNEY TITLE** | ✅ Available | `championships['conference_tournament']` | Array of years |
| **RECENT NCAA Appearances** | ✅ Available | `tournament_appearances['recent_ncaa_appearances']` | Array of last 5 years |

## Complete Data Structure

```json
{
  "championships": {
    "ncaa_tournament": ["1995", "1975", "1973", ...],      // ✅ NCAA CHAMPIONSHIPS
    "ncaa_runner_up": ["2006", "1980"],                    // ✅ NCAA RUNNER UP
    "conference_tournament": ["2014", "2008", ...],        // ✅ CONF TOURNEY TITLE
    "ncaa_final_four": ["2021", "2008", ...],             // All Final 4 years
    "ncaa_elite_eight": ["2021", "2008", ...],            // All Elite 8 years
    "ncaa_sweet_sixteen": ["2023", "2022", ...]           // All Sweet 16 years
  },
  "tournament_appearances": {
    "ncaa_tournament": 53,                                 // Total count
    "recent_ncaa_appearances": ["2025", "2023", "2022", "2021", "2020"],  // ✅ RECENT NCAA (last 5 years)
    "final_four": 19,                                      // ✅ FINAL 4 Count
    "recent_final_four": ["2021"],                        // ✅ FINAL 4 Recent (last 5 years)
    "elite_eight": 23,                                     // ✅ ELITE 8 Count
    "recent_elite_eight": ["2021"],                       // ✅ ELITE 8 Recent (last 5 years)
    "sweet_sixteen": 37,                                   // ✅ SWEET 16 Count
    "recent_sweet_sixteen": ["2023", "2022", "2021"]     // ✅ SWEET 16 Recent (last 5 years)
  }
}
```

## Example Output (UCLA)

```json
{
  "NCAA Championships": ["1995", "1975", "1973", "1972", "1971", "1970", "1969", "1968", "1967", "1965", "1964"],
  "NCAA Runner Up": ["2006", "1980"],
  "Final 4 Count": 19,
  "Final 4 Recent (5 years)": ["2021"],
  "Elite 8 Count": 23,
  "Elite 8 Recent (5 years)": ["2021"],
  "Sweet 16 Count": 37,
  "Sweet 16 Recent (5 years)": ["2023", "2022", "2021"],
  "Conf Tourney Titles": ["2014", "2008", "2006", "1987"],
  "All NCAA Appearances Count": 53,
  "Recent NCAA Appearances (5 years)": ["2025", "2023", "2022", "2021"]
}
```

## Notes

- **Recent appearances** are filtered to the last 5 years (current year - 5)
- **Counts** represent total historical appearances
- **Recent arrays** show up to 5 most recent years (may have fewer if not enough recent appearances)
- All years are returned as strings in "YYYY" format
- Years are sorted in descending order (most recent first)
