/**
 * Library Wrappers for CBB Data Functions
 * 
 * These wrapper functions allow you to call library functions directly from cells
 * without needing the library identifier prefix (e.g., =GET_PLAYERS_FULL(A1) instead of =CBBData.GET_PLAYERS_FULL(A1))
 */

// ========================================
// CATEGORY 1: TEAM META INFORMATION
// ========================================

/**
 * Get team metadata and records including wins, losses, and conference record
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with team metadata and records
 * @customfunction
 */
function GET_TEAM_META(url) {
  return CBBData.GET_TEAM_META(url);
}

// ========================================
// CATEGORY 2: TEAM RANKINGS
// ========================================

/**
 * Get team conference and D1 rankings for all stat categories
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with rankings for each stat category
 * @customfunction
 */
function GET_TEAM_RANKINGS(url) {
  return CBBData.GET_TEAM_RANKINGS(url);
}

// ========================================
// CATEGORY 3: TEAM AGGREGATED SEASON STATS
// ========================================

/**
 * Get aggregated team season statistics including team vs opponent stats
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with comprehensive team season statistics
 * @customfunction
 */
function GET_TEAM_SEASON_STATS(url) {
  return CBBData.GET_TEAM_SEASON_STATS(url);
}

/**
 * Get quadrant records (Q1-Q4) with wins, losses, and opponents
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with quadrant records for all 4 quadrants
 * @customfunction
 */
function GET_QUADRANT_RECORDS(url) {
  return CBBData.GET_QUADRANT_RECORDS(url);
}

// ========================================
// CATEGORY 4: TEAM GAME-BY-GAME STATS
// ========================================

/**
 * Get team game-by-game statistics with opponent stats
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with all games, team stats, and opponent stats
 * @customfunction
 */
function GET_TEAM_GAMES(url) {
  return CBBData.GET_TEAM_GAMES(url);
}

// ========================================
// CATEGORY 5: INDIVIDUAL PLAYERS - ALL DATA
// ========================================

/**
 * Get complete player roster with all season stats, rankings, and advanced metrics
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with all players and comprehensive statistics
 * @customfunction
 */
function GET_PLAYERS_FULL(url) {
  return CBBData.GET_PLAYERS_FULL(url);
}

// ========================================
// PLAYER GAME-BY-GAME LOG
// ========================================

/**
 * Get game-by-game statistics for a specific player
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {Array<Array>} Table with all games for the specified player
 * @customfunction
 */
function GET_PLAYER_GAMES(url, playerName) {
  return CBBData.GET_PLAYER_GAMES(url, playerName);
}

/**
 * Get player's most recent game statistics
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {Array<Array>} Table with the most recent game data
 * @customfunction
 */
function GET_PLAYER_LAST_GAME(url, playerName) {
  return CBBData.GET_PLAYER_LAST_GAME(url, playerName);
}

/**
 * Get player's most recent game as a compact summary string
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {string} Compact summary string of the last game
 * @customfunction
 */
function GET_PLAYER_LAST_GAME_SUMMARY(url, playerName) {
  return CBBData.GET_PLAYER_LAST_GAME_SUMMARY(url, playerName);
}

/**
 * Get player's previous season summary (most recent previous season)
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {string} Summary string of previous season stats
 * @customfunction
 */
function GET_PLAYER_PREVIOUS_SEASON_SUMMARY(url, playerName) {
  return CBBData.GET_PLAYER_PREVIOUS_SEASON_SUMMARY(url, playerName);
}

/**
 * Get player's last N games
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @param {number} n - Number of recent games to retrieve
 * @return {Array<Array>} Table with the last N games
 * @customfunction
 */
function GET_PLAYER_LAST_N_GAMES(url, playerName, n) {
  return CBBData.GET_PLAYER_LAST_N_GAMES(url, playerName, n);
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Generic data getter - returns JSON data or a specific path value
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} path - Optional dot-notation path to specific data (e.g., "team", "players.0.name")
 * @return {string|Object} JSON string if no path, or the value at the specified path
 * @customfunction
 */
