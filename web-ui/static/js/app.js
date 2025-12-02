let teams = [];
let selectedTeam = null;

// Load teams on page load
window.addEventListener('DOMContentLoaded', () => {
    loadTeams();
    setupSearch();
});

function loadTeams() {
    console.log('Loading teams...');
    fetch('/api/teams')
        .then(res => {
            console.log('Response status:', res.status);
            if (!res.ok) {
                return res.json().then(data => {
                    throw new Error(data.error || `HTTP ${res.status}`);
                });
            }
            return res.json();
        })
        .then(data => {
            console.log('Teams data received:', data.length, 'teams');
            if (data.error) {
                console.error('Error loading teams:', data.error);
                alert('Failed to load teams: ' + data.error);
                return;
            }
            if (!Array.isArray(data) || data.length === 0) {
                console.warn('No teams received');
                alert('No teams found. Please check the server logs.');
                return;
            }
            teams = data;
            console.log('Teams loaded successfully:', teams.length);
        })
        .catch(err => {
            console.error('Error fetching teams:', err);
            alert('Failed to load teams: ' + err.message);
        });
}

function setupSearch() {
    const searchInput = document.getElementById('team-search');
    const select = document.getElementById('team-select');
    const selectedDiv = document.getElementById('selected-team');
    const selectedName = document.getElementById('selected-team-name');
    
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        if (query.length === 0) {
            select.style.display = 'none';
            selectedDiv.style.display = 'none';
            selectedTeam = null;
            return;
        }
        
        // Check if teams are loaded
        if (!teams || teams.length === 0) {
            console.warn('Teams not loaded yet');
            searchInput.placeholder = 'Loading teams...';
            return;
        }
        
        const filtered = teams.filter(t => 
            t.name && t.name.toLowerCase().includes(query)
        ).slice(0, 20); // Show top 20 matches
        
        console.log(`Found ${filtered.length} teams matching "${query}"`);
        
        if (filtered.length > 0) {
            select.innerHTML = filtered.map(t => 
                `<option value="${t.id}">${t.name}</option>`
            ).join('');
            select.style.display = 'block';
        } else {
            select.style.display = 'none';
            console.log('No teams found matching query');
        }
    });
    
    select.addEventListener('change', (e) => {
        selectedTeam = teams.find(t => t.id == e.target.value);
        if (selectedTeam) {
            searchInput.value = selectedTeam.name;
            select.style.display = 'none';
            selectedDiv.style.display = 'block';
            selectedName.textContent = selectedTeam.name;
        }
    });
    
    // Hide dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !select.contains(e.target)) {
            select.style.display = 'none';
        }
    });
}

function generateData() {
    if (!selectedTeam) {
        alert('Please select a team from the dropdown');
        return;
    }
    
    // Fixed to 2026 season
    const season = 2026;
    const btn = document.getElementById('generate-btn');
    const status = document.getElementById('status');
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    
    // Reset UI
    btn.disabled = true;
    if (status) status.style.display = 'block';
    if (result) result.style.display = 'none';
    if (error) error.style.display = 'none';
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    if (progressBar) progressBar.style.width = '0%';
    if (progressText) progressText.textContent = '0%';
    
    // Start generation
    fetch('/api/generate', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            team_name: selectedTeam.name,
            season: season
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
            btn.disabled = false;
            return;
        }
        const jobId = data.job_id;
        pollStatus(jobId);
    })
    .catch(err => {
        showError('Failed to start generation: ' + err.message);
        btn.disabled = false;
    });
}

