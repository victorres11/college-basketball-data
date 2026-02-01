// ========================================
// CATEGORY 1: TEAM META INFORMATION
// ========================================

function GET_TEAM_META(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    // Format dataGenerated timestamp to EST
    var dataGeneratedFormatted = data.dataGenerated;
    if (data.dataGenerated) {
      try {
        // Parse ISO timestamp (should be in UTC format like "2025-12-02T19:36:45.123456+00:00" or "2025-12-02T19:36:45.123456Z")
        var isoString = data.dataGenerated;
        // Ensure it's treated as UTC if no timezone specified
        if (!isoString.includes('Z') && !isoString.match(/[+-]\d{2}:\d{2}$/)) {
          // If no timezone info, assume UTC and append Z
          isoString = isoString + 'Z';
        }
        var date = new Date(isoString);
        
        // Format as "YYYY-MM-DD HH:MM AM/PM (EST)"
        var dateStr = Utilities.formatDate(date, "America/New_York", "yyyy-MM-dd");
        var timeStr = Utilities.formatDate(date, "America/New_York", "hh:mm a");
        // Determine if EST or EDT (America/New_York handles both automatically)
        // For simplicity, we'll use EST as the label (though it may be EDT during daylight saving)
        dataGeneratedFormatted = dateStr + " " + timeStr + " (EST)";
      } catch (e) {
        // If parsing fails, use original value
        dataGeneratedFormatted = data.dataGenerated;
      }
    }
    
    var table = [
      ["Field", "Value"],
      ["Team", data.team],
      ["Season", data.season],
      ["Season Type", data.seasonType],
      ["Data Generated", dataGeneratedFormatted],
      ["Total Players", data.metadata.totalPlayers],
      ["API Calls", data.metadata.apiCalls]
    ];
    
    // Mascot - always include (use "N/A" if missing)
    table.push(["Mascot", data.mascot || "N/A"]);

    // Total record - always include section
    table.push([""]);
    table.push(["=== RECORD ==="]);
    var totalWins = (data.totalRecord && data.totalRecord.wins !== undefined) ? data.totalRecord.wins : "N/A";
    var totalLosses = (data.totalRecord && data.totalRecord.losses !== undefined) ? data.totalRecord.losses : "N/A";
    var totalGames = (data.totalRecord && data.totalRecord.games !== undefined) ? data.totalRecord.games : "N/A";
    var totalRecordStr = (totalWins !== "N/A" && totalLosses !== "N/A") ? totalWins + "-" + totalLosses : "N/A";
    table.push(["Total Record", totalRecordStr]);
    table.push(["Total Wins", totalWins]);
    table.push(["Total Losses", totalLosses]);
    table.push(["Total Games", totalGames]);

    // Conference record - always include section
    table.push([""]);
    table.push(["=== CONFERENCE RECORD ==="]);
    var confWins = (data.conferenceRecord && data.conferenceRecord.wins !== undefined) ? data.conferenceRecord.wins : "N/A";
    var confLosses = (data.conferenceRecord && data.conferenceRecord.losses !== undefined) ? data.conferenceRecord.losses : "N/A";
    var confGames = (data.conferenceRecord && data.conferenceRecord.games !== undefined) ? data.conferenceRecord.games : "N/A";
    var confRecordStr = (confWins !== "N/A" && confLosses !== "N/A") ? confWins + "-" + confLosses : "N/A";
    table.push(["Conference Record", confRecordStr]);
    table.push(["Conference Wins", confWins]);
    table.push(["Conference Losses", confLosses]);
    table.push(["Conference Games", confGames]);
    
    // NET Rating - always include section
    table.push([""]);
    table.push(["=== NET RATING ==="]);
    table.push(["NET Rank", (data.netRating && data.netRating.rating) || "N/A"]);
    table.push(["Previous Rank", (data.netRating && data.netRating.previousRating) || "N/A"]);
    table.push(["Source", (data.netRating && data.netRating.source) || "bballnet.com"]);
    table.push(["URL", (data.netRating && data.netRating.url) || "N/A"]);
    
    // AP Rankings - always include section (use "-" for unranked)
    table.push([""]);
    table.push(["=== AP RANKINGS ==="]);
    var currentRank = (data.metadata && data.metadata.apRankings && data.metadata.apRankings.current !== null && data.metadata.apRankings.current !== undefined)
      ? "#" + data.metadata.apRankings.current
      : "-";
    var highestRank = (data.metadata && data.metadata.apRankings && data.metadata.apRankings.highest !== null && data.metadata.apRankings.highest !== undefined)
      ? "#" + data.metadata.apRankings.highest
      : "-";
    table.push(["Current Rank", currentRank]);
    table.push(["Highest Rank", highestRank]);
    
    // Coach History - always show section headers, variable 0-6 season rows
    table.push([""]);
    table.push(["=== COACH HISTORY (Last 6 Complete Seasons) ==="]);
    table.push(["Season", "Conference", "Overall W-L", "Conf W-L", "NCAA Tournament", "Seed", "Coach"]);

    // Add season rows (0-6 rows depending on data availability)
    if (data.coachHistory && data.coachHistory.seasons && data.coachHistory.seasons.length > 0) {
      var seasonsToShow = data.coachHistory.seasons.slice(0, 6);
      seasonsToShow.forEach(function(season) {
        table.push([
          season.season || "",
          season.conference || "",
          season.overallWL || "",
          season.conferenceWL || "",
          season.ncaaTournament || "",
          season.seed || "",
          season.coach || ""
        ]);
      });
    }

    // Averages section - always include
    table.push([""]);
    table.push(["=== AVERAGES (Last 6 Seasons) ==="]);
    table.push(["Average Overall Wins", (data.coachHistory && data.coachHistory.averageOverallWins !== undefined) ? data.coachHistory.averageOverallWins : "N/A"]);
    table.push(["Average Conference Wins", (data.coachHistory && data.coachHistory.averageConferenceWins !== undefined) ? data.coachHistory.averageConferenceWins : "N/A"]);

    // Winningest coach section - always include
    var wc = (data.coachHistory && data.coachHistory.winningestCoach) || {};
    table.push([""]);
    table.push(["=== WINNINGEST COACH ==="]);
    table.push(["Coach", wc.coach || "N/A"]);
    var yearsStr = (wc.from && wc.to) ? wc.from + " - " + wc.to : "N/A";
    table.push(["Years", yearsStr]);
    table.push(["Seasons", wc.years || "N/A"]);
    table.push(["Record", wc.record || "N/A"]);
    table.push(["Wins", (wc.wins !== undefined) ? wc.wins : "N/A"]);
    table.push(["Losses", (wc.losses !== undefined) ? wc.losses : "N/A"]);
    table.push(["Win Percentage", wc.winPercentage || "N/A"]);
    table.push(["URL", (data.coachHistory && data.coachHistory.winningestCoachUrl) || "N/A"]);

    // Source and URL - always include
    table.push([""]);
    table.push(["Source", (data.coachHistory && data.coachHistory.source) || "N/A"]);
    table.push(["URL", (data.coachHistory && data.coachHistory.url) || "N/A"]);
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// SCHOOL COACHING HISTORY
// ========================================

function GET_SCHOOL_COACHING_HISTORY(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    // Check if coach history exists
    if (!data.coachHistory || !data.coachHistory.seasons || data.coachHistory.seasons.length === 0) {
      return [["Coach history not available"], ["Data may not have been generated with coach history information"]];
    }
    
    var table = [
      ["=== SCHOOL COACHING HISTORY ==="],
      [""],
      ["Season", "Conference", "Overall W-L", "Conf W-L", "NCAA Tournament", "Seed", "Coach"]
    ];
    
    // Get all seasons (full history, not just last 6)
    data.coachHistory.seasons.forEach(function(season) {
      table.push([
        season.season || "",
        season.conference || "",
        season.overallWL || "",
        season.conferenceWL || "",
        season.ncaaTournament || "",
        season.seed || "",
        season.coach || ""
      ]);
    });
    
    // Add source information
    if (data.coachHistory.source) {
      table.push([""]);
      table.push(["Source", data.coachHistory.source]);
    }
    if (data.coachHistory.url) {
      table.push(["URL", data.coachHistory.url]);
    }
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// CURRENT COACH SEASON COUNT
// ========================================

function GET_CURRENT_COACH_SEASON_COUNT(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    // Check if coach history exists
    if (!data.coachHistory || !data.coachHistory.seasons || data.coachHistory.seasons.length === 0) {
      return "N/A";
    }
    
    var seasons = data.coachHistory.seasons;
    
    // Get the current coach (most recent season, first in array)
    var currentCoach = seasons[0].coach;
    if (!currentCoach) {
      return "N/A";
    }
    
    // Count consecutive seasons with the same coach (starting from most recent)
    var count = 0;
    for (var i = 0; i < seasons.length; i++) {
      if (seasons[i].coach === currentCoach) {
        count++;
      } else {
        // Stop counting when we hit a different coach
        break;
      }
    }
    
    // Add 1 for the current incomplete season (which is skipped in the data)
    // The scraper skips the current incomplete season, so if the coach is still there,
    // we add 1 to account for the current season
    count = count + 1;
    
    return count.toString();
  } catch (e) {
    return "Error: " + e.message;
  }
}

// ========================================
// CATEGORY 2: TEAM RANKINGS
// ========================================

function GET_TEAM_RANKINGS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    // Check if rankings data exists
    if (!data.conferenceRankings || !data.conferenceRankings.rankings) {
      return [["Error: Conference rankings data not found in JSON"]];
    }
    // D1 rankings might be empty for early season data, so make it optional
    if (!data.d1Rankings) {
      data.d1Rankings = { rankings: {} };
    }
    if (!data.d1Rankings.rankings) {
      data.d1Rankings.rankings = {};
    }
    
    var confRankings = data.conferenceRankings.rankings;
    var d1Rankings = data.d1Rankings.rankings;
    
    var table = [[
      "Stat Category",
      "Conference Rank", "Conference Total", "Conference Value",
      "D1 Rank", "D1 Total", "D1 Value"
    ]];
    
    // Get all stat categories
    var categories = Object.keys(confRankings);
    
    categories.forEach(function(cat) {
      var confData = confRankings[cat];
      var d1Data = d1Rankings[cat];
      
      // Convert camelCase to readable format
      var readableName = cat.replace(/([A-Z])/g, ' $1').replace(/^./, function(str){ return str.toUpperCase(); });
      
      // Handle cases where D1 data might not exist (e.g., early season)
      table.push([
        readableName,
        confData && confData.rank ? confData.rank : "",
        confData && confData.totalTeams ? confData.totalTeams : "",
        confData && confData.value !== undefined ? confData.value : "",
        d1Data && d1Data.rank ? d1Data.rank : "",
        d1Data && d1Data.totalTeams ? d1Data.totalTeams : "",
        d1Data && d1Data.value !== undefined ? d1Data.value : ""
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message], ["Check that the URL in cell A1 is correct and the endpoint is accessible"]];
  }
}

// ========================================
// CATEGORY 3: TEAM AGGREGATED SEASON STATS
// ========================================

function GET_TEAM_SEASON_STATS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    var stats = data.teamSeasonStats;
    
    var table = [
      ["=== GENERAL INFO ==="],
      ["Season", stats.season],
      ["Team", stats.team],
      ["Conference", stats.conference],
      ["Games", stats.games],
      ["Wins", stats.wins],
      ["Losses", stats.losses],
      ["Win %", (stats.wins / stats.games * 100).toFixed(1) + "%"],
      ["Total Minutes", stats.totalMinutes],
      ["Pace", stats.pace],
      [""],
      ["=== TEAM STATS ===", "Team", "Opponent"],
      ["Possessions", stats.teamStats.possessions, stats.opponentStats.possessions],
      ["True Shooting %", stats.teamStats.trueShooting, stats.opponentStats.trueShooting],
      ["Rating", stats.teamStats.rating, stats.opponentStats.rating],
      [""],
      ["--- Scoring ---"],
      ["Total Points", stats.teamStats.points.total, stats.opponentStats.points.total],
      ["Points Per Game", (stats.teamStats.points.total / stats.games).toFixed(1), (stats.opponentStats.points.total / stats.games).toFixed(1)],
      ["Points in Paint", stats.teamStats.points.inPaint, stats.opponentStats.points.inPaint],
      ["Points off Turnovers", stats.teamStats.points.offTurnovers, stats.opponentStats.points.offTurnovers],
      ["Fast Break Points", stats.teamStats.points.fastBreak, stats.opponentStats.points.fastBreak],
      [""],
      ["--- Field Goals ---"],
      ["FG Made", stats.teamStats.fieldGoals.made, stats.opponentStats.fieldGoals.made],
      ["FG Attempted", stats.teamStats.fieldGoals.attempted, stats.opponentStats.fieldGoals.attempted],
      ["FG %", stats.teamStats.fieldGoals.pct + "%", stats.opponentStats.fieldGoals.pct + "%"],
      [""],
      ["--- Two-Point Field Goals ---"],
      ["2PT Made", stats.teamStats.twoPointFieldGoals.made, stats.opponentStats.twoPointFieldGoals.made],
      ["2PT Attempted", stats.teamStats.twoPointFieldGoals.attempted, stats.opponentStats.twoPointFieldGoals.attempted],
      ["2PT %", stats.teamStats.twoPointFieldGoals.pct + "%", stats.opponentStats.twoPointFieldGoals.pct + "%"],
      [""],
      ["--- Three-Point Field Goals ---"],
      ["3PT Made", stats.teamStats.threePointFieldGoals.made, stats.opponentStats.threePointFieldGoals.made],
      ["3PT Attempted", stats.teamStats.threePointFieldGoals.attempted, stats.opponentStats.threePointFieldGoals.attempted],
      ["3PT %", stats.teamStats.threePointFieldGoals.pct + "%", stats.opponentStats.threePointFieldGoals.pct + "%"],
      [""],
      ["--- Free Throws ---"],
      ["FT Made", stats.teamStats.freeThrows.made, stats.opponentStats.freeThrows.made],
      ["FT Attempted", stats.teamStats.freeThrows.attempted, stats.opponentStats.freeThrows.attempted],
      ["FT %", stats.teamStats.freeThrows.pct + "%", stats.opponentStats.freeThrows.pct + "%"],
      [""],
      ["--- Rebounds ---"],
      ["Offensive Rebounds", stats.teamStats.rebounds.offensive, stats.opponentStats.rebounds.offensive],
      ["Defensive Rebounds", stats.teamStats.rebounds.defensive, stats.opponentStats.rebounds.defensive],
      ["Total Rebounds", stats.teamStats.rebounds.total, stats.opponentStats.rebounds.total],
      [""],
      ["--- Other Stats ---"],
      ["Assists", stats.teamStats.assists, stats.opponentStats.assists],
      ["Steals", stats.teamStats.steals, stats.opponentStats.steals],
      ["Blocks", stats.teamStats.blocks, stats.opponentStats.blocks],
      ["Turnovers", stats.teamStats.turnovers.total, stats.opponentStats.turnovers.total],
      ["Team Turnovers", stats.teamStats.turnovers.teamTotal, stats.opponentStats.turnovers.teamTotal],
      [""],
      ["--- Fouls ---"],
      ["Total Fouls", stats.teamStats.fouls.total, stats.opponentStats.fouls.total],
      ["Technical Fouls", stats.teamStats.fouls.technical, stats.opponentStats.fouls.technical],
      ["Flagrant Fouls", stats.teamStats.fouls.flagrant, stats.opponentStats.fouls.flagrant],
      [""],
      ["--- Four Factors ---"],
      ["Effective FG %", stats.teamStats.fourFactors.effectiveFieldGoalPct + "%", stats.opponentStats.fourFactors.effectiveFieldGoalPct + "%"],
      ["Turnover Ratio", stats.teamStats.fourFactors.turnoverRatio, stats.opponentStats.fourFactors.turnoverRatio],
      ["Offensive Rebound %", stats.teamStats.fourFactors.offensiveReboundPct + "%", stats.opponentStats.fourFactors.offensiveReboundPct + "%"],
      ["Free Throw Rate", stats.teamStats.fourFactors.freeThrowRate + "%", stats.opponentStats.fourFactors.freeThrowRate + "%"]
    ];
    
    // Per-game stats section - always include (use safe defaults if missing)
    var pg = stats.perGameStats || {};
    var pgTeam = (pg && pg.teamStats) || {};
    var pgOpp = (pg && pg.opponentStats) || {};
    var pgMargins = (pg && pg.margins) || {};
    var pgRatios = (pg && pg.ratios) || {};

    table.push([""]);
    table.push(["--- Per Game Stats ---"]);
    table.push(["", "Team", "Opponent"]);
    table.push(["3PT FGM/G", (pgTeam.threePointFieldGoalsMadePerGame || 0).toFixed(2), ""]);
    table.push(["3PT FGA/G", (pgTeam.threePointFieldGoalsAttemptedPerGame || 0).toFixed(2), ""]);
    table.push(["Off Reb/G", (pgTeam.offensiveReboundsPerGame || 0).toFixed(2), ""]);
    table.push(["TO/G", (pgTeam.turnoversPerGame || 0).toFixed(2), ""]);
    table.push(["APG", (pgTeam.assistsPerGame || 0).toFixed(2), ""]);
    table.push(["FTM/G", (pgTeam.freeThrowsMadePerGame || 0).toFixed(2), ""]);
    table.push(["FTA/G", (pgTeam.freeThrowsAttemptedPerGame || 0).toFixed(2), ""]);
    table.push(["FT%", (pgTeam.freeThrowPct || 0).toFixed(1) + "%", ""]);
    table.push(["Fouls/G", (pgTeam.foulsPerGame || 0).toFixed(2), ""]);
    table.push(["Def Rebs/G", (pgTeam.defensiveReboundsPerGame || 0).toFixed(2), ""]);
    table.push(["SPG", (pgTeam.stealsPerGame || 0).toFixed(2), ""]);
    table.push(["BPG", (pgTeam.blocksPerGame || 0).toFixed(2), ""]);
    table.push([""]);
    table.push(["--- Opponent Per Game Stats ---"]);
    table.push(["Def. PPG", "", (pgOpp.pointsPerGame || 0).toFixed(2)]);
    table.push(["Def. FG%", "", (pgOpp.fieldGoalPct || 0).toFixed(1) + "%"]);
    table.push(["Def. 3P%", "", (pgOpp.threePointPct || 0).toFixed(1) + "%"]);
    table.push(["TO Forced/G", "", (pgOpp.turnoversForcedPerGame || 0).toFixed(2)]);
    table.push([""]);
    table.push(["--- Margins (Per Game) ---"]);
    table.push(["Point Margin", (pgMargins.pointMargin || 0).toFixed(2), ""]);
    table.push(["Rebound Margin", (pgMargins.reboundMargin || 0).toFixed(2), ""]);
    table.push(["TO Margin", (pgMargins.turnoverMargin || 0).toFixed(2), ""]);
    table.push([""]);
    table.push(["--- Ratios ---"]);
    table.push(["A:TO Ratio", (pgRatios.assistToTurnoverRatio || 0).toFixed(2), ""]);
    
    // Possession game records - always include (use defaults if missing)
    table.push([""]);
    table.push(["=== POSSESSION GAME RECORDS ==="]);
    table.push(["1-Possession Games",
     (stats.possessionGameRecords && stats.possessionGameRecords.onePossession ?
      stats.possessionGameRecords.onePossession.wins + "-" + stats.possessionGameRecords.onePossession.losses :
      "0-0")]);
    table.push(["2-Possession Games",
     (stats.possessionGameRecords && stats.possessionGameRecords.twoPossession ?
      stats.possessionGameRecords.twoPossession.wins + "-" + stats.possessionGameRecords.twoPossession.losses :
      "0-0")]);
    
    // Home/Away/Neutral records - always include (use "N/A" if missing)
    table.push([""]);
    table.push(["=== HOME/AWAY/NEUTRAL RECORDS ==="]);

    // Home records
    var homeRecord = data.homeRecord || {};
    var homeWins = homeRecord.wins !== undefined ? homeRecord.wins : "N/A";
    var homeLosses = homeRecord.losses !== undefined ? homeRecord.losses : "N/A";
    var homeGames = homeRecord.games !== undefined ? homeRecord.games : "N/A";
    var homeRecordStr = (homeWins !== "N/A" && homeLosses !== "N/A") ? homeWins + "-" + homeLosses : "N/A";
    table.push(["Home Record", homeRecordStr]);
    table.push(["Home Wins", homeWins]);
    table.push(["Home Losses", homeLosses]);
    table.push(["Home Games", homeGames]);

    // Away records
    var awayRecord = data.awayRecord || {};
    var awayWins = awayRecord.wins !== undefined ? awayRecord.wins : "N/A";
    var awayLosses = awayRecord.losses !== undefined ? awayRecord.losses : "N/A";
    var awayGames = awayRecord.games !== undefined ? awayRecord.games : "N/A";
    var awayRecordStr = (awayWins !== "N/A" && awayLosses !== "N/A") ? awayWins + "-" + awayLosses : "N/A";
    table.push(["Away Record", awayRecordStr]);
    table.push(["Away Wins", awayWins]);
    table.push(["Away Losses", awayLosses]);
    table.push(["Away Games", awayGames]);

    // Neutral records
    var neutralRecord = data.neutralRecord || {};
    var neutralWins = neutralRecord.wins !== undefined ? neutralRecord.wins : "N/A";
    var neutralLosses = neutralRecord.losses !== undefined ? neutralRecord.losses : "N/A";
    var neutralGames = neutralRecord.games !== undefined ? neutralRecord.games : "N/A";
    var neutralRecordStr = (neutralWins !== "N/A" && neutralLosses !== "N/A") ? neutralWins + "-" + neutralLosses : "N/A";
    table.push(["Neutral Record", neutralRecordStr]);
    table.push(["Neutral Wins", neutralWins]);
    table.push(["Neutral Losses", neutralLosses]);
    table.push(["Neutral Games", neutralGames]);
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// CATEGORY 3B: QUADRANT RECORDS
// ========================================

function GET_QUADRANT_RECORDS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    // Check if quadrant records exist
    if (!data.quadrantRecords) {
      return [["Quadrant records not available"], ["Data may not have been generated with quadrant information"]];
    }
    
    var table = [
      ["=== QUADRANT RECORDS ==="],
      [""],
      ["Quadrant", "Record", "Wins", "Losses", "Opponents"]
    ];
    
    // Process each quadrant (1-4)
    for (var i = 1; i <= 4; i++) {
      var quadKey = "quad" + i;
      var quadData = data.quadrantRecords[quadKey];
      
      if (quadData) {
        var record = quadData.record || "0-0";
        var wins = quadData.wins || 0;
        var losses = quadData.losses || 0;
        var opponents = quadData.opponents || [];
        
        // Format opponents list
        var opponentsStr = "";
        if (opponents.length > 0) {
          // Convert normalized names back to readable format
          opponentsStr = opponents.map(function(opp) {
            return opp.replace(/_/g, ' ').replace(/\b\w/g, function(l) { return l.toUpperCase(); });
          }).join(", ");
        } else {
          opponentsStr = "None";
        }
        
        table.push([
          "Quad " + i,
          record,
          wins,
          losses,
          opponentsStr
        ]);
      } else {
        table.push([
          "Quad " + i,
          "0-0",
          0,
          0,
          "None"
        ]);
      }
    }
    
    // Upcoming games section - always show headers, variable 0-N data rows
    var q1Count = 0;
    if (data.upcomingGames && data.upcomingGames.length > 0) {
      for (var k = 0; k < data.upcomingGames.length; k++) {
        if (data.upcomingGames[k].quadrant === "Q1") {
          q1Count++;
        }
      }
    }

    table.push([""]);
    table.push(["=== UPCOMING GAMES ==="]);
    table.push(["Upcoming Q1 Games", q1Count]);
    table.push([""]);
    table.push(["Quadrant", "Location", "Rank", "Opponent", "Date"]);

    // Add game rows (0-N rows depending on data availability)
    if (data.upcomingGames && data.upcomingGames.length > 0) {
      for (var j = 0; j < data.upcomingGames.length; j++) {
        var game = data.upcomingGames[j];
        var rankStr = game.rank ? "(" + game.rank + ")" : "";
        table.push([
          game.quadrant || "",
          game.location || "",
          rankStr,
          game.opponent || "",
          game.date || ""
        ]);
      }
    }
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// CATEGORY 4: TEAM GAME-BY-GAME STATS
// ========================================

function GET_TEAM_GAMES(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());

    // Check if teamGameStats exists
    if (!data.teamGameStats) {
      return [["Error: teamGameStats data not found in JSON"], ["Run DEBUG_JSON to check structure"]];
    }

    if (!Array.isArray(data.teamGameStats)) {
      return [["Error: teamGameStats is not an array"], ["Type: " + typeof data.teamGameStats]];
    }

    var table = [[
      "Date", "Opponent", "Home/Away", "Conference", "Result",
      "Score", "Opp Score",
      "FGM-FGA", "FG%", "3PM-3PA", "3P%", "FTM-FTA", "FT%",
      "OReb", "DReb", "TReb", "Ast", "Stl", "Blk", "TO", "Fouls",
      "Opp FGM-FGA", "Opp FG%", "Opp 3PM-3PA", "Opp 3P%", "Opp FTM-FTA", "Opp FT%",
      "Opp OReb", "Opp DReb", "Opp TReb", "Opp Ast", "Opp Stl", "Opp Blk", "Opp TO", "Opp Fouls"
    ]];

    // Collect all games with sortable dates
    var allGames = [];

    // Process played games
    data.teamGameStats.forEach(function(game) {
      var result = game.teamStats.points.total > game.opponentStats.points.total ? "W" : "L";

      // Format date from '2024-11-05T03:30:00.000Z' to '11/5'
      var dateObj = new Date(game.startDate);
      var month = dateObj.getMonth() + 1; // getMonth() returns 0-11
      var day = dateObj.getDate();
      var formattedDate = month + "/" + day;

      // Format opponent name: "@ Team" for away, "Team (N)" for neutral, "Team" for home
      var opponentDisplay = game.neutralSite 
        ? game.opponent + " (N)" 
        : (game.isHome ? game.opponent : "@ " + game.opponent);
      
      allGames.push({
        sortDate: dateObj,
        row: [
          formattedDate,
          opponentDisplay,
          game.neutralSite ? "Neutral" : (game.isHome ? "Home" : "Away"),
          game.conferenceGame ? "Conf" : "Non-Conf",
          result,
          game.teamStats.points.total,
          game.opponentStats.points.total,
          game.teamStats.fieldGoals.made + "-" + game.teamStats.fieldGoals.attempted,
          (game.teamStats.fieldGoals.pct / 100).toFixed(3),
          game.teamStats.threePointFieldGoals.made + "-" + game.teamStats.threePointFieldGoals.attempted,
          (game.teamStats.threePointFieldGoals.pct / 100).toFixed(3),
          game.teamStats.freeThrows.made + "-" + game.teamStats.freeThrows.attempted,
          (game.teamStats.freeThrows.pct / 100).toFixed(3),
          game.teamStats.rebounds.offensive,
          game.teamStats.rebounds.defensive,
          game.teamStats.rebounds.total,
          game.teamStats.assists,
          game.teamStats.steals,
          game.teamStats.blocks,
          game.teamStats.turnovers.total,
          game.teamStats.fouls.total,
          game.opponentStats.fieldGoals.made + "-" + game.opponentStats.fieldGoals.attempted,
          (game.opponentStats.fieldGoals.pct / 100).toFixed(3),
          game.opponentStats.threePointFieldGoals.made + "-" + game.opponentStats.threePointFieldGoals.attempted,
          (game.opponentStats.threePointFieldGoals.pct / 100).toFixed(3),
          game.opponentStats.freeThrows.made + "-" + game.opponentStats.freeThrows.attempted,
          (game.opponentStats.freeThrows.pct / 100).toFixed(3),
          game.opponentStats.rebounds.offensive,
          game.opponentStats.rebounds.defensive,
          game.opponentStats.rebounds.total,
          game.opponentStats.assists,
          game.opponentStats.steals,
          game.opponentStats.blocks,
          game.opponentStats.turnovers.total,
          game.opponentStats.fouls.total
        ]
      });
    });

    // Process upcoming games (if available)
    if (data.upcomingGames && data.upcomingGames.length > 0) {
      data.upcomingGames.forEach(function(game) {
        // Parse date from 'MM/DD/YYYY' format (e.g., '12/17/2025')
        var dateParts = game.date.split('/');
        var upcomingDateObj = new Date(dateParts[2], dateParts[0] - 1, dateParts[1]);
        var month = upcomingDateObj.getMonth() + 1;
        var day = upcomingDateObj.getDate();
        var formattedDate = month + "/" + day;

        allGames.push({
          sortDate: upcomingDateObj,
          row: [
            formattedDate,
            game.opponent || "",
            game.location || "",
            "",  // Conference - empty for upcoming
            "",  // Result - empty for upcoming
            "",  // Score
            "",  // Opp Score
            "",  // FGM-FGA
            "",  // FG%
            "",  // 3PM-3PA
            "",  // 3P%
            "",  // FTM-FTA
            "",  // FT%
            "",  // OReb
            "",  // DReb
            "",  // TReb
            "",  // Ast
            "",  // Stl
            "",  // Blk
            "",  // TO
            "",  // Fouls
            "",  // Opp FGM-FGA
            "",  // Opp FG%
            "",  // Opp 3PM-3PA
            "",  // Opp 3P%
            "",  // Opp FTM-FTA
            "",  // Opp FT%
            "",  // Opp OReb
            "",  // Opp DReb
            "",  // Opp TReb
            "",  // Opp Ast
            "",  // Opp Stl
            "",  // Opp Blk
            "",  // Opp TO
            ""   // Opp Fouls
          ]
        });
      });
    }

    // Deduplicate games by date - prefer played games (with results) over upcoming games
    var gamesByDate = {};
    allGames.forEach(function(game) {
      var dateKey = game.sortDate.toISOString().split('T')[0]; // YYYY-MM-DD
      var hasResult = game.row[4] !== ""; // Result column (W/L)

      if (!gamesByDate[dateKey]) {
        // First game for this date
        gamesByDate[dateKey] = game;
      } else if (hasResult && gamesByDate[dateKey].row[4] === "") {
        // Current game has result, existing one doesn't - replace
        gamesByDate[dateKey] = game;
      }
      // If existing game has result, keep it (don't replace with upcoming)
    });

    // Convert back to array and sort chronologically
    var deduplicatedGames = Object.values(gamesByDate);
    deduplicatedGames.sort(function(a, b) {
      return a.sortDate - b.sortDate;
    });

    // Build final table
    deduplicatedGames.forEach(function(game) {
      table.push(game.row);
    });

    return table;
  } catch (e) {
    return [["Error: " + e.message], ["Check the data structure with DEBUG_JSON"]];
  }
}

