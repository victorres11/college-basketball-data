# Venue Data Availability in CBB API

## Summary

The CBB API provides venue/location data through two endpoints:

1. **`/games` endpoint** - Contains venue fields in game objects (often null)
2. **`/venues` endpoint** - Contains detailed venue information (979 venues available)

## Available Venue Fields in `/games` Endpoint

When querying the `/games` endpoint, each game object includes these venue-related fields:

```json
{
  "venueId": null,           // Integer ID linking to venues table (often null)
  "venue": null,             // String name of venue (often null)
  "city": null,              // String city name (often null)
  "state": null,             // String state name (often null)
  "neutralSite": false,      // Boolean (always populated)
  "attendance": null,         // Integer attendance number (often null)
  "gameNotes": null          // String additional notes (often null)
}
```

**Note:** While these fields exist in the API response structure, they are often `null` for many games, especially historical games.

## `/venues` Endpoint

The `/venues` endpoint provides detailed venue information:

### Endpoint Structure
- **URL:** `/venues`
- **Returns:** Array of venue objects
- **Total Venues:** 979 venues in database

### Venue Object Structure

```json
{
  "id": 16,                  // Integer venue ID
  "sourceId": "479",         // String source identifier
  "name": "Pauley Pavilion", // String venue name
  "city": "Los Angeles",      // String city name
  "state": "CA",             // String state name (may be null)
  "country": "United States" // String country name
}
```

### Querying Specific Venues

You can query a specific venue by ID:
```
GET /venues?id={venueId}
```

## Example: Oregon and UCLA Venues

Found in the venues database:

1. **Pauley Pavilion** (UCLA)
   - ID: 16
   - City: Los Angeles, CA
   - Country: United States

2. **Matthew Knight Arena** (Oregon)
   - ID: 191
   - City: Eugene, OR
   - Country: United States

## How to Get Complete Venue Info for a Game

To get complete venue information for a game:

1. **Check `game.venueId`** - If populated, use this to query the venues endpoint
2. **Query `/venues?id={venueId}`** - Get full venue details
3. **Fallback** - If `venueId` is null, use `game.venue`, `game.city`, `game.state` if available

### Example Code

```python
# Get game
game = api.get_game_by_id(game_id)

# Try to get venue details
venue_info = {}
if game.get('venueId'):
    venues = api._make_request("venues", {"id": game['venueId']})
    if venues and len(venues) > 0:
        venue_info = venues[0]
else:
    # Fallback to game fields
    venue_info = {
        "name": game.get('venue'),
        "city": game.get('city'),
        "state": game.get('state')
    }
```

## Limitations

1. **Venue fields often null** - Many games (especially historical) don't have venue data populated
2. **No upcoming Oregon vs UCLA game found** - Searched Dec 2025, Jan 2026, Feb 2026
3. **Venue data more reliable for recent games** - Newer games more likely to have venue data

## Recommendations

1. **For upcoming games:** Check if `venueId` is populated and query the venues endpoint
2. **For historical games:** Venue data may not be available
3. **Use `neutralSite` field:** This is always populated and indicates if game is at a neutral location
4. **Consider venue lookup:** If you have a list of common venues, you can pre-fetch venue details from `/venues` endpoint

