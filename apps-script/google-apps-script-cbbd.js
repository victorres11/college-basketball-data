// ========================================
// CATEGORY 1: TEAM META INFORMATION
// ========================================

function GET_TEAM_META(url) {
    try {
      var response = UrlFetchApp.fetch(url);
      var data = JSON.parse(response.getContentText());
      
      var table = [
        ["Field", "Value"],
        ["Team", data.team],
        ["Season", data.season],
        ["Season Type", data.seasonType],
        ["Data Generated", data.dataGenerated],
        ["Total Players", data.metadata.totalPlayers],
        ["API Calls", data.metadata.apiCalls]
      ];
      
      // Add mascot if available (from cached roster)
      if (data.mascot) {
        table.push(["Mascot", data.mascot]);
      }
      
      // Add total record if available
      if (data.totalRecord) {
        table.push([""]);
        table.push(["=== RECORD ==="]);
        table.push(["Total Record", data.totalRecord.wins + "-" + data.totalRecord.losses]);
        table.push(["Total Wins", data.totalRecord.wins]);
        table.push(["Total Losses", data.totalRecord.losses]);
        table.push(["Total Games", data.totalRecord.games]);
      }
      
      // Add conference record if available
      if (data.conferenceRecord) {
        table.push([""]);
        table.push(["=== CONFERENCE RECORD ==="]);
        table.push(["Conference Record", data.conferenceRecord.wins + "-" + data.conferenceRecord.losses]);
        table.push(["Conference Wins", data.conferenceRecord.wins]);
        table.push(["Conference Losses", data.conferenceRecord.losses]);
        table.push(["Conference Games", data.conferenceRecord.games]);
      }
      
      // Add NET rating if available
      if (data.netRating) {
        table.push([""]);
        table.push(["=== NET RATING ==="]);
        table.push(["NET Rank", data.netRating.rating || "N/A"]);
        if (data.netRating.previousRating) {
          table.push(["Previous Rank", data.netRating.previousRating]);
        }
        table.push(["Source", data.netRating.source || "bballnet.com"]);
        if (data.netRating.url) {
          table.push(["URL", data.netRating.url]);
        }
      }
      
      // Add coach history if available (append to end)
      if (data.coachHistory && data.coachHistory.seasons && data.coachHistory.seasons.length > 0) {
        table.push([""]);
        table.push(["=== COACH HISTORY (Last 6 Complete Seasons) ==="]);
        table.push(["Season", "Conference", "Overall W-L", "Conf W-L", "NCAA Tournament", "Seed", "Coach"]);
        
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
        
        if (data.coachHistory.source) {
          table.push([""]);
          table.push(["Source", data.coachHistory.source]);
        }
        if (data.coachHistory.url) {
          table.push(["URL", data.coachHistory.url]);
        }
      }
      
      return table;
    } catch (e) {
      return [["Error: " + e.message]];
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
      
      // Add per-game stats if available
      if (stats.perGameStats) {
        var pg = stats.perGameStats;
        var pgTeam = pg.teamStats || {};
        var pgOpp = pg.opponentStats || {};
        var pgMargins = pg.margins || {};
        var pgRatios = pg.ratios || {};
        
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
      }
      
      // Add possession game records at the end
      if (stats.possessionGameRecords) {
        table.push([""]);
        table.push(["=== POSSESSION GAME RECORDS ==="]);
        table.push(["1-Possession Games", 
         (stats.possessionGameRecords.onePossession ? 
          stats.possessionGameRecords.onePossession.wins + "-" + stats.possessionGameRecords.onePossession.losses : 
          "0-0")]);
        table.push(["2-Possession Games", 
         (stats.possessionGameRecords.twoPossession ? 
          stats.possessionGameRecords.twoPossession.wins + "-" + stats.possessionGameRecords.twoPossession.losses : 
          "0-0")]);
      }
      
      // Add home/away/neutral records at the end
      if (data.homeRecord || data.awayRecord || data.neutralRecord) {
        table.push([""]);
        table.push(["=== HOME/AWAY/NEUTRAL RECORDS ==="]);
        if (data.homeRecord) {
          table.push(["Home Record", data.homeRecord.wins + "-" + data.homeRecord.losses]);
          table.push(["Home Wins", data.homeRecord.wins]);
          table.push(["Home Losses", data.homeRecord.losses]);
          table.push(["Home Games", data.homeRecord.games]);
        }
        if (data.awayRecord) {
          table.push(["Away Record", data.awayRecord.wins + "-" + data.awayRecord.losses]);
          table.push(["Away Wins", data.awayRecord.wins]);
          table.push(["Away Losses", data.awayRecord.losses]);
          table.push(["Away Games", data.awayRecord.games]);
        }
        if (data.neutralRecord) {
          table.push(["Neutral Record", data.neutralRecord.wins + "-" + data.neutralRecord.losses]);
          table.push(["Neutral Wins", data.neutralRecord.wins]);
          table.push(["Neutral Losses", data.neutralRecord.losses]);
          table.push(["Neutral Games", data.neutralRecord.games]);
        }
      }
      
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
      
      if (data.teamGameStats.length === 0) {
        return [["Error: teamGameStats array is empty"]];
      }
      
      var table = [[
        "Date", "Opponent", "Home/Away", "Conference", "Result",
        "Score", "Opp Score",
        "FGM-FGA", "FG%", "3PM-3PA", "3P%", "FTM-FTA", "FT%",
        "OReb", "DReb", "TReb", "Ast", "Stl", "Blk", "TO", "Fouls",
        "Opp FGM-FGA", "Opp FG%", "Opp 3PM-3PA", "Opp 3P%", "Opp FTM-FTA", "Opp FT%",
        "Opp OReb", "Opp DReb", "Opp TReb", "Opp Ast", "Opp Stl", "Opp Blk", "Opp TO", "Opp Fouls"
      ]];
      
      data.teamGameStats.forEach(function(game) {
        var result = game.teamStats.points.total > game.opponentStats.points.total ? "W" : "L";
        
        // Format date from '2024-11-05T03:30:00.000Z' to '11/5'
        var dateObj = new Date(game.startDate);
        var month = dateObj.getMonth() + 1; // getMonth() returns 0-11
        var day = dateObj.getDate();
        var formattedDate = month + "/" + day;
        
        table.push([
          formattedDate,
          game.opponent,
          game.isHome ? "Home" : "Away",
          game.conferenceGame ? "Conf" : "Non-Conf",
          result,
          game.teamStats.points.total,
          game.opponentStats.points.total,
          game.teamStats.fieldGoals.made + "-" + game.teamStats.fieldGoals.attempted,
          game.teamStats.fieldGoals.pct + "%",
          game.teamStats.threePointFieldGoals.made + "-" + game.teamStats.threePointFieldGoals.attempted,
          game.teamStats.threePointFieldGoals.pct + "%",
          game.teamStats.freeThrows.made + "-" + game.teamStats.freeThrows.attempted,
          game.teamStats.freeThrows.pct + "%",
          game.teamStats.rebounds.offensive,
          game.teamStats.rebounds.defensive,
          game.teamStats.rebounds.total,
          game.teamStats.assists,
          game.teamStats.steals,
          game.teamStats.blocks,
          game.teamStats.turnovers.total,
          game.teamStats.fouls.total,
          game.opponentStats.fieldGoals.made + "-" + game.opponentStats.fieldGoals.attempted,
          game.opponentStats.fieldGoals.pct + "%",
          game.opponentStats.threePointFieldGoals.made + "-" + game.opponentStats.threePointFieldGoals.attempted,
          game.opponentStats.threePointFieldGoals.pct + "%",
          game.opponentStats.freeThrows.made + "-" + game.opponentStats.freeThrows.attempted,
          game.opponentStats.freeThrows.pct + "%",
          game.opponentStats.rebounds.offensive,
          game.opponentStats.rebounds.defensive,
          game.opponentStats.rebounds.total,
          game.opponentStats.assists,
          game.opponentStats.steals,
          game.opponentStats.blocks,
          game.opponentStats.turnovers.total,
          game.opponentStats.fouls.total
        ]);
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
  function GET_PLAYER_LAST_GAME_SUMMARY(url, playerName) {
    try {
      var response = UrlFetchApp.fetch(url);
      var data = JSON.parse(response.getContentText());
      
      var player = data.players.find(function(p) {
        return p.name.toLowerCase() === playerName.toLowerCase();
      });
      
      if (!player) return "Player not found";
      if (!player.gameByGame || player.gameByGame.length === 0) return "No games found";
      
      // Get last game
      var game = player.gameByGame[player.gameByGame.length - 1];
      var totalReb = game.rebounds.offensive + game.rebounds.defensive;
      
      // Format: {points}p, {rebounds}r, {assists}a, {turnovers}to, {steals}s, {blocks}b, {fgm}-{fga}fg, {ftm}-{fta}ft, ({3pmade}-{3pa})3p, [{minutes}]
      var summary = game.points + "p, " +
                    totalReb + "r, " +
                    game.assists + "a, " +
                    game.turnovers + "to, " +
                    game.steals + "s, " +
                    game.blocks + "b, " +
                    game.fieldGoals.made + "-" + game.fieldGoals.attempted + "fg, " +
                    game.freeThrows.made + "-" + game.freeThrows.attempted + "ft, " +
                    "(" + game.threePointFieldGoals.made + "-" + game.threePointFieldGoals.attempted + ")3p, " +
                    "[" + game.minutes + "]";
      
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
      
      // Get most recent previous season (last element in array)
      var prevSeason = player.previousSeasons[player.previousSeasons.length - 1];
      var stats = prevSeason.seasonStats;
      
      // Format school name to uppercase
      var school = prevSeason.team.toUpperCase();
      
      // Get values with safe defaults
      var gamesStarted = prevSeason.gamesStarted || 0;
      var ppg = stats.pointsPerGame || 0;  // Changed from stats.ppg
      var rpg = stats.reboundsPerGame || 0;  // Changed from stats.rpg
      var threePct = stats.threePointFieldGoals ? stats.threePointFieldGoals.pct || 0 : 0;  // Changed from .percentage
      var ftPct = stats.freeThrows ? stats.freeThrows.pct || 0 : 0;  // Changed from .percentage
      
      // Format: {School/team} {games_started}g, {season_avg_points}p, {season_avg_rebounds}r, {3p_percentage}% 3p, {ft_percentage}% FT
      var summary = school + " " +
                    gamesStarted + "g, " +
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