function GET_DATA(url, path) {
  return CBBData.GET_DATA(url, path);
}

/**
 * Get specific player stat by path
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @param {string} statPath - Dot-notation path to the stat (e.g., "seasonTotals.points", "seasonTotals.ppg")
 * @return {*} The value of the specified stat
 * @customfunction
 */
function GET_PLAYER_STAT(url, playerName, statPath) {
  return CBBData.GET_PLAYER_STAT(url, playerName, statPath);
}

/**
 * Get list of all player names
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with list of all player names
 * @customfunction
 */
function GET_PLAYERS(url) {
  return CBBData.GET_PLAYERS(url);
}

// ========================================
// PLAYER CAREER HISTORY (Previous Seasons)
// ========================================

/**
 * Get player's career history across previous seasons
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {Array<Array>} Table with previous seasons' statistics
 * @customfunction
 */
function GET_PLAYER_CAREER(url, playerName) {
  return CBBData.GET_PLAYER_CAREER(url, playerName);
}

/**
 * Get complete career overview including current and previous seasons
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} playerName - Name of the player (case-insensitive)
 * @return {Array<Array>} Table with all seasons (previous + current)
 * @customfunction
 */
function GET_PLAYER_FULL_CAREER(url, playerName) {
  return CBBData.GET_PLAYER_FULL_CAREER(url, playerName);
}

/**
 * Get career history for all players in one table
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with all players' career histories
 * @customfunction
 */
function GET_ALL_PLAYERS_CAREERS(url) {
  return CBBData.GET_ALL_PLAYERS_CAREERS(url);
}

// ========================================
// DEBUG FUNCTION
// ========================================

/**
 * Debug function to check JSON structure and data availability
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Debug information about the JSON structure
 * @customfunction
 */
function DEBUG_JSON(url) {
  return CBBData.DEBUG_JSON(url);
}

// ========================================
// CATEGORY: KENPOM DATA
// ========================================

/**
 * Get full KenPom report table with all categories
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with all KenPom categories and statistics
 * @customfunction
 */
function GET_KENPOM_REPORT_TABLE(url) {
  return CBBData.GET_KENPOM_REPORT_TABLE(url);
}

/**
 * Get specific KenPom category data
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @param {string} categoryName - Name of the category (e.g., "Adj. Efficiency", "Adj. Tempo", "Effective FG%")
 * @return {Array<Array>} Table with category-specific data
 * @customfunction
 */
function GET_KENPOM_CATEGORY(url, categoryName) {
  return CBBData.GET_KENPOM_CATEGORY(url, categoryName);
}

/**
 * Get KenPom Adj. Efficiency (most commonly requested stat)
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with Adj. Efficiency offense, defense, and rankings
 * @customfunction
 */
function GET_KENPOM_ADJ_EFFICIENCY(url) {
  return CBBData.GET_KENPOM_ADJ_EFFICIENCY(url);
}

/**
 * Get KenPom Adj. Tempo
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with Adj. Tempo combined value, ranking, and D-I avg
 * @customfunction
 */
function GET_KENPOM_ADJ_TEMPO(url) {
  return CBBData.GET_KENPOM_ADJ_TEMPO(url);
}

/**
 * Get KenPom Four Factors (Effective FG%, Turnover %, Off. Reb. %, FTA/FGA)
 * @param {string} url - URL to the JSON data file (typically in cell A1)
 * @return {Array<Array>} Table with all Four Factors statistics
 * @customfunction
 */
function GET_KENPOM_FOUR_FACTORS(url) {
  return CBBData.GET_KENPOM_FOUR_FACTORS(url);
}

// ========================================
// TEST FUNCTION
// ========================================

/**
 * Test function to verify library is working correctly
 * Returns a simple table with test values - no parameters needed
 * @return {Array<Array>} Test table with sample data
 * @customfunction
 */
function TEST_FUNCTION() {
  return CBBData.TEST_FUNCTION();
}
