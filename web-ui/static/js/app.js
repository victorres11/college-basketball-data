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
    status.style.display = 'block';
    result.style.display = 'none';
    error.style.display = 'none';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('progress-text').textContent = '0%';
    
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
    const interval = setInterval(() => {
        fetch(`/api/status/${jobId}`)
            .then(res => res.json())
            .then(data => {
                if (data.error) {
                    clearInterval(interval);
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
                
                if (data.status === 'completed') {
                    clearInterval(interval);
                    showResult(data.url, data.gameDates || []);
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                } else if (data.status === 'failed') {
                    clearInterval(interval);
                    showError(data.error || 'Generation failed');
                    const btn = document.getElementById('generate-btn');
                    if (btn) btn.disabled = false;
                }
            })
            .catch(err => {
                clearInterval(interval);
                showError('Failed to check status: ' + err.message);
                const btn = document.getElementById('generate-btn');
                if (btn) btn.disabled = false;
            });
    }, 2000); // Poll every 2 seconds
}

function showResult(url, gameDates) {
    const result = document.getElementById('result');
    const error = document.getElementById('error');
    const resultUrl = document.getElementById('result-url');
    const gameList = document.getElementById('game-list');
    const gameCount = document.getElementById('game-count');
    
    if (error) error.style.display = 'none';
    if (result) result.style.display = 'block';
    if (resultUrl) {
        resultUrl.href = url;
        resultUrl.textContent = url;
    }
    
    // Display game dates
    if (gameDates && gameDates.length > 0) {
        if (gameCount) gameCount.textContent = gameDates.length;
        if (gameList) {
            gameList.innerHTML = '<table style="width: 100%; border-collapse: collapse;"><thead><tr><th style="text-align: left; padding: 5px; border-bottom: 1px solid #ddd;">Date</th><th style="text-align: left; padding: 5px; border-bottom: 1px solid #ddd;">Opponent</th><th style="text-align: left; padding: 5px; border-bottom: 1px solid #ddd;">Type</th></tr></thead><tbody>';
            
            gameDates.forEach(game => {
                const type = game.conferenceGame ? 'Conference' : 'Non-Conference';
                const location = game.isHome ? ' (Home)' : ' (Away)';
                gameList.innerHTML += `<tr><td style="padding: 5px; border-bottom: 1px solid #eee;">${game.date}</td><td style="padding: 5px; border-bottom: 1px solid #eee;">${game.opponent}${location}</td><td style="padding: 5px; border-bottom: 1px solid #eee;">${type}</td></tr>`;
            });
            
            gameList.innerHTML += '</tbody></table>';
        }
    } else {
        if (gameCount) gameCount.textContent = '0';
        if (gameList) gameList.innerHTML = '<p style="color: #666; font-style: italic;">No games detected in the data.</p>';
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

