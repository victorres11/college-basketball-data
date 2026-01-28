#!/usr/bin/env node
/**
 * CBB Data Sheet Generator (ShaqDieselBot)
 * 
 * Usage: node generate-sheet.js <team-name> <user-email> <telegram-chat-id>
 * 
 * Steps:
 * 1. Fetch roster from CBB API
 * 2. Duplicate template sheet
 * 3. Rename new sheet
 * 4. Copy roster data
 * 5. Share with user (writer permissions)
 * 6. Return sheet URL
 * 
 * Sends Telegram notification on completion or error only.
 */

const { google } = require('googleapis');
const fs = require('fs');
const https = require('https');
const path = require('path');

const MASTER_TEMPLATE_ID = '1Bq3S1HKhWKn0WZ7Yg0G7zQmqqNk0rG1H1WXT3xnGcR0';
const API_BASE = 'https://cbb-data-generator.onrender.com';

// Load Telegram config
const telegramConfig = JSON.parse(fs.readFileSync(path.join(__dirname, '../config/telegram.json')));
const TELEGRAM_BOT_TOKEN = telegramConfig.botToken;

// Shaq-style status messages
const SHAQ_STATUS_MESSAGES = [
  "🏀 Still cookin' that data, baby! The Big Diesel don't rush greatness!",
  "🔥 Processing like Shaq in the paint — DOMINANT but takes time!",
  "💪 Hang tight! I'm working harder than Hack-a-Shaq defense!",
  "🍗 Barbecue chicken! Almost ready to serve up that data sheet!",
  "⏳ The Big Aristotle is thinking... data incoming soon!",
  "🎯 Like my free throws... it takes a minute, but we get there!"
];

// Send Telegram message
function sendTelegram(chatId, message) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML'
    });
    
    const options = {
      hostname: 'api.telegram.org',
      path: `/bot${TELEGRAM_BOT_TOKEN}/sendMessage`,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };
    
    const req = https.request(options, (res) => {
      let resData = '';
      res.on('data', chunk => resData += chunk);
      res.on('end', () => {
        try {
          const parsed = JSON.parse(resData);
          if (parsed.ok) {
            resolve(parsed);
          } else {
            reject(new Error(parsed.description || 'Telegram API error'));
          }
        } catch (e) {
          reject(new Error('Invalid Telegram response'));
        }
      });
    });
    
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Get random Shaq status message
function getShaqStatus() {
  return SHAQ_STATUS_MESSAGES[Math.floor(Math.random() * SHAQ_STATUS_MESSAGES.length)];
}

// Helper: POST JSON
function postJSON(url, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      }
    };
    
    const req = https.request(options, (res) => {
      let resData = '';
      res.on('data', chunk => resData += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(resData));
        } catch (e) {
          reject(new Error('Invalid JSON response: ' + resData));
        }
      });
    });
    
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// Helper: GET JSON
function getJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch (e) {
          reject(new Error('Invalid JSON response'));
        }
      });
    }).on('error', reject);
  });
}