function pollStatus(jobId) {
    let isCompleted = false; // Flag to prevent race conditions
    const interval = setInterval(() => {
        // Don't poll if already completed
        if (isCompleted) {
            clearInterval(interval);
            return;
        }
        
        fetch(`/api/status/${jobId}`)
            .then(res => {
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                // Don't process if already completed
                if (isCompleted) {
                    return;
                }
                
                if (data.error) {
                    clearInterval(interval);
                    isCompleted = true;
                    showError(data.error);
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                    return;
                }
                
                // Update status message (with null check)
                const statusMessage = document.getElementById('status-message');
                if (statusMessage && data.message) {
                    statusMessage.textContent = data.message;
                }
                
                // Update progress (with null checks)
                const progress = data.progress || 0;
                const progressBar = document.getElementById('progress-bar');
                const progressText = document.getElementById('progress-text');
                if (progressBar) {
                    progressBar.style.width = progress + '%';
                }
                if (progressText) {
                    progressText.textContent = progress + '%';
                }
                
                // Update status table if available
                updateStatusTable(data.status || []);
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    isCompleted = true;
                    showResult(data.url, data.gameDates || []);
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    isCompleted = true;
                    showError(data.error || 'Generation failed');
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                }
            })
            .catch(err => {
                // Only show error if not already completed
                if (!isCompleted) {
                    clearInterval(interval);
                    isCompleted = true;
                    const errorMsg = err.message || String(err);
                    showError('Failed to check status: ' + errorMsg);
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                }
            });
    }, 2000); // Poll every 2 seconds
}

function showResult(url, gameDates) {
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const resultUrl = document.getElementById('result-url');
    const gameList = document.getElementById('game-list');
    const gameCount = document.getElementById('game-count');
    const statusMessage = document.getElementById('status-message');
    
    if (error) error.style.display = 'none';
    if (result) result.style.display = 'block';
    if (statusMessage && statusMessage.textContent !== 'Complete!') {
        statusMessage.textContent = 'Complete!';
    }
    if (resultUrl && url) {
        // Clean the URL - trim whitespace and ensure it's a valid URL
        const cleanUrl = url.trim();
        resultUrl.href = cleanUrl;
        resultUrl.textContent = cleanUrl;
    }
    
    // Display game dates
    if (gameDates && gameDates.length > 0) {
        if (gameCount) gameCount.textContent = gameDates.length;
        if (gameList) {
            // Build table with proper structure
            let tableHTML = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em;">';
            tableHTML += '<thead>';
            tableHTML += '<tr style="background-color: #f5f5f5;">';
            tableHTML += '<th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; font-weight: 600;">Date</th>';
            tableHTML += '<th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; font-weight: 600;">Opponent</th>';
            tableHTML += '<th style="text-align: left; padding: 10px; border-bottom: 2px solid #ddd; font-weight: 600;">Type</th>';
            tableHTML += '</tr>';
            tableHTML += '</thead>';
            tableHTML += '<tbody>';
            
            gameDates.forEach((game, index) => {
                const type = game.conferenceGame ? 'Conference' : 'Non-Conference';
                const location = game.isHome ? ' (Home)' : ' (Away)';
                const rowColor = index % 2 === 0 ? '#ffffff' : '#fafafa';
                tableHTML += `<tr style="background-color: ${rowColor};">`;
                tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee;">${game.date}</td>`;
                tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee;">${game.opponent}${location}</td>`;
                tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee;">${type}</td>`;
                tableHTML += '</tr>';
            });
            
            tableHTML += '</tbody>';
            tableHTML += '</table>';
            gameList.innerHTML = tableHTML;
        }
    } else {
        if (gameCount) gameCount.textContent = '0';
        if (gameList) gameList.innerHTML = '<p style="color: #666; font-style: italic; margin-top: 10px;">No games detected in the data.</p>';
    }
}

function showError(message) {
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('error-message');
    
    if (result) result.style.display = 'none';
    if (error) error.style.display = 'block';
    if (errorMessage) errorMessage.textContent = message;
}