// ========================================
// CATEGORY 5: INDIVIDUAL PLAYERS - ALL DATA
// ========================================

function GET_PLAYERS_FULL(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var table = [[
      // Basic Info
      "Name", "Jersey", "Position", "Height", "Class", "Freshman", "Hometown", "High School",
      // Season Totals - Playing Time
      "Games", "GS", "Min", "MPG",
      // Season Totals - Scoring
      "Pts", "PPG",
      // Season Totals - Rebounds
      "OReb", "DReb", "TReb", "RPG",
      // Season Totals - Playmaking
      "Ast", "APG", "TO", "A/TO",
      // Season Totals - Defense
      "Stl", "SPG", "Blk", "BPG",
      // Season Totals - Shooting
      "FGM", "FGA", "FG%", "2PM", "2PA", "2P%",
      "3PM", "3PA", "3P%", "FTM", "FTA", "FT%",
      // Advanced Stats
      "ORtg", "DRtg", "NetRtg", "PORPAG", "Usage%",
      "AST/TO", "OReb%", "FTR", "eFG%", "TS%",
      "WS Off", "WS Def", "WS Total", "WS/40",
      // Conference Rankings - Per Game Stats (original 13)
      "PPG Rank", "APG Rank", "RPG Rank", "SPG Rank", "BPG Rank",
      "FG% Rank", "3P% Rank", "FT% Rank", "eFG% Rank",
      "A/TO Rank", "ORtg Rank", "DRtg Rank", "NetRtg Rank",
      // Conference Rankings - New Total/Volume Stats (12 new)
      "MPG Rank", "FGM Rank", "FGA Rank", "3PM Rank", "3PA Rank",
      "FTM Rank", "FTA Rank", "OReb Rank", "DReb Rank", "TReb Rank",
      "Ast Rank", "Blk Rank",
      // Season Totals - Fouls/Ejections (moved to end)
      "Fouls", "Foul Outs", "Ejections",
      // Shooting Breakdown (moved to end to preserve column positions)
      "Dunks Att", "Dunks Made", "Dunks %",
      "Layups Att", "Layups Made", "Layups %",
      "Tip-Ins Att", "Tip-Ins Made", "Tip-Ins %",
      "2PT Jumpers Att", "2PT Jumpers Made", "2PT Jumpers %",
      "3PT Jumpers Att", "3PT Jumpers Made", "3PT Jumpers %"
    ]];
    
    // Sort players: Top 9 by MPG (then by jersey), rest by total minutes
    var playersCopy = data.players.slice(); // Make a copy to sort
    
    // Sort all players by MPG first to identify top 9
    playersCopy.sort(function(a, b) {
      var mpgA = a.seasonTotals.mpg || 0;
      var mpgB = b.seasonTotals.mpg || 0;
      return mpgB - mpgA; // Descending
    });
    
    // Take top 9 by MPG
    var top9 = playersCopy.slice(0, 9);
    var rest = playersCopy.slice(9);
    
    // Sort top 9 by jersey number (low to high)
    top9.sort(function(a, b) {
      var jerseyA = parseInt(a.jerseyNumber) || 0;
      var jerseyB = parseInt(b.jerseyNumber) || 0;
      return jerseyA - jerseyB; // Ascending
    });
    
    // Sort rest by total minutes (high to low)
    rest.sort(function(a, b) {
      var minA = a.seasonTotals.minutes || 0;
      var minB = b.seasonTotals.minutes || 0;
      return minB - minA; // Descending
    });
    
    // Combine: top 9 first, then rest
    var sortedPlayers = top9.concat(rest);
    
    // Helper function to safely get nested values
    var safe = function(obj, path, defaultVal) {
      if (!obj) return defaultVal || "";
      var keys = path.split('.');
      var val = obj;
      for (var i = 0; i < keys.length; i++) {
        if (val === null || val === undefined) return defaultVal || "";
        val = val[keys[i]];
      }
      return val !== null && val !== undefined ? val : (defaultVal || "");
    };
    
    sortedPlayers.forEach(function(player) {
      var st = player.seasonTotals;
      var cr = player.conferenceRankings;
      
      table.push([
        // Basic Info
        player.name || "",
        player.jerseyNumber || "",
        player.position || "",
        player.height || "",
        player.class || "",
        player.isFreshman || false,
        player.hometown || "",
        player.highSchool || "",
        // Season Totals - Playing Time
        safe(st, 'games', 0),
        safe(st, 'gamesStarted', 0),
        safe(st, 'minutes', 0),
        safe(st, 'mpg', 0),
        // Season Totals - Scoring
        safe(st, 'points', 0),
        safe(st, 'ppg', 0),
        // Season Totals - Rebounds
        safe(st, 'rebounds.offensive', 0),
        safe(st, 'rebounds.defensive', 0),
        safe(st, 'rebounds.total', 0),
        safe(st, 'rpg', 0),
        // Season Totals - Playmaking
        safe(st, 'assists', 0),
        safe(st, 'apg', 0),
        safe(st, 'turnovers', 0),
        safe(st, 'assistToTurnoverRatio', 0),
        // Season Totals - Defense
        safe(st, 'steals', 0),
        safe(st, 'spg', 0),
        safe(st, 'blocks', 0),
        safe(st, 'bpg', 0),
        // Season Totals - Shooting
        safe(st, 'fieldGoals.made', 0),
        safe(st, 'fieldGoals.attempted', 0),
        safe(st, 'fieldGoals.percentage', 0),
        safe(player, 'twoPointFieldGoals.made', 0),
        safe(player, 'twoPointFieldGoals.attempted', 0),
        safe(player, 'twoPointFieldGoals.pct', 0),
        safe(st, 'threePointFieldGoals.made', 0),
        safe(st, 'threePointFieldGoals.attempted', 0),
        safe(st, 'threePointFieldGoals.percentage', 0),
        safe(st, 'freeThrows.made', 0),
        safe(st, 'freeThrows.attempted', 0),
        safe(st, 'freeThrows.percentage', 0),
        // Advanced Stats (directly on player object)
        safe(player, 'offensiveRating', ""),
        safe(player, 'defensiveRating', ""),
        safe(player, 'netRating', ""),
        safe(player, 'PORPAG', ""),
        safe(player, 'usage', ""),
        safe(player, 'assistsTurnoverRatio', ""),
        safe(player, 'offensiveReboundPct', ""),
        safe(player, 'freeThrowRate', ""),
        safe(player, 'effectiveFieldGoalPct', ""),
        safe(player, 'trueShootingPct', ""),
        safe(player, 'winShares.offensive', ""),
        safe(player, 'winShares.defensive', ""),
        safe(player, 'winShares.total', ""),
        safe(player, 'winShares.totalPer40', ""),
        // Conference Rankings - Original 13
        cr && cr.pointsPerGame ? cr.pointsPerGame.rank + "/" + cr.pointsPerGame.totalPlayers : "",
        cr && cr.assistsPerGame ? cr.assistsPerGame.rank + "/" + cr.assistsPerGame.totalPlayers : "",
        cr && cr.reboundsPerGame ? cr.reboundsPerGame.rank + "/" + cr.reboundsPerGame.totalPlayers : "",
        cr && cr.stealsPerGame ? cr.stealsPerGame.rank + "/" + cr.stealsPerGame.totalPlayers : "",
        cr && cr.blocksPerGame ? cr.blocksPerGame.rank + "/" + cr.blocksPerGame.totalPlayers : "",
        cr && cr.fieldGoalPct ? cr.fieldGoalPct.rank + "/" + cr.fieldGoalPct.totalPlayers : "",
        cr && cr.threePointPct ? cr.threePointPct.rank + "/" + cr.threePointPct.totalPlayers : "",
        cr && cr.freeThrowPct ? cr.freeThrowPct.rank + "/" + cr.freeThrowPct.totalPlayers : "",
        cr && cr.effectiveFieldGoalPct ? cr.effectiveFieldGoalPct.rank + "/" + cr.effectiveFieldGoalPct.totalPlayers : "",
        cr && cr.assistToTurnoverRatio ? cr.assistToTurnoverRatio.rank + "/" + cr.assistToTurnoverRatio.totalPlayers : "",
        cr && cr.offensiveRating ? cr.offensiveRating.rank + "/" + cr.offensiveRating.totalPlayers : "",
        cr && cr.defensiveRating ? cr.defensiveRating.rank + "/" + cr.defensiveRating.totalPlayers : "",
        cr && cr.netRating ? cr.netRating.rank + "/" + cr.netRating.totalPlayers : "",
        // Conference Rankings - New 12 (volume/total stats)
        cr && cr.minutesPerGame ? cr.minutesPerGame.rank + "/" + cr.minutesPerGame.totalPlayers : "",
        cr && cr.fieldGoalsMade ? cr.fieldGoalsMade.rank + "/" + cr.fieldGoalsMade.totalPlayers : "",
        cr && cr.fieldGoalsAttempted ? cr.fieldGoalsAttempted.rank + "/" + cr.fieldGoalsAttempted.totalPlayers : "",
        cr && cr.threePointFieldGoalsMade ? cr.threePointFieldGoalsMade.rank + "/" + cr.threePointFieldGoalsMade.totalPlayers : "",
        cr && cr.threePointFieldGoalsAttempted ? cr.threePointFieldGoalsAttempted.rank + "/" + cr.threePointFieldGoalsAttempted.totalPlayers : "",
        cr && cr.freeThrowsMade ? cr.freeThrowsMade.rank + "/" + cr.freeThrowsMade.totalPlayers : "",
        cr && cr.freeThrowsAttempted ? cr.freeThrowsAttempted.rank + "/" + cr.freeThrowsAttempted.totalPlayers : "",
        cr && cr.offensiveRebounds ? cr.offensiveRebounds.rank + "/" + cr.offensiveRebounds.totalPlayers : "",
        cr && cr.defensiveRebounds ? cr.defensiveRebounds.rank + "/" + cr.defensiveRebounds.totalPlayers : "",
        cr && cr.totalRebounds ? cr.totalRebounds.rank + "/" + cr.totalRebounds.totalPlayers : "",
        cr && cr.totalAssists ? cr.totalAssists.rank + "/" + cr.totalAssists.totalPlayers : "",
        cr && cr.totalBlocks ? cr.totalBlocks.rank + "/" + cr.totalBlocks.totalPlayers : "",
        // Season Totals - Fouls/Ejections (moved to end)
        safe(st, 'fouls', 0),
        safe(st, 'foulOuts', 0),
        safe(st, 'ejections', 0),
        // Shooting Breakdown (from shootingStats) - moved to end to preserve column positions
        safe(player, 'shootingStats.dunks.attempted', 0),
        safe(player, 'shootingStats.dunks.made', 0),
        safe(player, 'shootingStats.dunks.pct', 0),
        safe(player, 'shootingStats.layups.attempted', 0),
        safe(player, 'shootingStats.layups.made', 0),
        safe(player, 'shootingStats.layups.pct', 0),
        safe(player, 'shootingStats.tipIns.attempted', 0),
        safe(player, 'shootingStats.tipIns.made', 0),
        safe(player, 'shootingStats.tipIns.pct', 0),
        safe(player, 'shootingStats.twoPointJumpers.attempted', 0),
        safe(player, 'shootingStats.twoPointJumpers.made', 0),
        safe(player, 'shootingStats.twoPointJumpers.pct', 0),
        safe(player, 'shootingStats.threePointJumpers.attempted', 0),
        safe(player, 'shootingStats.threePointJumpers.made', 0),
        safe(player, 'shootingStats.threePointJumpers.pct', 0)
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message], ["Line: " + e.lineNumber]];
  }
}

// ========================================
// CATEGORY 5: INDIVIDUAL PLAYERS - ALL DATA (NUMERIC SORT)
// ========================================

function GET_PLAYERS_FULL_NUMERIC(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var table = [[
      // Basic Info
      "Name", "Jersey", "Position", "Height", "Class", "Freshman", "Hometown", "High School",
      // Season Totals - Playing Time
      "Games", "GS", "Min", "MPG",
      // Season Totals - Scoring
      "Pts", "PPG",
      // Season Totals - Rebounds
      "OReb", "DReb", "TReb", "RPG",
      // Season Totals - Playmaking
      "Ast", "APG", "TO", "A/TO",
      // Season Totals - Defense
      "Stl", "SPG", "Blk", "BPG",
      // Season Totals - Shooting
      "FGM", "FGA", "FG%", "2PM", "2PA", "2P%",
      "3PM", "3PA", "3P%", "FTM", "FTA", "FT%",
      // Advanced Stats
      "ORtg", "DRtg", "NetRtg", "PORPAG", "Usage%",
      "AST/TO", "OReb%", "FTR", "eFG%", "TS%",
      "WS Off", "WS Def", "WS Total", "WS/40",
      // Conference Rankings - Per Game Stats (original 13)
      "PPG Rank", "APG Rank", "RPG Rank", "SPG Rank", "BPG Rank",
      "FG% Rank", "3P% Rank", "FT% Rank", "eFG% Rank",
      "A/TO Rank", "ORtg Rank", "DRtg Rank", "NetRtg Rank",
      // Conference Rankings - New Total/Volume Stats (12 new)
      "MPG Rank", "FGM Rank", "FGA Rank", "3PM Rank", "3PA Rank",
      "FTM Rank", "FTA Rank", "OReb Rank", "DReb Rank", "TReb Rank",
      "Ast Rank", "Blk Rank",
      // Season Totals - Fouls/Ejections (moved to end)
      "Fouls", "Foul Outs", "Ejections",
      // Shooting Breakdown (moved to end to preserve column positions)
      "Dunks Att", "Dunks Made", "Dunks %",
      "Layups Att", "Layups Made", "Layups %",
      "Tip-Ins Att", "Tip-Ins Made", "Tip-Ins %",
      "2PT Jumpers Att", "2PT Jumpers Made", "2PT Jumpers %",
      "3PT Jumpers Att", "3PT Jumpers Made", "3PT Jumpers %"
    ]];
    
    // Sort players by jersey number ascending
    var playersCopy = data.players.slice(); // Make a copy to sort
    
    playersCopy.sort(function(a, b) {
      var jerseyA = parseInt(a.jerseyNumber);
      if (isNaN(jerseyA)) {
        jerseyA = 9999; // Put non-numeric at end
      }
      var jerseyB = parseInt(b.jerseyNumber);
      if (isNaN(jerseyB)) {
        jerseyB = 9999; // Put non-numeric at end
      }
      return jerseyA - jerseyB; // Ascending
    });
    
    var sortedPlayers = playersCopy;
    
    // Helper function to safely get nested values
    var safe = function(obj, path, defaultVal) {
      if (!obj) return defaultVal || "";
      var keys = path.split('.');
      var val = obj;
      for (var i = 0; i < keys.length; i++) {
        if (val === null || val === undefined) return defaultVal || "";
        val = val[keys[i]];
      }
      return val !== null && val !== undefined ? val : (defaultVal || "");
    };
    
    sortedPlayers.forEach(function(player) {
      var st = player.seasonTotals;
      var cr = player.conferenceRankings;
      
      table.push([
        // Basic Info
        player.name || "",
        player.jerseyNumber || "",
        player.position || "",
        player.height || "",
        player.class || "",
        player.isFreshman || false,
        player.hometown || "",
        player.highSchool || "",
        // Season Totals - Playing Time
        safe(st, 'games', 0),
        safe(st, 'gamesStarted', 0),
        safe(st, 'minutes', 0),
        safe(st, 'mpg', 0),
        // Season Totals - Scoring
        safe(st, 'points', 0),
        safe(st, 'ppg', 0),
        // Season Totals - Rebounds
        safe(st, 'rebounds.offensive', 0),
        safe(st, 'rebounds.defensive', 0),
        safe(st, 'rebounds.total', 0),
        safe(st, 'rpg', 0),
        // Season Totals - Playmaking
        safe(st, 'assists', 0),
        safe(st, 'apg', 0),
        safe(st, 'turnovers', 0),
        safe(st, 'assistToTurnoverRatio', 0),
        // Season Totals - Defense
        safe(st, 'steals', 0),
        safe(st, 'spg', 0),
        safe(st, 'blocks', 0),
        safe(st, 'bpg', 0),
        // Season Totals - Shooting
        safe(st, 'fieldGoals.made', 0),
        safe(st, 'fieldGoals.attempted', 0),
        safe(st, 'fieldGoals.percentage', 0),
        safe(player, 'twoPointFieldGoals.made', 0),
        safe(player, 'twoPointFieldGoals.attempted', 0),
        safe(player, 'twoPointFieldGoals.pct', 0),
        safe(st, 'threePointFieldGoals.made', 0),
        safe(st, 'threePointFieldGoals.attempted', 0),
        safe(st, 'threePointFieldGoals.percentage', 0),
        safe(st, 'freeThrows.made', 0),
        safe(st, 'freeThrows.attempted', 0),
        safe(st, 'freeThrows.percentage', 0),
        // Advanced Stats (directly on player object)
        safe(player, 'offensiveRating', ""),
        safe(player, 'defensiveRating', ""),
        safe(player, 'netRating', ""),
        safe(player, 'PORPAG', ""),
        safe(player, 'usage', ""),
        safe(player, 'assistsTurnoverRatio', ""),
        safe(player, 'offensiveReboundPct', ""),
        safe(player, 'freeThrowRate', ""),
        safe(player, 'effectiveFieldGoalPct', ""),
        safe(player, 'trueShootingPct', ""),
        safe(player, 'winShares.offensive', ""),
        safe(player, 'winShares.defensive', ""),
        safe(player, 'winShares.total', ""),
        safe(player, 'winShares.totalPer40', ""),
        // Conference Rankings - Original 13
        cr && cr.pointsPerGame ? cr.pointsPerGame.rank + "/" + cr.pointsPerGame.totalPlayers : "",
        cr && cr.assistsPerGame ? cr.assistsPerGame.rank + "/" + cr.assistsPerGame.totalPlayers : "",
        cr && cr.reboundsPerGame ? cr.reboundsPerGame.rank + "/" + cr.reboundsPerGame.totalPlayers : "",
        cr && cr.stealsPerGame ? cr.stealsPerGame.rank + "/" + cr.stealsPerGame.totalPlayers : "",
        cr && cr.blocksPerGame ? cr.blocksPerGame.rank + "/" + cr.blocksPerGame.totalPlayers : "",
        cr && cr.fieldGoalPct ? cr.fieldGoalPct.rank + "/" + cr.fieldGoalPct.totalPlayers : "",
        cr && cr.threePointPct ? cr.threePointPct.rank + "/" + cr.threePointPct.totalPlayers : "",
        cr && cr.freeThrowPct ? cr.freeThrowPct.rank + "/" + cr.freeThrowPct.totalPlayers : "",
        cr && cr.effectiveFieldGoalPct ? cr.effectiveFieldGoalPct.rank + "/" + cr.effectiveFieldGoalPct.totalPlayers : "",
        cr && cr.assistToTurnoverRatio ? cr.assistToTurnoverRatio.rank + "/" + cr.assistToTurnoverRatio.totalPlayers : "",
        cr && cr.offensiveRating ? cr.offensiveRating.rank + "/" + cr.offensiveRating.totalPlayers : "",
        cr && cr.defensiveRating ? cr.defensiveRating.rank + "/" + cr.defensiveRating.totalPlayers : "",
        cr && cr.netRating ? cr.netRating.rank + "/" + cr.netRating.totalPlayers : "",
        // Conference Rankings - New 12 (volume/total stats)
        cr && cr.minutesPerGame ? cr.minutesPerGame.rank + "/" + cr.minutesPerGame.totalPlayers : "",
        cr && cr.fieldGoalsMade ? cr.fieldGoalsMade.rank + "/" + cr.fieldGoalsMade.totalPlayers : "",
        cr && cr.fieldGoalsAttempted ? cr.fieldGoalsAttempted.rank + "/" + cr.fieldGoalsAttempted.totalPlayers : "",
        cr && cr.threePointFieldGoalsMade ? cr.threePointFieldGoalsMade.rank + "/" + cr.threePointFieldGoalsMade.totalPlayers : "",
        cr && cr.threePointFieldGoalsAttempted ? cr.threePointFieldGoalsAttempted.rank + "/" + cr.threePointFieldGoalsAttempted.totalPlayers : "",
        cr && cr.freeThrowsMade ? cr.freeThrowsMade.rank + "/" + cr.freeThrowsMade.totalPlayers : "",
        cr && cr.freeThrowsAttempted ? cr.freeThrowsAttempted.rank + "/" + cr.freeThrowsAttempted.totalPlayers : "",
        cr && cr.offensiveRebounds ? cr.offensiveRebounds.rank + "/" + cr.offensiveRebounds.totalPlayers : "",
        cr && cr.defensiveRebounds ? cr.defensiveRebounds.rank + "/" + cr.defensiveRebounds.totalPlayers : "",
        cr && cr.totalRebounds ? cr.totalRebounds.rank + "/" + cr.totalRebounds.totalPlayers : "",
        cr && cr.totalAssists ? cr.totalAssists.rank + "/" + cr.totalAssists.totalPlayers : "",
        cr && cr.totalBlocks ? cr.totalBlocks.rank + "/" + cr.totalBlocks.totalPlayers : "",
        // Season Totals - Fouls/Ejections (moved to end)
        safe(st, 'fouls', 0),
        safe(st, 'foulOuts', 0),
        safe(st, 'ejections', 0),
        // Shooting Breakdown (from shootingStats) - moved to end to preserve column positions
        safe(player, 'shootingStats.dunks.attempted', 0),
        safe(player, 'shootingStats.dunks.made', 0),
        safe(player, 'shootingStats.dunks.pct', 0),
        safe(player, 'shootingStats.layups.attempted', 0),
        safe(player, 'shootingStats.layups.made', 0),
        safe(player, 'shootingStats.layups.pct', 0),
        safe(player, 'shootingStats.tipIns.attempted', 0),
        safe(player, 'shootingStats.tipIns.made', 0),
        safe(player, 'shootingStats.tipIns.pct', 0),
        safe(player, 'shootingStats.twoPointJumpers.attempted', 0),
        safe(player, 'shootingStats.twoPointJumpers.made', 0),
        safe(player, 'shootingStats.twoPointJumpers.pct', 0),
        safe(player, 'shootingStats.threePointJumpers.attempted', 0),
        safe(player, 'shootingStats.threePointJumpers.made', 0),
        safe(player, 'shootingStats.threePointJumpers.pct', 0)
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message], ["Line: " + e.lineNumber]];
  }
}

// ========================================
// PLAYER GAME-BY-GAME LOG
// ========================================

function GET_PLAYER_GAMES(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return [["Player not found"]];
    
    var table = [[
      "Date", "Opponent", "Home/Away", "Conf", "Starter",
      "Min", "Pts", "OReb", "DReb", "TReb", "Ast", "TO", "Stl", "Blk",
      "FGM-FGA", "3PM-3PA", "FTM-FTA",
      "Fouls", "Foul Outs", "Ejections"
    ]];
    
    player.gameByGame.forEach(function(game) {
      var fouls = game.fouls || 0;
      var foulOut = fouls >= 5 ? "Yes" : "No";
      table.push([
        game.date,
        game.opponent,
        game.isHome ? "Home" : "Away",
        game.conferenceGame ? "Conf" : "Non-Conf",
        game.starter ? "Start" : "Bench",
        game.minutes,
        game.points,
        game.rebounds.offensive,
        game.rebounds.defensive,
        game.rebounds.offensive + game.rebounds.defensive,
        game.assists,
        game.turnovers,
        game.steals,
        game.blocks,
        game.fieldGoals.made + "-" + game.fieldGoals.attempted,
        game.threePointFieldGoals.made + "-" + game.threePointFieldGoals.attempted,
        game.freeThrows.made + "-" + game.freeThrows.attempted,
        fouls,
        foulOut,
        game.ejected ? "Yes" : "No"
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// Get player's most recent game
function GET_PLAYER_LAST_GAME(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return [["Player not found"]];
    if (!player.gameByGame || player.gameByGame.length === 0) return [["No games found"]];
    
    var table = [[
      "Date", "Opponent", "Home/Away", "Conf", "Starter",
      "Min", "Pts", "OReb", "DReb", "TReb", "Ast", "TO", "Stl", "Blk",
      "Fouls", "Ejected",
      "FGM-FGA", "3PM-3PA", "FTM-FTA"
    ]];
    
    // Get last game
    var game = player.gameByGame[player.gameByGame.length - 1];
    
    table.push([
      game.date,
      game.opponent,
      game.isHome ? "Home" : "Away",
      game.conferenceGame ? "Conf" : "Non-Conf",
      game.starter ? "Start" : "Bench",
      game.minutes,
      game.points,
      game.rebounds.offensive,
      game.rebounds.defensive,
      game.rebounds.offensive + game.rebounds.defensive,
      game.assists,
      game.turnovers,
      game.steals,
      game.blocks,
      game.fouls || 0,
      game.ejected ? "Yes" : "No",
      game.fieldGoals.made + "-" + game.fieldGoals.attempted,
      game.threePointFieldGoals.made + "-" + game.threePointFieldGoals.attempted,
      game.freeThrows.made + "-" + game.freeThrows.attempted
    ]);
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// Get player's last game as compact summary string
// Shows stats from team's most recent game (even if player didn't play)
function GET_PLAYER_LAST_GAME_SUMMARY(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return "Player not found";
    
    // Get team's most recent game
    if (!data.teamGameStats || data.teamGameStats.length === 0) {
      return "No team games found";
    }
    
    // Sort team games by date (most recent first)
    var sortedTeamGames = data.teamGameStats.slice().sort(function(a, b) {
      return new Date(b.startDate) - new Date(a.startDate);
    });
    
    var mostRecentTeamGame = sortedTeamGames[0];
    
    // Find player's stats for this specific game
    var playerGame = null;
    if (player.gameByGame && player.gameByGame.length > 0) {
      // Match by date and opponent
      var teamGameDate = new Date(mostRecentTeamGame.startDate).toISOString().split('T')[0]; // Get YYYY-MM-DD
      
      playerGame = player.gameByGame.find(function(pg) {
        var playerGameDate = new Date(pg.date).toISOString().split('T')[0];
        return playerGameDate === teamGameDate && 
               pg.opponent === mostRecentTeamGame.opponent;
      });
    }
    
    // If player didn't play in the most recent game, return "-"
    if (!playerGame) {
      return "-";
    }
    
    // Player did play - format stats
    var totalReb = playerGame.rebounds.offensive + playerGame.rebounds.defensive;
    
    // Format: {points}p, {rebounds}r, {assists}a, {turnovers}to, {steals}s, {blocks}b, {fgm}-{fga}fg, {ftm}-{fta}ft, ({3pmade}-{3pa})3p, [{minutes}]
    var summary = playerGame.points + "p, " +
                  totalReb + "r, " +
                  playerGame.assists + "a, " +
                  playerGame.turnovers + "to, " +
                  playerGame.steals + "s, " +
                  playerGame.blocks + "b, " +
                  playerGame.fieldGoals.made + "-" + playerGame.fieldGoals.attempted + "fg, " +
                  playerGame.freeThrows.made + "-" + playerGame.freeThrows.attempted + "ft, " +
                  "(" + playerGame.threePointFieldGoals.made + "-" + playerGame.threePointFieldGoals.attempted + ")3p, " +
                  "[" + playerGame.minutes + "]";
    
    return summary;
  } catch (e) {
    return "Error: " + e.message;
  }
}


// Get player's previous season summary (most recent previous season)
function GET_PLAYER_PREVIOUS_SEASON_SUMMARY(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return "Player not found";
    if (!player.previousSeasons || player.previousSeasons.length === 0) return "-";
    
    // Get most recent previous season by finding the one with the highest season year
    // Sort by season year descending and take the first one
    var sortedSeasons = player.previousSeasons.slice().sort(function(a, b) {
      return (b.season || 0) - (a.season || 0);
    });
    var prevSeason = sortedSeasons[0];
    var stats = prevSeason.seasonStats;
    
    // Format school name to uppercase
    var school = prevSeason.team.toUpperCase();
    
    // Get values with safe defaults
    var games = prevSeason.games || 0;
    var ppg = stats.pointsPerGame || 0;  // Changed from stats.ppg
    var rpg = stats.reboundsPerGame || 0;  // Changed from stats.rpg
    var threePct = stats.threePointFieldGoals ? stats.threePointFieldGoals.pct || 0 : 0;  // Changed from .percentage
    var ftPct = stats.freeThrows ? stats.freeThrows.pct || 0 : 0;  // Changed from .percentage
    
    // Format: {School/team} {games}g, {season_avg_points}p, {season_avg_rebounds}r, {3p_percentage}% 3p, {ft_percentage}% FT
    var summary = school + " " +
                  games + "g, " +
                  ppg + "p, " +
                  rpg + "r, " +
                  threePct + "% 3P, " +
                  ftPct + "% FT";
    
    return summary;
  } catch (e) {
    return "Error: " + e.message;
  }
}


// Get player's last N games
function GET_PLAYER_LAST_N_GAMES(url, playerName, n) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return [["Player not found"]];
    if (!player.gameByGame || player.gameByGame.length === 0) return [["No games found"]];
    
    var table = [[
      "Date", "Opponent", "Home/Away", "Conf", "Starter",
      "Min", "Pts", "OReb", "DReb", "TReb", "Ast", "TO", "Stl", "Blk",
      "Fouls", "Ejected",
      "FGM-FGA", "3PM-3PA", "FTM-FTA"
    ]];
    
    // Get last N games (or all games if N is larger than total games)
    var gamesToShow = Math.min(n, player.gameByGame.length);
    var startIndex = player.gameByGame.length - gamesToShow;
    
    for (var i = startIndex; i < player.gameByGame.length; i++) {
      var game = player.gameByGame[i];
      table.push([
        game.date,
        game.opponent,
        game.isHome ? "Home" : "Away",
        game.conferenceGame ? "Conf" : "Non-Conf",
        game.starter ? "Start" : "Bench",
        game.minutes,
        game.points,
        game.rebounds.offensive,
        game.rebounds.defensive,
        game.rebounds.offensive + game.rebounds.defensive,
        game.assists,
        game.turnovers,
        game.steals,
        game.blocks,
        game.fouls || 0,
        game.ejected ? "Yes" : "No",
        game.fieldGoals.made + "-" + game.fieldGoals.attempted,
        game.threePointFieldGoals.made + "-" + game.threePointFieldGoals.attempted,
        game.freeThrows.made + "-" + game.freeThrows.attempted
      ]);
    }
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

// Generic data getter
function GET_DATA(url, path) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    if (!path) return JSON.stringify(data);
    
    var keys = path.split('.');
    var value = data;
    for (var i = 0; i < keys.length; i++) {
      value = value[keys[i]];
    }
    return value;
  } catch (e) {
    return "Error: " + e.message;
  }
}

// Get specific player stat
function GET_PLAYER_STAT(url, playerName, statPath) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return "Player not found";
    
    var keys = statPath.split('.');
    var value = player;
    for (var i = 0; i < keys.length; i++) {
      value = value[keys[i]];
    }
    return value;
  } catch (e) {
    return "Error: " + e.message;
  }
}

// Get all player names
function GET_PLAYERS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    return data.players.map(function(player) {
      return [player.name];
    });
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// PLAYER CAREER HISTORY (Previous Seasons)
// ========================================

function GET_PLAYER_CAREER(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return [["Player not found"]];
    if (!player.previousSeasons || player.previousSeasons.length === 0) {
      return [["No previous seasons data available"]];
    }
    
    var table = [[
      "Season", "Team", "Conference",
      "Games", "GS", "Min", "MPG",
      "Pts", "PPG", "Reb", "RPG", "Ast", "APG",
      "FGM-FGA", "FG%", "3PM-3PA", "3P%", "FTM-FTA", "FT%"
    ]];
    
    player.previousSeasons.forEach(function(season) {
      var stats = season.seasonStats;
      
      table.push([
        season.season,  // Just use it directly - it's already formatted correctly
        season.team,
        season.conference,
        season.games,
        season.gamesStarted,
        stats.minutes || 0,
        stats.minutesPerGame || 0,
        stats.points || 0,
        stats.pointsPerGame || 0,
        stats.rebounds ? stats.rebounds.total : 0,
        stats.reboundsPerGame || 0,
        stats.assists || 0,
        stats.assistsPerGame || 0,
        (stats.fieldGoals ? stats.fieldGoals.made : 0) + "-" + (stats.fieldGoals ? stats.fieldGoals.attempted : 0),
        stats.fieldGoals ? stats.fieldGoals.pct : 0,
        (stats.threePointFieldGoals ? stats.threePointFieldGoals.made : 0) + "-" + (stats.threePointFieldGoals ? stats.threePointFieldGoals.attempted : 0),
        stats.threePointFieldGoals ? stats.threePointFieldGoals.pct : 0,
        (stats.freeThrows ? stats.freeThrows.made : 0) + "-" + (stats.freeThrows ? stats.freeThrows.attempted : 0),
        stats.freeThrows ? stats.freeThrows.pct : 0
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// Get complete career overview (current + previous seasons)
function GET_PLAYER_FULL_CAREER(url, playerName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var player = data.players.find(function(p) {
      return p.name.toLowerCase() === playerName.toLowerCase();
    });
    
    if (!player) return [["Player not found"]];
    
    var table = [[
      "Season", "Team", "Conference", "Type",
      "Games", "GS", "Min", "MPG",
      "Pts", "PPG", "Reb", "RPG", "Ast", "APG",
      "FGM-FGA", "FG%", "3PM-3PA", "3P%", "FTM-FTA", "FT%"
    ]];
    
    // Add previous seasons first
    if (player.previousSeasons && player.previousSeasons.length > 0) {
      player.previousSeasons.forEach(function(season) {
        var stats = season.seasonStats;
        
        // Format season properly - it's a number in the JSON
        var seasonYear = season.season;
        var nextYear = seasonYear + 1;
        var formattedSeason = seasonYear + "-" + nextYear.toString().slice(-2);
        
        table.push([
          formattedSeason,
          season.team,
          season.conference,
          "Previous",
          season.games,
          season.gamesStarted,
          stats.minutes || 0,
          stats.minutesPerGame || 0,
          stats.points || 0,
          stats.pointsPerGame || 0,
          stats.rebounds ? stats.rebounds.total : 0,
          stats.reboundsPerGame || 0,
          stats.assists || 0,
          stats.assistsPerGame || 0,
          (stats.fieldGoals ? stats.fieldGoals.made : 0) + "-" + (stats.fieldGoals ? stats.fieldGoals.attempted : 0),
          stats.fieldGoals ? stats.fieldGoals.pct : 0,
          (stats.threePointFieldGoals ? stats.threePointFieldGoals.made : 0) + "-" + (stats.threePointFieldGoals ? stats.threePointFieldGoals.attempted : 0),
          stats.threePointFieldGoals ? stats.threePointFieldGoals.pct : 0,
          (stats.freeThrows ? stats.freeThrows.made : 0) + "-" + (stats.freeThrows ? stats.freeThrows.attempted : 0),
          stats.freeThrows ? stats.freeThrows.pct : 0
        ]);
      });
    }
    
    // Add current season - data.season is already formatted as "2024-25"
    var st = player.seasonTotals;
    table.push([
      data.season,  // Already formatted correctly
      data.team,
      data.teamSeasonStats ? data.teamSeasonStats.conference : "Not sure",
      "Current",
      st.games,
      st.gamesStarted,
      st.minutes,
      st.mpg,
      st.points,
      st.ppg,
      st.rebounds.total,
      st.rpg,
      st.assists,
      st.apg,
      st.fieldGoals.made + "-" + st.fieldGoals.attempted,
      st.fieldGoals.percentage,
      st.threePointFieldGoals.made + "-" + st.threePointFieldGoals.attempted,
      st.threePointFieldGoals.percentage,
      st.freeThrows.made + "-" + st.freeThrows.attempted,
      st.freeThrows.percentage
    ]);
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// ALL PLAYERS CAREERS (ONE TABLE)
// ========================================

function GET_ALL_PLAYERS_CAREERS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var table = [[
      "Player", "Season", "Team", "Conference", "Type",
      "Games", "GS", "Min", "MPG",
      "Pts", "PPG", "Reb", "RPG", "Ast", "APG",
      "FGM-FGA", "FG%", "3PM-3PA", "3P%", "FTM-FTA", "FT%"
    ]];
    
    // Loop through each player
    data.players.forEach(function(player) {
      var playerName = player.name;
      
      // Add previous seasons first (if any)
      if (player.previousSeasons && player.previousSeasons.length > 0) {
        player.previousSeasons.forEach(function(season) {
          var stats = season.seasonStats;
          
          // Format season properly - it's a number in the JSON
          var seasonYear = season.season;
          // var nextYear = seasonYear + 1;
          var formattedSeason = seasonYear;
          
          table.push([
            playerName,
            formattedSeason,
            season.team,
            season.conference,
            "Previous",
            season.games,
            season.gamesStarted,
            stats.minutes || 0,
            stats.minutesPerGame || 0,
            stats.points || 0,
            stats.pointsPerGame || 0,
            stats.rebounds ? stats.rebounds.total : 0,
            stats.reboundsPerGame || 0,
            stats.assists || 0,
            stats.assistsPerGame || 0,
            (stats.fieldGoals ? stats.fieldGoals.made : 0) + "-" + (stats.fieldGoals ? stats.fieldGoals.attempted : 0),
            stats.fieldGoals ? stats.fieldGoals.pct : 0,
            (stats.threePointFieldGoals ? stats.threePointFieldGoals.made : 0) + "-" + (stats.threePointFieldGoals ? stats.threePointFieldGoals.attempted : 0),
            stats.threePointFieldGoals ? stats.threePointFieldGoals.pct : 0,
            (stats.freeThrows ? stats.freeThrows.made : 0) + "-" + (stats.freeThrows ? stats.freeThrows.attempted : 0),
            stats.freeThrows ? stats.freeThrows.pct : 0
          ]);
        });
      }
      
      // Add current season - data.season is already formatted as "2024-25"
      var st = player.seasonTotals;
      table.push([
        playerName,
        data.season,  // Already formatted correctly
        data.team,
        data.teamSeasonStats ? data.teamSeasonStats.conference : "Not Sure",
        "Current",
        st.games,
        st.gamesStarted,
        st.minutes,
        st.mpg,
        st.points,
        st.ppg,
        st.rebounds.total,
        st.rpg,
        st.assists,
        st.apg,
        st.fieldGoals.made + "-" + st.fieldGoals.attempted,
        st.fieldGoals.percentage,
        st.threePointFieldGoals.made + "-" + st.threePointFieldGoals.attempted,
        st.threePointFieldGoals.percentage,
        st.freeThrows.made + "-" + st.freeThrows.attempted,
        st.freeThrows.percentage
      ]);
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}


// ========================================
// DEBUG FUNCTION
// ========================================

function DEBUG_JSON(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    return [
      ["=== JSON STRUCTURE DEBUG ==="],
      [""],
      ["Top-level keys:"],
      ["team: " + (data.team ? "✓" : "✗")],
      ["season: " + (data.season ? "✓" : "✗")],
      ["seasonType: " + (data.seasonType ? "✓" : "✗")],
      ["players: " + (data.players ? "✓ (length: " + data.players.length + ")" : "✗")],
      ["teamGameStats: " + (data.teamGameStats ? "✓ (length: " + data.teamGameStats.length + ")" : "✗")],
      ["teamSeasonStats: " + (data.teamSeasonStats ? "✓" : "✗")],
      ["conferenceRankings: " + (data.conferenceRankings ? "✓" : "✗")],
      ["conferenceRankings.rankings: " + (data.conferenceRankings && data.conferenceRankings.rankings ? "✓" : "✗")],
      ["d1Rankings: " + (data.d1Rankings ? "✓" : "✗")],
      ["d1Rankings.rankings: " + (data.d1Rankings && data.d1Rankings.rankings ? "✓" : "✗")],
      ["metadata: " + (data.metadata ? "✓" : "✗")],
      [""],
      ["Raw data preview (first 500 chars):"],
      [response.getContentText().substring(0, 500)]
    ];
  } catch (e) {
    return [["Error: " + e.message], ["Stack: " + e.stack]];
  }
}

// ========================================
// TEST FUNCTION
// ========================================

/**
 * Test function to verify library is working correctly
 * Returns a simple table with test values
 * @return {Array<Array>} Test table with sample data
 */
function TEST_FUNCTION() {
  return [
    ["=== TEST FUNCTION ==="],
    ["Status", "✅ Working"],
    ["Library", "CBB Data Functions Library"],
    ["Version", "Development Mode"],
    ["Timestamp", new Date().toLocaleString()],
    [""],
    ["Test Values"],
    ["Number", 42],
    ["Text", "Hello from Google Apps Script!"],
    ["Boolean", true],
    ["Array", "[1, 2, 3]"],
    [""],
    ["If you see this, the library is working correctly!"]
  ];
}


// ========================================
// CATEGORY: KENPOM DATA
// ========================================

// Helper function to remove % from percentage values
function removePercent(value) {
  if (typeof value === 'string' && value.endsWith('%')) {
    return value.slice(0, -1); // Remove last character (%)
  }
  return value;
}

// Get full KenPom report table (includes Bart Torvik data appended)
function GET_KENPOM_REPORT_TABLE(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    var table = [];

    // KenPom Report Table - always show headers
    table.push(
      ["=== KENPOM REPORT TABLE ==="],
      [""],
      ["Category", "Offense", "Offense Rank", "Defense", "Defense Rank", "D-I Avg"]
    );

    // Check if KenPom data exists and process it
    var reportTable = (data.kenpom && (data.kenpom.reportTable || data.kenpom.report_table_structured)) || null;

    if (reportTable) {
      // Process each category
      for (var category in reportTable) {
        var categoryData = reportTable[category];

        // Handle Adj. Tempo specially (has combined instead of offense/defense)
        if (category === "Adj. Tempo") {
          var combined = removePercent(categoryData.combined || "");
          var ranking = categoryData.ranking !== null ? categoryData.ranking : "";
          var d1Avg = removePercent(categoryData.d1_avg || "");

          table.push([
            category,
            combined,
            ranking,
            "", // No defense for tempo
            "", // No defense rank
            d1Avg
          ]);
        } else if (categoryData.value !== undefined) {
          // Handle categories with "value" field (Bench Minutes, D-1 Experience, etc.)
          var value = removePercent(categoryData.value || "");
          var ranking = categoryData.ranking !== null ? categoryData.ranking : "";
          var d1Avg = removePercent(categoryData.d1_avg || "");

          table.push([
            category,
            value,
            ranking,
            "", // No defense for value-based categories
            "", // No defense rank
            d1Avg
          ]);
        } else {
          // Standard categories with offense/defense
          var offense = removePercent(categoryData.offense || "");
          var offenseRank = categoryData.offense_ranking !== null ? categoryData.offense_ranking : "";
          var defense = removePercent(categoryData.defense || "");
          var defenseRank = categoryData.defense_ranking !== null ? categoryData.defense_ranking : "";
          var d1Avg = removePercent(categoryData.d1_avg || "");

          // Skip empty categories (section headers)
          if (!offense && !defense && !d1Avg) {
            continue;
          }

          table.push([
            category,
            offense,
            offenseRank,
            defense,
            defenseRank,
            d1Avg
          ]);
        }
      }
    } else {
      // No KenPom data - show "N/A" row
      table.push(["KenPom data not available", "N/A", "N/A", "N/A", "N/A", "N/A"]);
    }
    
    // Bart Torvik data section - always show all subsections
    table.push([""]);
    table.push(["=== BART TORVIK TEAMSHEET DATA ==="]);
    table.push([""]);

    var bt = data.barttorvik || {};

    // Basic info - always include
    table.push(["Rank", bt.rank || "N/A"]);
    table.push(["Seed", bt.seed || "N/A"]);
    table.push([""]);

    // Resume metrics - always include section
    table.push(["=== RESUME METRICS ==="]);
    table.push(["NET", (bt.resume && bt.resume.net) || "N/A"]);
    table.push(["KPI", (bt.resume && bt.resume.kpi) || "N/A"]);
    table.push(["SOR", (bt.resume && bt.resume.sor) || "N/A"]);
    table.push(["WAB", (bt.resume && bt.resume.wab) || "N/A"]);
    table.push(["Avg", (bt.resume && bt.resume.avg) || "N/A"]);
    table.push([""]);

    // Quality metrics - always include section
    table.push(["=== QUALITY METRICS ==="]);
    table.push(["BPI", (bt.quality && bt.quality.bpi) || "N/A"]);
    table.push(["KenPom", (bt.quality && bt.quality.kenpom) || "N/A"]);
    table.push(["TRK", (bt.quality && bt.quality.trk) || "N/A"]);
    table.push(["Avg", (bt.quality && bt.quality.avg) || "N/A"]);
    table.push([""]);

    // Quadrant records - always include section with all quadrants
    table.push(["=== QUADRANT RECORDS ==="]);
    var q1a = (bt.quadrants && bt.quadrants.q1a) || {};
    var q1 = (bt.quadrants && bt.quadrants.q1) || {};
    var q2 = (bt.quadrants && bt.quadrants.q2) || {};
    var q1_and_q2 = (bt.quadrants && bt.quadrants.q1_and_q2) || {};
    var q3 = (bt.quadrants && bt.quadrants.q3) || {};
    var q4 = (bt.quadrants && bt.quadrants.q4) || {};

    table.push(["Q1A", q1a.record || "N/A", "(" + (q1a.wins || 0) + "-" + (q1a.losses || 0) + ")"]);
    table.push(["Q1", q1.record || "N/A", "(" + (q1.wins || 0) + "-" + (q1.losses || 0) + ")"]);
    table.push(["Q2", q2.record || "N/A", "(" + (q2.wins || 0) + "-" + (q2.losses || 0) + ")"]);
    table.push(["Q1&2", q1_and_q2.record || "N/A", "(" + (q1_and_q2.wins || 0) + "-" + (q1_and_q2.losses || 0) + ")"]);
    table.push(["Q3", q3.record || "N/A", "(" + (q3.wins || 0) + "-" + (q3.losses || 0) + ")"]);
    table.push(["Q4", q4.record || "N/A", "(" + (q4.wins || 0) + "-" + (q4.losses || 0) + ")"]);
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// Get specific KenPom category
function GET_KENPOM_CATEGORY(url, categoryName) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    if (!data.kenpom) {
      return [["KenPom data not available"], ["Regenerate the data file to include KenPom API data"]];
    }
    
    // Check for reportTable (new API structure) or report_table_structured (old scraping structure)
    var reportTable = data.kenpom.reportTable || data.kenpom.report_table_structured;
    
    if (!reportTable) {
      return [["KenPom data not available"], ["reportTable missing from kenpom object"]];
    }
    var categoryData = reportTable[categoryName];
    
    if (!categoryData) {
      return [["Category not found: " + categoryName]];
    }
    
    var table = [
      ["=== " + categoryName.toUpperCase() + " ==="],
      [""]
    ];
    
    // Handle Adj. Tempo specially
    if (categoryName === "Adj. Tempo") {
      table.push(["Combined", removePercent(categoryData.combined || "N/A")]);
      table.push(["Ranking", categoryData.ranking !== null ? categoryData.ranking : "N/A"]);
      table.push(["D-I Avg", removePercent(categoryData.d1_avg || "N/A")]);
    } else if (categoryData.value !== undefined) {
      // Handle categories with "value" field (Bench Minutes, D-1 Experience, etc.)
      table.push(["Value", removePercent(categoryData.value || "N/A")]);
      table.push(["Ranking", categoryData.ranking !== null ? categoryData.ranking : "N/A"]);
      table.push(["D-I Avg", removePercent(categoryData.d1_avg || "N/A")]);
    } else {
      table.push(["Offense", removePercent(categoryData.offense || "N/A")]);
      table.push(["Offense Ranking", categoryData.offense_ranking !== null ? categoryData.offense_ranking : "N/A"]);
      table.push(["Defense", removePercent(categoryData.defense || "N/A")]);
      table.push(["Defense Ranking", categoryData.defense_ranking !== null ? categoryData.defense_ranking : "N/A"]);
      table.push(["D-I Avg", removePercent(categoryData.d1_avg || "N/A")]);
    }
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// Get KenPom Adj. Efficiency (most commonly requested)
function GET_KENPOM_ADJ_EFFICIENCY(url) {
  return GET_KENPOM_CATEGORY(url, "Adj. Efficiency");
}

// Get KenPom Adj. Tempo
function GET_KENPOM_ADJ_TEMPO(url) {
  return GET_KENPOM_CATEGORY(url, "Adj. Tempo");
}

// Get KenPom Four Factors
function GET_KENPOM_FOUR_FACTORS(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    if (!data.kenpom) {
      return [["KenPom data not available"], ["Regenerate the data file to include KenPom API data"]];
    }
    
    // Check for reportTable (new API structure) or report_table_structured (old scraping structure)
    var reportTable = data.kenpom.reportTable || data.kenpom.report_table_structured;
    
    if (!reportTable) {
      return [["KenPom data not available"], ["reportTable missing from kenpom object"]];
    }
    var fourFactors = [
      "Effective FG%",
      "Turnover %",
      "Off. Reb. %",
      "FTA/FGA"
    ];
    
    var table = [
      ["=== FOUR FACTORS ==="],
      [""],
      ["Category", "Offense", "Offense Rank", "Defense", "Defense Rank", "D-I Avg"]
    ];
    
    fourFactors.forEach(function(category) {
      var categoryData = reportTable[category];
      if (categoryData) {
        table.push([
          category,
          removePercent(categoryData.offense || ""),
          categoryData.offense_ranking !== null ? categoryData.offense_ranking : "",
          removePercent(categoryData.defense || ""),
          categoryData.defense_ranking !== null ? categoryData.defense_ranking : "",
          removePercent(categoryData.d1_avg || "")
        ]);
      }
    });
    
    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// CATEGORY: WIKIPEDIA DATA
// ========================================

function GET_WIKI_DATA(url) {
  try {
    var response = UrlFetchApp.fetch(url);
    var data = JSON.parse(response.getContentText());
    
    if (!data.wikipedia) {
      return [["Wikipedia data not available"]];
    }
    
    var wiki = data.wikipedia;
    var championships = wiki.championships || {};
    var tournamentAppearances = wiki.tournamentAppearances || {};
    
    var table = [
      ["=== TEAM INFORMATION ==="],
      ["University", wiki.universityName || "N/A"],
      ["Head Coach", wiki.headCoach || "N/A"],
      ["Head Coach Seasons", wiki.headCoachSeasons ? wiki.headCoachSeasons + " seasons" : "N/A"],
      ["Conference", wiki.conference || "N/A"],
      ["Location", wiki.location || "N/A"],
      ["All-Time Record", wiki.allTimeRecord || "N/A"],
      [""],
      ["=== ARENA ==="],
      ["Arena", wiki.arena || "N/A"],
      ["Capacity", wiki.capacity ? wiki.capacity.toLocaleString() : "N/A"],
      [""],
      ["=== NCAA CHAMPIONSHIPS ==="],
      ["NCAA Tournament Championships", championships.ncaaTournament && championships.ncaaTournament.length ? championships.ncaaTournament.length + " titles" : "0 titles"],
      ["Championship Years", championships.ncaaTournament && championships.ncaaTournament.length ? championships.ncaaTournament.join(", ") : "None"],
      [""],
      ["=== NCAA RUNNER UP ==="],
      ["Runner Up Appearances", championships.ncaaRunnerUp && championships.ncaaRunnerUp.length ? championships.ncaaRunnerUp.length + " times" : "0 times"],
      ["Runner Up Years", championships.ncaaRunnerUp && championships.ncaaRunnerUp.length ? championships.ncaaRunnerUp.join(", ") : "None"],
      [""],
      ["=== TOURNAMENT APPEARANCES ==="],
      ["NCAA Tournament", tournamentAppearances.ncaaTournament ? tournamentAppearances.ncaaTournament + " appearances" : "N/A"],
      ["NCAA Tournament Years", tournamentAppearances.ncaaTournamentYears && tournamentAppearances.ncaaTournamentYears.length ? tournamentAppearances.ncaaTournamentYears.join(", ") : "None"],
      [""],
      ["Final Four", tournamentAppearances.finalFour ? tournamentAppearances.finalFour + " appearances" : "N/A"],
      ["Final Four Years", tournamentAppearances.finalFourYears && tournamentAppearances.finalFourYears.length ? tournamentAppearances.finalFourYears.join(", ") : "None"],
      [""],
      ["Elite Eight", tournamentAppearances.eliteEight ? tournamentAppearances.eliteEight + " appearances" : "N/A"],
      ["Elite Eight Years", tournamentAppearances.eliteEightYears && tournamentAppearances.eliteEightYears.length ? tournamentAppearances.eliteEightYears.join(", ") : "None"],
      [""],
      ["Sweet Sixteen", tournamentAppearances.sweetSixteen ? tournamentAppearances.sweetSixteen + " appearances" : "N/A"],
      ["Sweet Sixteen Years", tournamentAppearances.sweetSixteenYears && tournamentAppearances.sweetSixteenYears.length ? tournamentAppearances.sweetSixteenYears.join(", ") : "None"],
      [""],
      ["=== CONFERENCE TOURNAMENT TITLES ==="],
      ["Conference Tournament Championships", championships.conferenceTournament && championships.conferenceTournament.length ? championships.conferenceTournament.length + " titles" : "0 titles"],
      ["Championship Years", championships.conferenceTournament && championships.conferenceTournament.length ? championships.conferenceTournament.join(", ") : "None"],
      [""],
      ["=== CONFERENCE REGULAR SEASON TITLES ==="],
      ["Conference Regular Season Championships", championships.regularSeason && championships.regularSeason.length ? championships.regularSeason.length + " titles" : "0 titles"],
      ["Championship Years", championships.regularSeason && championships.regularSeason.length ? championships.regularSeason.join(", ") : "None"],
      [""]
    ];
    
    // Add source information (always include, use "N/A" if missing)
    table.push(["Source", wiki.source || "N/A"]);
    table.push(["URL", wiki.url || "N/A"]);

    return table;
  } catch (e) {
    return [["Error: " + e.message]];
  }
}

// ========================================
// CATEGORY: SPREADSHEET UTILITIES
// ========================================

/**
 * Copies the dynamic roster data from GET_PLAYERS_FULL and pastes it as values.
 * This automates the manual "copy and paste as values" step.
 *
 * Source: GET_PLAYERS_FULL!A3:CQ23 (header + up to 20 players)
 * Destination: GET_PLAYERS_FULL!A24:CQ44
 *
 * Call this function after duplicating a template or when data needs refreshing.
 * Can be triggered via menu: CBB Tools > Copy Roster as Values
 */
function COPY_ROSTER_AS_VALUES() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var destSheet = ss.getSheetByName("GET_PLAYERS_FULL");
  var sourceSheet = ss.getSheetByName("_PLAYERS_RAW");

  if (!destSheet) {
    SpreadsheetApp.getUi().alert("Error: GET_PLAYERS_FULL sheet not found");
    return;
  }

  if (!sourceSheet) {
    SpreadsheetApp.getUi().alert("Error: _PLAYERS_RAW sheet not found.\n\nThis spreadsheet may need to be updated to use the new structure.");
    return;
  }

  // Source range: _PLAYERS_RAW!A3:CQ21 (row 3 = header, rows 4-21 = up to 18 players)
  // 95 columns (A to CQ), 19 rows (header + 18 players max)
  var sourceRange = sourceSheet.getRange("A3:CQ21");
  var sourceValues = sourceRange.getValues();

  // Find the last row with data (check column A for player names)
  var lastDataRow = 0;
  for (var i = 0; i < sourceValues.length; i++) {
    if (sourceValues[i][0] && sourceValues[i][0] !== "") {
      lastDataRow = i;
    }
  }

  // Include header row (row 0) plus all player rows
  var rowsToCopy = lastDataRow + 1;

  // Clear destination range first (GET_PLAYERS_FULL!A24:CQ44)
  var clearRange = destSheet.getRange("A24:CQ44");
  clearRange.clearContent();

  // Copy only the rows that have data (starting at row 24)
  var destRange = destSheet.getRange(24, 1, rowsToCopy, 95); // Row 24, Col A, rowsToCopy rows, 95 cols
  var dataToCopy = sourceValues.slice(0, rowsToCopy);
  destRange.setValues(dataToCopy);

  // Show confirmation
  SpreadsheetApp.getUi().alert("Roster copied successfully!\n\n" + (rowsToCopy - 1) + " players copied to rows 24-" + (23 + rowsToCopy));
}

/**
 * Triggers a refresh of the team data by calling the web API.
 * Extracts team name from the JSON URL in _PLAYERS_RAW!A1.
 *
 * This is a fire-and-forget operation - the generation runs in the background
 * and typically takes 30-45 seconds to complete (without historical stats).
 *
 * After generation completes, use RELOAD_DATA() to fetch the fresh data.
 */
function REFRESH_TEAM_DATA() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("_PLAYERS_RAW");
  var ui = SpreadsheetApp.getUi();

  // Try to detect user's email for pre-filling
  var detectedEmail = "";
  try {
    detectedEmail = Session.getEffectiveUser().getEmail() || "";
  } catch (e) {
    detectedEmail = "";
  }

  // Try to get current team name from URL
  var currentTeamName = "";
  if (sheet) {
    var jsonUrl = sheet.getRange("A1").getValue();
    if (jsonUrl) {
      var match = jsonUrl.match(/\/([a-z_]+)_scouting_data_\d{4}\.json/i);
      if (match) {
        var teamSlug = match[1];
        currentTeamName = teamSlug.replace(/_/g, ' ').replace(/\b\w/g, function(c) { return c.toUpperCase(); });
      }
    }
  }

  // Build HTML for the dialog with email input and spinner overlay
  var htmlContent = '<!DOCTYPE html>' +
    '<html><head>' +
    '<style>' +
    'body { font-family: Arial, sans-serif; padding: 15px; margin: 0; }' +
    '.form-group { margin-bottom: 12px; }' +
    'label { font-weight: bold; display: block; margin-bottom: 6px; font-size: 13px; }' +
    'input[type="text"], input[type="email"] { width: 100%; padding: 8px; font-size: 14px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }' +
    '.checkbox-container { margin-bottom: 8px; }' +
    '.checkbox-container label { font-weight: normal; display: inline; }' +
    '.checkbox-container input { margin-right: 8px; }' +
    '.note { font-size: 11px; color: #666; margin-bottom: 12px; padding: 6px 8px; background-color: #f5f5f5; border-radius: 4px; }' +
    '.email-note { font-size: 11px; color: #888; margin-top: 4px; }' +
    '.buttons { text-align: right; margin-top: 12px; }' +
    'button { padding: 8px 16px; margin-left: 8px; cursor: pointer; font-size: 13px; }' +
    '.primary { background-color: #4285f4; color: white; border: none; border-radius: 4px; }' +
    '.primary:hover { background-color: #3367d6; }' +
    '.primary:disabled { background-color: #a0c4ff; cursor: not-allowed; }' +
    '.secondary { background-color: #f1f1f1; border: 1px solid #ccc; border-radius: 4px; }' +
    '.secondary:disabled { opacity: 0.5; cursor: not-allowed; }' +
    /* Spinner overlay styles */
    '.overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.9); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; }' +
    '.overlay.active { display: flex; }' +
    '.spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #4285f4; border-radius: 50%; animation: spin 1s linear infinite; }' +
    '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }' +
    '.overlay-text { margin-top: 15px; font-size: 14px; color: #333; text-align: center; }' +
    '.overlay-subtext { margin-top: 5px; font-size: 12px; color: #666; }' +
    '</style>' +
    '</head><body>' +
    /* Spinner overlay */
    '<div id="overlay" class="overlay">' +
    '<div class="spinner"></div>' +
    '<div class="overlay-text" id="overlayText">Starting data generation...</div>' +
    '<div class="overlay-subtext">This window will close automatically</div>' +
    '</div>' +
    /* Form content */
    '<div class="form-group">' +
    '<label>Team:</label>' +
    '<div style="font-size: 18px; font-weight: 600; color: #1a73e8; padding: 8px 0;">' + currentTeamName + '</div>' +
    '</div>' +
    '<div class="form-group">' +
    '<label>Email for notification (optional):</label>' +
    '<input type="email" id="emailInput" placeholder="you@example.com" value="' + detectedEmail + '">' +
    '<div class="email-note">Get notified when data generation completes</div>' +
    '</div>' +
    '<div class="buttons">' +
    '<button class="secondary" id="cancelBtn" onclick="google.script.host.close()">Cancel</button>' +
    '<button class="primary" id="submitBtn" onclick="submitRefresh()">Start Generation</button>' +
    '</div>' +
    '<script>' +
    'var isSubmitting = false;' +
    'var teamName = "' + currentTeamName + '";' +
    'function submitRefresh() {' +
    '  if (isSubmitting) {' +
    '    console.log("[CBBD] submitRefresh blocked - already submitting");' +
    '    return;' +
    '  }' +
    '  isSubmitting = true;' +
    '  console.log("[CBBD] submitRefresh started");' +
    '  var email = document.getElementById("emailInput").value.trim();' +
    '  var submitBtn = document.getElementById("submitBtn");' +
    '  var cancelBtn = document.getElementById("cancelBtn");' +
    '  var overlay = document.getElementById("overlay");' +
    '  var overlayText = document.getElementById("overlayText");' +
    /* Show spinner overlay */
    '  overlay.classList.add("active");' +
    '  overlayText.textContent = "Starting data generation for " + teamName + "...";' +
    '  submitBtn.disabled = true;' +
    '  cancelBtn.disabled = true;' +
    '  console.log("[CBBD] Calling refreshTeamWithOptions for: " + teamName + ", email: " + email);' +
    '  google.script.run' +
    '    .withSuccessHandler(function(result) {' +
    '      console.log("[CBBD] Success - closing modal");' +
    '      google.script.host.close();' +
    '    })' +
    '    .withFailureHandler(function(error) {' +
    '      console.log("[CBBD] Error: " + error);' +
    '      isSubmitting = false;' +
    '      overlay.classList.remove("active");' +
    '      submitBtn.disabled = false;' +
    '      cancelBtn.disabled = false;' +
    '      alert("Error: " + error);' +
    '    })' +
    '    .refreshTeamWithOptions(teamName, email);' +
    '}' +
    '</script>' +
    '</body></html>';

  var html = HtmlService.createHtmlOutput(htmlContent)
    .setWidth(400)
    .setHeight(340);

  ui.showModalDialog(html, 'Step 1: Start Data Generation');
}

/**
 * Helper function called by REFRESH_TEAM_DATA dialog.
 * Updates the URL if team changed and triggers regeneration.
 * Historical stats are now handled automatically (smart detection).
 *
 * @param {string} teamName - The team name to regenerate
 * @param {string} notifyEmail - Email address for completion notification (optional)
 */
function refreshTeamWithOptions(teamName, notifyEmail) {
  Logger.log("[CBBD] refreshTeamWithOptions called - team: " + teamName + ", email: " + (notifyEmail || "none"));

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("_PLAYERS_RAW");

  if (sheet) {
    // Convert team name to URL slug (spaces to underscores, lowercase)
    var teamSlug = teamName.toLowerCase().replace(/\s+/g, '_');
    var newUrl = "https://cbb-data-files.s3.us-east-1.amazonaws.com/data/2026/" + teamSlug + "_scouting_data_2026.json";

    // Update the URL in _PLAYERS_RAW!A1
    sheet.getRange("A1").setValue(newUrl);
    SpreadsheetApp.flush();
  }

  // Trigger the regeneration (historical stats handled automatically via smart detection)
  triggerTeamRegeneration(teamName, notifyEmail);
}

/**
 * Shared function to trigger data regeneration for a team.
 * Called by both REFRESH_TEAM_DATA and REFRESH_DIFFERENT_TEAM.
 * Historical stats are now handled automatically via smart detection.
 *
 * @param {string} teamName - The team name to regenerate data for
 * @param {string} providedEmail - Email for completion notification (optional)
 */
function triggerTeamRegeneration(teamName, providedEmail) {
  Logger.log("[CBBD] triggerTeamRegeneration called - team: " + teamName + ", providedEmail: " + (providedEmail || "none"));

  var userEmail = "";

  // If email was provided from modal, use it directly (no prompt needed)
  if (providedEmail !== undefined && providedEmail !== null) {
    userEmail = providedEmail;
    Logger.log("[CBBD] Using email from modal: " + userEmail);
  } else {
    // Legacy path: prompt for email (used by REFRESH_TEAM_DATA which doesn't have modal)
    var detectedEmail = "";
    try {
      detectedEmail = Session.getEffectiveUser().getEmail() || "";
    } catch (e) {
      detectedEmail = "";
    }

    var ui = SpreadsheetApp.getUi();
    var promptMessage = detectedEmail
      ? 'Your email: ' + detectedEmail + '\n\nClick OK to use this email, or enter a different one below.\nClick Cancel to skip email notification.'
      : 'Enter your email to receive a notification when data refresh completes (or click Cancel to skip):';

    var response = ui.prompt('Email Notification', promptMessage, ui.ButtonSet.OK_CANCEL);

    if (response.getSelectedButton() == ui.Button.OK) {
      var enteredEmail = response.getResponseText().trim();
      // Use entered email if provided, otherwise use detected email
      userEmail = enteredEmail || detectedEmail;
    }
  }

  // Call the API to trigger data generation
  // Historical stats are handled automatically via smart detection (no param needed)
  var apiUrl = "https://cbb-data-generator.onrender.com/api/generate";

  try {
    var payload = {
      "team_name": teamName
    };

    // Add email notification if available
    if (userEmail) {
      payload["notify_email"] = userEmail;
      Logger.log("[CBBD] Email notification will be sent to: " + userEmail);
    }

    var options = {
      "method": "post",
      "contentType": "application/json",
      "payload": JSON.stringify(payload),
      "muteHttpExceptions": true
    };

    Logger.log("[CBBD] Calling API: " + apiUrl + " with payload: " + JSON.stringify(payload));
    var response = UrlFetchApp.fetch(apiUrl, options);
    Logger.log("[CBBD] API response code: " + response.getResponseCode());
    var responseCode = response.getResponseCode();
    var responseBody = JSON.parse(response.getContentText());

    if (responseCode === 200 && responseBody.job_id) {
      Logger.log("[CBBD] Job started successfully - job_id: " + responseBody.job_id);
      var timeEstimate = "30-60 sec";  // Smart detection: uses cache when available

      // Build toast message (keep it short for the toast)
      var toastTitle = "Data refresh started!";
      var toastMessage = teamName + " - " + timeEstimate;
      if (userEmail) {
        toastMessage += ". Email notification: " + userEmail;
      }

      // Show non-blocking toast notification (15 second display)
      SpreadsheetApp.getActiveSpreadsheet().toast(toastMessage, toastTitle, 15);
    } else {
      Logger.log("[CBBD] API error - status: " + responseCode + ", response: " + JSON.stringify(responseBody));
      SpreadsheetApp.getUi().alert(
        "Error starting data refresh:\n\n" +
        "Status: " + responseCode + "\n" +
        "Response: " + JSON.stringify(responseBody)
      );
    }
  } catch (e) {
    Logger.log("[CBBD] Exception calling API: " + e.message);
    SpreadsheetApp.getUi().alert("Error calling API:\n\n" + e.message);
  }
}

/**
 * Opens a dialog to select a different team and regenerate its data.
 * Fetches the list of all teams from the API and displays a searchable dropdown.
 */
function REFRESH_DIFFERENT_TEAM() {
  var ui = SpreadsheetApp.getUi();

  // Try to detect user's email for pre-filling
  var detectedEmail = "";
  try {
    detectedEmail = Session.getEffectiveUser().getEmail() || "";
  } catch (e) {
    detectedEmail = "";
  }

  // Fetch the list of teams from the API
  var teamsApiUrl = "https://cbb-data-generator.onrender.com/api/teams";
  var teams = [];

  try {
    var response = UrlFetchApp.fetch(teamsApiUrl, { muteHttpExceptions: true });
    var responseCode = response.getResponseCode();

    if (responseCode === 200) {
      teams = JSON.parse(response.getContentText());
    } else {
      ui.alert("Error fetching team list. Please try again.");
      return;
    }
  } catch (e) {
    ui.alert("Error fetching team list:\n\n" + e.message);
    return;
  }

  if (!teams || teams.length === 0) {
    ui.alert("No teams found. Please try again later.");
    return;
  }

  // Build teams JSON for the search (extract just names)
  var teamNames = [];
  for (var i = 0; i < teams.length; i++) {
    teamNames.push(teams[i].name || teams[i]);
  }
  var teamsJson = JSON.stringify(teamNames);

  // Build HTML for the dialog with fuzzy search, email input, and spinner overlay
  var htmlContent = '<!DOCTYPE html>' +
    '<html><head>' +
    '<style>' +
    'body { font-family: Arial, sans-serif; padding: 15px; margin: 0; }' +
    '.form-group { margin-bottom: 12px; }' +
    'label { font-weight: bold; display: block; margin-bottom: 6px; font-size: 13px; }' +
    'input[type="text"], input[type="email"] { width: 100%; padding: 8px; font-size: 14px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }' +
    '.search-container { position: relative; }' +
    '.search-input { width: 100%; }' +
    '.dropdown { position: absolute; top: 100%; left: 0; right: 0; max-height: 200px; overflow-y: auto; background: white; border: 1px solid #ddd; border-top: none; border-radius: 0 0 4px 4px; z-index: 100; display: none; }' +
    '.dropdown.show { display: block; }' +
    '.dropdown-item { padding: 8px 12px; cursor: pointer; font-size: 14px; }' +
    '.dropdown-item:hover, .dropdown-item.highlighted { background-color: #e8f0fe; }' +
    '.selected-team { margin-top: 6px; padding: 6px 10px; background-color: #e8f5e9; border-radius: 4px; font-size: 13px; color: #2e7d32; display: none; }' +
    '.selected-team.show { display: block; }' +
    '.checkbox-container { margin-bottom: 8px; }' +
    '.checkbox-container label { font-weight: normal; display: inline; }' +
    '.checkbox-container input { margin-right: 8px; }' +
    '.note { font-size: 11px; color: #666; margin-bottom: 12px; padding: 6px 8px; background-color: #f5f5f5; border-radius: 4px; }' +
    '.email-note { font-size: 11px; color: #888; margin-top: 4px; }' +
    '.buttons { text-align: right; margin-top: 12px; }' +
    'button { padding: 8px 16px; margin-left: 8px; cursor: pointer; font-size: 13px; }' +
    '.primary { background-color: #4285f4; color: white; border: none; border-radius: 4px; }' +
    '.primary:hover { background-color: #3367d6; }' +
    '.primary:disabled { background-color: #a0c4ff; cursor: not-allowed; }' +
    '.secondary { background-color: #f1f1f1; border: 1px solid #ccc; border-radius: 4px; }' +
    '.secondary:disabled { opacity: 0.5; cursor: not-allowed; }' +
    /* Spinner overlay styles */
    '.overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(255,255,255,0.9); z-index: 1000; justify-content: center; align-items: center; flex-direction: column; }' +
    '.overlay.active { display: flex; }' +
    '.spinner { width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #4285f4; border-radius: 50%; animation: spin 1s linear infinite; }' +
    '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }' +
    '.overlay-text { margin-top: 15px; font-size: 14px; color: #333; text-align: center; }' +
    '.overlay-subtext { margin-top: 5px; font-size: 12px; color: #666; }' +
    '</style>' +
    '</head><body>' +
    /* Spinner overlay */
    '<div id="overlay" class="overlay">' +
    '<div class="spinner"></div>' +
    '<div class="overlay-text" id="overlayText">Starting data generation...</div>' +
    '<div class="overlay-subtext">This window will close automatically</div>' +
    '</div>' +
    /* Form content */
    '<div class="form-group">' +
    '<label>Search Team:</label>' +
    '<div class="search-container">' +
    '<input type="text" id="teamSearch" class="search-input" placeholder="Type to search (e.g., Oregon, UCLA, Duke)" autocomplete="off">' +
    '<div id="dropdown" class="dropdown"></div>' +
    '</div>' +
    '<div id="selectedTeam" class="selected-team"><strong>Selected:</strong> <span id="selectedTeamName"></span></div>' +
    '</div>' +
    '<div class="form-group">' +
    '<label>Email for notification (optional):</label>' +
    '<input type="email" id="emailInput" placeholder="you@example.com" value="' + detectedEmail + '">' +
    '<div class="email-note">Get notified when data generation completes</div>' +
    '</div>' +
    '<div class="buttons">' +
    '<button class="secondary" id="cancelBtn" onclick="google.script.host.close()">Cancel</button>' +
    '<button class="primary" id="submitBtn" onclick="submitTeam()">Regenerate Data</button>' +
    '</div>' +
    '<script>' +
    'var teams = ' + teamsJson + ';' +
    'var selectedTeamName = null;' +
    'var isSubmitting = false;' +
    'var highlightedIndex = -1;' +
    'var filteredTeams = [];' +
    '' +
    'var searchInput = document.getElementById("teamSearch");' +
    'var dropdown = document.getElementById("dropdown");' +
    'var selectedDiv = document.getElementById("selectedTeam");' +
    'var selectedNameSpan = document.getElementById("selectedTeamName");' +
    '' +
    'searchInput.addEventListener("input", function(e) {' +
    '  var query = e.target.value.toLowerCase().trim();' +
    '  highlightedIndex = -1;' +
    '  if (selectedTeamName && selectedTeamName.toLowerCase() !== query) {' +
    '    selectedTeamName = null;' +
    '    selectedDiv.classList.remove("show");' +
    '  }' +
    '  if (query.length === 0) {' +
    '    dropdown.classList.remove("show");' +
    '    filteredTeams = [];' +
    '    return;' +
    '  }' +
    '  filteredTeams = teams.filter(function(t) {' +
    '    return t.toLowerCase().indexOf(query) !== -1;' +
    '  }).slice(0, 15);' +
    '  if (filteredTeams.length > 0) {' +
    '    dropdown.innerHTML = filteredTeams.map(function(t, i) {' +
    '      return "<div class=\\"dropdown-item\\" data-index=\\"" + i + "\\" onclick=\\"selectTeam(\'" + t.replace(/\'/g, "\\\\\'") + "\')\\">" + t + "</div>";' +
    '    }).join("");' +
    '    dropdown.classList.add("show");' +
    '  } else {' +
    '    dropdown.innerHTML = "<div class=\\"dropdown-item\\" style=\\"color:#999;cursor:default;\\">No teams found</div>";' +
    '    dropdown.classList.add("show");' +
    '  }' +
    '});' +
    '' +
    'searchInput.addEventListener("keydown", function(e) {' +
    '  var items = dropdown.querySelectorAll(".dropdown-item[data-index]");' +
    '  if (e.key === "ArrowDown") {' +
    '    e.preventDefault();' +
    '    highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);' +
    '    updateHighlight(items);' +
    '  } else if (e.key === "ArrowUp") {' +
    '    e.preventDefault();' +
    '    highlightedIndex = Math.max(highlightedIndex - 1, 0);' +
    '    updateHighlight(items);' +
    '  } else if (e.key === "Enter") {' +
    '    e.preventDefault();' +
    '    if (highlightedIndex >= 0 && filteredTeams[highlightedIndex]) {' +
    '      selectTeam(filteredTeams[highlightedIndex]);' +
    '    }' +
    '  }' +
    '});' +
    '' +
    'function updateHighlight(items) {' +
    '  items.forEach(function(item, i) {' +
    '    if (i === highlightedIndex) {' +
    '      item.classList.add("highlighted");' +
    '      item.scrollIntoView({ block: "nearest" });' +
    '    } else {' +
    '      item.classList.remove("highlighted");' +
    '    }' +
    '  });' +
    '}' +
    '' +
    'function selectTeam(teamName) {' +
    '  selectedTeamName = teamName;' +
    '  searchInput.value = teamName;' +
    '  selectedNameSpan.textContent = teamName;' +
    '  selectedDiv.classList.add("show");' +
    '  dropdown.classList.remove("show");' +
    '  highlightedIndex = -1;' +
    '}' +
    '' +
    'document.addEventListener("click", function(e) {' +
    '  if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {' +
    '    dropdown.classList.remove("show");' +
    '  }' +
    '});' +
    '' +
    'function submitTeam() {' +
    '  if (isSubmitting) {' +
    '    console.log("[CBBD] submitTeam blocked - already submitting");' +
    '    return;' +
    '  }' +
    '  if (!selectedTeamName) {' +
    '    alert("Please select a team from the dropdown");' +
    '    searchInput.focus();' +
    '    return;' +
    '  }' +
    '  isSubmitting = true;' +
    '  console.log("[CBBD] submitTeam started");' +
    '  var teamName = selectedTeamName;' +
    '  var email = document.getElementById("emailInput").value.trim();' +
    '  var submitBtn = document.getElementById("submitBtn");' +
    '  var cancelBtn = document.getElementById("cancelBtn");' +
    '  var overlay = document.getElementById("overlay");' +
    '  var overlayText = document.getElementById("overlayText");' +
    '  overlay.classList.add("active");' +
    '  overlayText.textContent = "Starting data generation for " + teamName + "...";' +
    '  submitBtn.disabled = true;' +
    '  cancelBtn.disabled = true;' +
    '  console.log("[CBBD] Calling regenerateAndSwitchTeam for: " + teamName + ", email: " + email);' +
    '  google.script.run' +
    '    .withSuccessHandler(function(result) {' +
    '      console.log("[CBBD] Success - closing modal");' +
    '      google.script.host.close();' +
    '    })' +
    '    .withFailureHandler(function(error) {' +
    '      console.log("[CBBD] Error: " + error);' +
    '      isSubmitting = false;' +
    '      overlay.classList.remove("active");' +
    '      submitBtn.disabled = false;' +
    '      cancelBtn.disabled = false;' +
    '      alert("Error: " + error);' +
    '    })' +
    '    .regenerateAndSwitchTeam(teamName, email);' +
    '}' +
    '</script>' +
    '</body></html>';

  var html = HtmlService.createHtmlOutput(htmlContent)
    .setWidth(420)
    .setHeight(380);

  ui.showModalDialog(html, 'Refresh Different Team');
}

/**
 * Regenerates data for a team AND updates the spreadsheet URL to load that team.
 * Called by REFRESH_DIFFERENT_TEAM dialog.
 * Historical stats are now handled automatically via smart detection.
 *
 * @param {string} teamName - The team name to regenerate and switch to
 * @param {string} notifyEmail - Email address for completion notification (optional)
 */
function regenerateAndSwitchTeam(teamName, notifyEmail) {
  Logger.log("[CBBD] regenerateAndSwitchTeam called - team: " + teamName + ", email: " + (notifyEmail || "none"));

  // First, update the URL in _PLAYERS_RAW!A1 to point to the new team
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("_PLAYERS_RAW");

  if (sheet) {
    // Convert team name to URL slug (spaces to underscores, lowercase)
    var teamSlug = teamName.toLowerCase().replace(/\s+/g, '_');
    var newUrl = "https://cbb-data-files.s3.us-east-1.amazonaws.com/data/2026/" + teamSlug + "_scouting_data_2026.json";

    // Update the URL in _PLAYERS_RAW!A1
    sheet.getRange("A1").setValue(newUrl);
    SpreadsheetApp.flush();
  }

  // Trigger the regeneration (historical stats handled automatically via smart detection)
  triggerTeamRegeneration(teamName, notifyEmail);
}

/**
 * Reloads data by adding/updating a cache-buster parameter on the JSON URL.
 * This forces Google Sheets to re-fetch the data from the server.
 *
 * After reloading, displays the "Data Generated" timestamp so the user
 * can confirm they're seeing fresh data.
 */
function RELOAD_DATA() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName("_PLAYERS_RAW");
  var metaSheet = ss.getSheetByName("meta");

  if (!sheet) {
    SpreadsheetApp.getUi().alert("Error: _PLAYERS_RAW sheet not found.\n\nThis spreadsheet may need to be updated to use the new structure.");
    return;
  }

  // Read the current JSON URL from _PLAYERS_RAW!A1
  var jsonUrl = sheet.getRange("A1").getValue();

  if (!jsonUrl || jsonUrl === "") {
    SpreadsheetApp.getUi().alert("Error: No JSON URL found in _PLAYERS_RAW!A1");
    return;
  }

  // Remove existing cache-buster if present, then add new one
  var baseUrl = jsonUrl.split('?')[0];
  var newUrl = baseUrl + "?t=" + new Date().getTime();

  // Update the URL in _PLAYERS_RAW!A1
  sheet.getRange("A1").setValue(newUrl);

  // Force recalculation
  SpreadsheetApp.flush();

  // Wait a moment for formulas to recalculate
  Utilities.sleep(2000);

  // Copy roster as values automatically
  COPY_ROSTER_AS_VALUES();

  // Read the Data Generated timestamp from meta sheet
  var dataGenerated = "Unknown";
  if (metaSheet) {
    dataGenerated = metaSheet.getRange("B7").getValue() || "Unknown";
  }

  SpreadsheetApp.getUi().alert(
    "✅ Data loaded successfully!\n\n" +
    "Data Generated: " + dataGenerated + "\n\n" +
    "Roster has been copied as values.\n\n" +
    "Tip: If data looks stale, run '1️⃣ Start Data Generation' first, wait for the email notification, then run this step again."
  );
}

/**
 * Creates a custom menu in the spreadsheet for easy access to utilities.
 * This function runs automatically when the spreadsheet is opened.
 */
function onOpen() {
  var ui = SpreadsheetApp.getUi();
  ui.createMenu('CBB Tools')
    .addItem('1️⃣ Start Data Generation', 'REFRESH_TEAM_DATA')
    .addItem('2️⃣ Load Updated Data', 'RELOAD_DATA')
    .addSeparator()
    .addItem('Switch to Different Team...', 'REFRESH_DIFFERENT_TEAM')
    .addSeparator()
    .addItem('Copy Roster as Values', 'COPY_ROSTER_AS_VALUES')
    .addToUi();
}