// Helper: Sleep
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Main workflow
async function generateSheet(teamName, userEmail, chatId) {
  const startTime = Date.now();
  console.log(`🔄 Step 1: Triggering data generation for ${teamName}...`);
  
  // Trigger API generate
  const generateResp = await postJSON(`${API_BASE}/api/generate`, { 
    team_name: teamName,
    notify_email: userEmail 
  });
  
  if (generateResp.error) {
    throw new Error(generateResp.error);
  }
  
  const jobId = generateResp.job_id;
  console.log(`✅ Job started: ${jobId}`);
  
  // Poll for completion
  console.log('🔄 Step 2: Waiting for data generation...');
  let status;
  let attempts = 0;
  const maxAttempts = 120; // 10 minutes max
  
  while (attempts < maxAttempts) {
    status = await getJSON(`${API_BASE}/api/status/${jobId}`);
    
    if (status.status === 'completed') {
      console.log(`✅ Data generated successfully`);
      break;
    } else if (status.status === 'failed') {
      throw new Error(status.error || 'Generation failed');
    }
    
    // Console status update every 30 seconds
    if (attempts % 6 === 0) {
      console.log(`📢 STATUS UPDATE: Still processing data for ${teamName}. Estimated wait time: ${Math.round((maxAttempts - attempts) * 5 / 60)} minutes remaining...`);
    }
    
    await sleep(5000); // Wait 5 seconds
    attempts++;
  }
  
  if (attempts >= maxAttempts) {
    if (chatId) {
      await sendTelegram(chatId, `❌ Aw man! The ${teamName} data generation timed out. Hit me up again and we'll try one more time, baby!`);
    }
    throw new Error('Generation timed out');
  }
  
  const dataUrl = status.url;
  console.log(`📊 Data URL: ${dataUrl}`);
  
  if (!dataUrl) {
    throw new Error('No data URL returned from API');
  }
  
  // Load Google credentials
  const credentials = JSON.parse(fs.readFileSync('../config/gcp-oauth.keys.json'));
  const token = JSON.parse(fs.readFileSync('../config/sheets_token.json'));
  
  const oauth2Client = new google.auth.OAuth2(
    credentials.installed.client_id,
    credentials.installed.client_secret,
    credentials.installed.redirect_uris[0]
  );
  
  oauth2Client.setCredentials(token);
  
  const drive = google.drive({ version: 'v3', auth: oauth2Client });
  const sheets = google.sheets({ version: 'v4', auth: oauth2Client });
  
  // Step 3: Duplicate master template
  console.log('🔄 Step 3: Duplicating master template...');
  
  const today = new Date().toISOString().split('T')[0];
  const newSheetName = `SENECA - ${teamName} - ${today}`;
  
  const copyResponse = await drive.files.copy({
    fileId: MASTER_TEMPLATE_ID,
    requestBody: {
      name: newSheetName
    }
  });
  
  const newSheetId = copyResponse.data.id;
  console.log(`✅ Created: ${newSheetName}`);
  console.log(`   ID: ${newSheetId}`);
  
  // Step 4: Update _PLAYERS_RAW!A1 with data URL
  console.log('🔄 Step 4: Setting data URL in _PLAYERS_RAW...');
  
  await sheets.spreadsheets.values.update({
    spreadsheetId: newSheetId,
    range: '_PLAYERS_RAW!A1',
    valueInputOption: 'RAW',
    requestBody: {
      values: [[dataUrl]]
    }
  });
  
  console.log(`✅ Data URL set`);
  
  // Step 5: Wait for IMPORTDATA to resolve with retry loop
  console.log('🔄 Step 5: Waiting for IMPORTDATA to resolve...');
  const maxRetries = 20; // 20 * 3s = 60 seconds max
  let importResolved = false;
  
  for (let retry = 1; retry <= maxRetries; retry++) {
    await sleep(3000);
    console.log(`   Retry ${retry}/${maxRetries}: Checking _PLAYERS_RAW for data...`);
    
    const checkData = await sheets.spreadsheets.values.get({
      spreadsheetId: newSheetId,
      range: '_PLAYERS_RAW!A3:A10'
    });
    
    const checkValues = checkData.data.values || [];
    const hasData = checkValues.some(row => row && row[0] && row[0].toString().trim() !== '');
    
    if (hasData) {
      console.log(`✅ IMPORTDATA resolved after ${retry * 3} seconds`);
      importResolved = true;
      break;
    }
  }
  
  if (!importResolved) {
    throw new Error('IMPORTDATA did not resolve after 60 seconds — _PLAYERS_RAW is still empty');
  }
  
  console.log('🔄 Step 6: Copying roster as values...');
  
  // Read from _PLAYERS_RAW (source)
  const sourceData = await sheets.spreadsheets.values.get({
    spreadsheetId: newSheetId,
    range: '_PLAYERS_RAW!A3:CQ21'
  });
  
  const sourceValues = sourceData.data.values || [];
  
  // Find last row with data
  let lastDataRow = 0;
  for (let i = 0; i < sourceValues.length; i++) {
    if (sourceValues[i] && sourceValues[i][0]) {
      lastDataRow = i;
    }
  }
  
  const rowsToCopy = lastDataRow + 1;
  
  if (rowsToCopy === 0) {
    throw new Error('rowsToCopy is 0 — IMPORTDATA appeared to resolve but no player rows found in A3:CQ21');
  }
  
  // Clear destination first
  await sheets.spreadsheets.values.clear({
    spreadsheetId: newSheetId,
    range: 'GET_PLAYERS_FULL!A24:CQ44'
  });
  
  // Copy data as values
  const dataToCopy = sourceValues.slice(0, rowsToCopy);
  await sheets.spreadsheets.values.update({
    spreadsheetId: newSheetId,
    range: 'GET_PLAYERS_FULL!A24',
    valueInputOption: 'RAW',
    requestBody: {
      values: dataToCopy
    }
  });
  
  console.log(`✅ Copied ${rowsToCopy} rows (header + ${rowsToCopy - 1} players) as values`);
  
  // Step 7: Share with user (writer permissions)
  console.log(`🔄 Step 7: Sharing with ${userEmail}...`);
  
  await drive.permissions.create({
    fileId: newSheetId,
    requestBody: {
      type: 'user',
      role: 'writer',
      emailAddress: userEmail
    },
    sendNotificationEmail: true
  });
  
  console.log('✅ Sheet shared with full edit permissions');
  
  // Return URL
  const sheetUrl = `https://docs.google.com/spreadsheets/d/${newSheetId}`;
  
  console.log('');
  console.log('='.repeat(80));
  console.log('🎉 Sheet created successfully!');
  console.log(`🔗 ${sheetUrl}`);
  console.log('='.repeat(80));
  
  // Track timing
  const endTime = Date.now();
  const durationSeconds = Math.round((endTime - startTime) / 1000);
  const durationMinutes = (durationSeconds / 60).toFixed(1);
  
  console.log(`⏱️  Total time: ${durationMinutes} minutes (${durationSeconds}s)`);
  
  // Save timing to memory
  const timingsPath = path.join(__dirname, '../memory/timings.json');
  let timings = { runs: [] };
  
  try {
    if (fs.existsSync(timingsPath)) {
      timings = JSON.parse(fs.readFileSync(timingsPath));
    }
  } catch (e) {
    console.log('⚠️  Could not load existing timings, creating new file');
  }
  
  timings.runs.push({
    team: teamName,
    timestamp: new Date().toISOString(),
    durationSeconds,
    durationMinutes: parseFloat(durationMinutes)
  });
  
  // Keep last 50 runs
  if (timings.runs.length > 50) {
    timings.runs = timings.runs.slice(-50);
  }
  
  // Calculate average
  const avgSeconds = timings.runs.reduce((sum, r) => sum + r.durationSeconds, 0) / timings.runs.length;
  const avgMinutes = (avgSeconds / 60).toFixed(1);
  timings.averageSeconds = Math.round(avgSeconds);
  timings.averageMinutes = parseFloat(avgMinutes);
  timings.totalRuns = timings.runs.length;
  
  fs.writeFileSync(timingsPath, JSON.stringify(timings, null, 2));
  console.log(`📊 Average time over ${timings.totalRuns} runs: ${avgMinutes} minutes`);
  
  // Send completion message via Telegram
  if (chatId) {
    const completionMsg = `🏆 BOOM! KAZAAM! 🏆\n\nYour ${teamName} data sheet is READY, baby! The Big Data Diesel delivered!\n\n🔗 ${sheetUrl}\n\n✅ Full edit access granted\n📧 Also shared to ${userEmail}\n\n⏱️ Done in ${durationMinutes} min (avg: ${avgMinutes} min over ${timings.totalRuns} runs)\n\nRings, Erneh! 🏀💍`;
    try {
      await sendTelegram(chatId, completionMsg);
      console.log(`✅ Completion message sent to ${chatId}`);
    } catch (e) {
      console.log(`⚠️ Failed to send completion message: ${e.message}`);
    }
  }
  
  return sheetUrl;
}

// CLI entry point
if (require.main === module) {
  const [teamName, userEmail, chatId] = process.argv.slice(2);
  
  if (!teamName || !userEmail) {
    console.error('Usage: node generate-sheet.js <team-name> <user-email> [telegram-chat-id]');
    process.exit(1);
  }
  
  generateSheet(teamName, userEmail, chatId)
    .catch(async (err) => {
      console.error('❌ Error:', err.message);
      // Send error notification if chatId provided
      if (chatId) {
        try {
          await sendTelegram(chatId, `❌ Aw man! Something went wrong with your ${teamName} sheet: ${err.message}\n\nTry again, baby — even Shaq missed free throws sometimes! 🏀`);
        } catch (e) {
          console.error('Failed to send error notification:', e.message);
        }
      }
      process.exit(1);
    });
}

module.exports = { generateSheet };