function updateStatusTable(statusList) {
    const container = document.getElementById('status-table-container');
    const tableDiv = document.getElementById('status-table');
    
    if (!container || !tableDiv) return;
    
    if (!statusList || statusList.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    // Build table HTML
    let tableHTML = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 0.9em; background-color: #fff; border: 1px solid #ddd; border-radius: 4px;">';
    tableHTML += '<thead>';
    tableHTML += '<tr style="background-color: #f5f5f5;">';
    tableHTML += '<th style="text-align: left; padding: 12px; border-bottom: 2px solid #ddd; font-weight: 600; width: 40%;">Data Source</th>';
    tableHTML += '<th style="text-align: center; padding: 12px; border-bottom: 2px solid #ddd; font-weight: 600; width: 15%;">Status</th>';
    tableHTML += '<th style="text-align: left; padding: 12px; border-bottom: 2px solid #ddd; font-weight: 600; width: 45%;">Details</th>';
    tableHTML += '</tr>';
    tableHTML += '</thead>';
    tableHTML += '<tbody>';
    
    statusList.forEach((item, index) => {
        const status = item.status || 'pending';
        const name = item.name || 'Unknown';
        const message = item.message || '';
        const details = item.details || '';
        
        // Determine status color and icon
        let statusColor = '#666';
        let statusIcon = '⏳';
        let statusText = 'Pending';
        
        if (status === 'success') {
            statusColor = '#2e7d32';
            statusIcon = '✅';
            statusText = 'Success';
        } else if (status === 'failed') {
            statusColor = '#c62828';
            statusIcon = '❌';
            statusText = 'Failed';
        } else if (status === 'skipped') {
            statusColor = '#f57c00';
            statusIcon = '⏭️';
            statusText = 'Skipped';
        }
        
        const rowColor = index % 2 === 0 ? '#ffffff' : '#fafafa';
        tableHTML += `<tr style="background-color: ${rowColor};">`;
        tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee; font-weight: 500;">${name}</td>`;
        tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center; color: ${statusColor}; font-weight: 600;">${statusIcon} ${statusText}</td>`;
        tableHTML += `<td style="padding: 10px; border-bottom: 1px solid #eee; color: #666; font-size: 0.9em;">${message || details || '—'}</td>`;
        tableHTML += '</tr>';
    });
    
    tableHTML += '</tbody>';
    tableHTML += '</table>';
    
    tableDiv.innerHTML = tableHTML;
}

function copyUrlToClipboard() {
    const resultUrl = document.getElementById('result-url');
    const copyFeedback = document.getElementById('copy-feedback');
    const copyBtn = document.getElementById('copy-url-btn');
    
    if (!resultUrl || !resultUrl.href || resultUrl.href === '#') {
        if (copyFeedback) {
            copyFeedback.textContent = '❌ No URL available to copy';
            copyFeedback.style.color = '#c62828';
            copyFeedback.style.display = 'block';
            setTimeout(() => {
                copyFeedback.style.display = 'none';
            }, 3000);
        }
        return;
    }
    
    // Get the URL and trim any whitespace
    const url = resultUrl.href.trim();
    
    // Use the Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(() => {
            // Show success feedback
            if (copyFeedback) {
                copyFeedback.textContent = '✅ URL copied to clipboard!';
                copyFeedback.style.color = '#2e7d32';
                copyFeedback.style.display = 'block';
            }
            if (copyBtn) {
                copyBtn.textContent = '✅ Copied!';
                copyBtn.style.backgroundColor = '#2e7d32';
                setTimeout(() => {
                    copyBtn.textContent = '📋 Copy URL';
                    copyBtn.style.backgroundColor = '#667eea';
                }, 2000);
            }
            // Hide feedback after 3 seconds
            setTimeout(() => {
                if (copyFeedback) copyFeedback.style.display = 'none';
            }, 3000);
        }).catch(err => {
            // Fallback for older browsers
            fallbackCopyTextToClipboard(url);
        });
    } else {
        // Fallback for browsers that don't support Clipboard API
        fallbackCopyTextToClipboard(url);
    }
}

function fallbackCopyTextToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        const copyFeedback = document.getElementById('copy-feedback');
        const copyBtn = document.getElementById('copy-url-btn');
        
        if (successful) {
            if (copyFeedback) {
                copyFeedback.textContent = '✅ URL copied to clipboard!';
                copyFeedback.style.color = '#2e7d32';
                copyFeedback.style.display = 'block';
            }
            if (copyBtn) {
                copyBtn.textContent = '✅ Copied!';
                copyBtn.style.backgroundColor = '#2e7d32';
                setTimeout(() => {
                    copyBtn.textContent = '📋 Copy URL';
                    copyBtn.style.backgroundColor = '#667eea';
                }, 2000);
            }
            setTimeout(() => {
                if (copyFeedback) copyFeedback.style.display = 'none';
            }, 3000);
        } else {
            throw new Error('Copy command failed');
        }
    } catch (err) {
        const copyFeedback = document.getElementById('copy-feedback');
        if (copyFeedback) {
            copyFeedback.textContent = '❌ Failed to copy. Please copy manually.';
            copyFeedback.style.color = '#c62828';
            copyFeedback.style.display = 'block';
        }
    } finally {
        document.body.removeChild(textArea);
    }
}

