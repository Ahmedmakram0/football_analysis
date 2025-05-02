// Global variables to store match data
let matchData = null;
let selectedPlayer = null;

// DOM Elements
const elements = {
    matchSelector: document.getElementById('match-selector'),
    analyzeBtn: document.getElementById('analyze-btn'),
    fileUpload: document.getElementById('file-upload'),
    loading: document.getElementById('loading'),
    results: document.getElementById('results'),
    
    // Match overview
    homeTeamName: document.getElementById('home-team-name'),
    awayTeamName: document.getElementById('away-team-name'),
    homeFormation: document.getElementById('home-formation'),
    awayFormation: document.getElementById('away-formation'),
    homeScore: document.getElementById('home-score'),
    awayScore: document.getElementById('away-score'),
    
    // Stats
    possessionHome: document.getElementById('possession-home'),
    possessionAway: document.getElementById('possession-away'),
    possessionHomeValue: document.getElementById('possession-home-value'),
    possessionAwayValue: document.getElementById('possession-away-value'),
    shotsHome: document.getElementById('shots-home'),
    shotsAway: document.getElementById('shots-away'),
    xgHome: document.getElementById('xg-home'),
    xgAway: document.getElementById('xg-away'),
    passesHome: document.getElementById('passes-home'),
    passesAway: document.getElementById('passes-away'),
    passCompletionHome: document.getElementById('pass-completion-home'),
    passCompletionAway: document.getElementById('pass-completion-away'),
    
    // Visualizations
    matchVisualization: document.getElementById('match-visualization'),
    homeShotMap: document.getElementById('home-shot-map'),
    awayShotMap: document.getElementById('away-shot-map'),
    playerHeatmap: document.getElementById('position-heatmap'),
    playerHeatmapTitle: document.getElementById('heatmap-title'),
    playerSelector: document.getElementById('player-selector'),
    
    // Player stats
    homeSummary: document.getElementById('home-summary'),
    awaySummary: document.getElementById('away-summary'),
    homePlayersTable: document.getElementById('home-players-table'),
    awayPlayersTable: document.getElementById('away-players-table')
};

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Initialize tab switching for visualization sections
    initializeTabs();
    
    // Initialize team tabs
    initializeTeamTabs();
    
    // Load available JSON files
    loadAvailableFiles();
    
    // Initialize the analyze button
    elements.analyzeBtn.addEventListener('click', analyzeMatch);
    
    // Initialize file upload
    elements.fileUpload.addEventListener('change', handleFileUpload);
    
    // Initialize player selector
    if (elements.playerSelector) {
        elements.playerSelector.addEventListener('change', handlePlayerSelection);
    }
});

// Initialize tab switching
function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons
            tabButtons.forEach(btn => btn.classList.remove('active'));
            
            // Add active class to current button
            button.classList.add('active');
            
            // Hide all tab contents
            tabContents.forEach(content => content.classList.add('hidden'));
            
            // Show the selected tab content
            const tabId = button.getAttribute('data-tab');
            document.getElementById(tabId).classList.remove('hidden');
        });
    });
}

// Initialize team tabs
function initializeTeamTabs() {
    const teamTabs = document.querySelectorAll('.team-tab');
    const teamPanes = document.querySelectorAll('.team-pane');
    
    teamTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            teamTabs.forEach(t => t.classList.remove('active'));
            
            // Add active class to current tab
            tab.classList.add('active');
            
            // Hide all team content
            teamPanes.forEach(pane => pane.classList.add('hidden'));
            
            // Show the selected team content
            const team = tab.getAttribute('data-team');
            document.getElementById(`${team}-team-stats`).classList.remove('hidden');
        });
    });
}

// Load available JSON files from the server
async function loadAvailableFiles() {
    try {
        const response = await fetch('/list-files');
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Clear existing options
        elements.matchSelector.innerHTML = '';
        
        // Add options for each available file
        if (data.files && data.files.length > 0) {
            data.files.forEach(file => {
                const option = document.createElement('option');
                option.value = file;
                option.textContent = `Match ${file.split('/').pop().split('.')[0]}`;
                elements.matchSelector.appendChild(option);
            });
            
            // Enable the analyze button
            elements.analyzeBtn.disabled = false;
        } else {
            // If no files available, add a placeholder option
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No files available';
            option.disabled = true;
            option.selected = true;
            elements.matchSelector.appendChild(option);
            
            // Disable the analyze button
            elements.analyzeBtn.disabled = true;
        }
    } catch (error) {
        console.error('Error loading available files:', error);
        
        // Add a placeholder option
        const option = document.createElement('option');
        option.value = '';
        option.textContent = 'Error loading files';
        option.disabled = true;
        option.selected = true;
        elements.matchSelector.appendChild(option);
    }
}

// Handle file upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Show loading indicator
    elements.loading.classList.remove('hidden');
    elements.results.classList.add('hidden');
    
    try {
        // Create a FormData object to send the file to the server
        const formData = new FormData();
        formData.append('file', file);
        
        // Send the file to the server for analysis
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Get the file path from the server response
        const filePath = result.file_path;
        
        // Reload available files to update the dropdown
        await loadAvailableFiles();
        
        // Select the newly added file
        elements.matchSelector.value = filePath;
        
        // Analyze the uploaded file
        await analyzeMatchFile(filePath);
        
    } catch (error) {
        console.error('Error uploading file:', error);
        alert(`Error uploading file: ${error.message}`);
        elements.loading.classList.add('hidden');
    }
}

// Main function to analyze a match
async function analyzeMatch() {
    try {
        // Show loading indicator
        elements.loading.classList.remove('hidden');
        elements.results.classList.add('hidden');
        
        // Reset the selected player
        selectedPlayer = null;
        
        // Get selected match file
        const matchFile = elements.matchSelector.value;
        
        // Analyze the selected file
        await analyzeMatchFile(matchFile);
        
    } catch (error) {
        console.error('Error analyzing match:', error);
        alert(`Error analyzing match: ${error.message}`);
        elements.loading.classList.add('hidden');
    }
}

// Handle player selection
async function handlePlayerSelection(event) {
    const playerName = event.target.value;
    selectedPlayer = playerName;
    
    if (playerName && matchData) {
        elements.loading.classList.remove('hidden');
        
        // Get the current match file
        const matchFile = elements.matchSelector.value;
        
        // Fetch player-specific heatmap
        await analyzeMatchFile(matchFile, playerName);
        
        elements.loading.classList.add('hidden');
    }
}

// Function to analyze a specific match file
async function analyzeMatchFile(matchFile, playerName = null) {
    try {
        // Construct URL with player name if provided
        let url = `/analyze?file=${encodeURIComponent(matchFile)}`;
        if (playerName) {
            url += `&player=${encodeURIComponent(playerName)}`;
        }
        
        // Fetch analysis results from the server
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        // Parse the JSON response
        matchData = await response.json();
        
        if (matchData.error) {
            throw new Error(matchData.error);
        }
        
        // Render the analysis results
        renderMatchData(matchData);
        
        // Hide loading indicator and show results
        elements.loading.classList.add('hidden');
        elements.results.classList.remove('hidden');
        
        // Update player selector if needed
        if (!playerName) {
            populatePlayerSelector(matchData);
        }
        
    } catch (error) {
        console.error('Error fetching analysis:', error);
        alert(`Error analyzing match: ${error.message}`);
        elements.loading.classList.add('hidden');
    }
}

// Populate player selector dropdown
function populatePlayerSelector(data) {
    if (!elements.playerSelector) return;
    
    // Clear existing options
    elements.playerSelector.innerHTML = '';
    
    // Add a default option
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Select a player';
    defaultOption.selected = true;
    elements.playerSelector.appendChild(defaultOption);
    
    // Add home team players
    const homeOptgroup = document.createElement('optgroup');
    homeOptgroup.label = data.match_details.home_team;
    
    data.home_player_stats.forEach(player => {
        const option = document.createElement('option');
        option.value = player.player_name;
        option.textContent = `${player.jersey} - ${player.player_name} (${player.position})`;
        homeOptgroup.appendChild(option);
    });
    
    elements.playerSelector.appendChild(homeOptgroup);
    
    // Add away team players
    const awayOptgroup = document.createElement('optgroup');
    awayOptgroup.label = data.match_details.away_team;
    
    data.away_player_stats.forEach(player => {
        const option = document.createElement('option');
        option.value = player.player_name;
        option.textContent = `${player.jersey} - ${player.player_name} (${player.position})`;
        awayOptgroup.appendChild(option);
    });
    
    elements.playerSelector.appendChild(awayOptgroup);
}

// Render match data to the UI
function renderMatchData(data) {
    // Make sure possession data sums to 100%
    if (data.match_stats.possession.away === 0) {
        data.match_stats.possession.away = 100 - data.match_stats.possession.home;
    }
    
    // Render match details
    elements.homeTeamName.textContent = data.match_details.home_team;
    elements.awayTeamName.textContent = data.match_details.away_team;
    elements.homeFormation.textContent = data.match_details.home_formation;
    elements.awayFormation.textContent = data.match_details.away_formation;
    
    // Render scores
    elements.homeScore.textContent = data.match_stats.goals.home;
    elements.awayScore.textContent = data.match_stats.goals.away;
    
    // Render stats
    // Possession
    const homePoss = data.match_stats.possession.home;
    const awayPoss = data.match_stats.possession.away;
    elements.possessionHome.style.width = `${homePoss}%`;
    elements.possessionAway.style.width = `${awayPoss}%`;
    elements.possessionHomeValue.textContent = `${homePoss}%`;
    elements.possessionAwayValue.textContent = `${awayPoss}%`;
    
    // Shots
    elements.shotsHome.textContent = data.match_stats.shots.home;
    elements.shotsAway.textContent = data.match_stats.shots.away;
    
    // xG
    elements.xgHome.textContent = data.match_stats.xg.home.toFixed(2);
    elements.xgAway.textContent = data.match_stats.xg.away.toFixed(2);
    
    // Passes
    elements.passesHome.textContent = data.match_stats.passes.home;
    elements.passesAway.textContent = data.match_stats.passes.away;
    
    // Pass completion
    elements.passCompletionHome.textContent = `${data.match_stats.passes.home_completion.toFixed(1)}%`;
    elements.passCompletionAway.textContent = `${data.match_stats.passes.away_completion.toFixed(1)}%`;
    
    // Render player summaries
    elements.homeSummary.textContent = data.home_summary || "No summary available.";
    elements.awaySummary.textContent = data.away_summary || "No summary available.";
    
    // Render player stats tables
    renderPlayerTable(elements.homePlayersTable, data.home_player_stats || []);
    renderPlayerTable(elements.awayPlayersTable, data.away_player_stats || []);
    
    // Render match visualization
    if (data.match_visualization) {
        elements.matchVisualization.src = `data:image/png;base64,${data.match_visualization}`;
    }
    
    // Render shot maps
    if (data.home_shot_map && elements.homeShotMap) {
        elements.homeShotMap.src = `data:image/png;base64,${data.home_shot_map}`;
    }
    
    if (data.away_shot_map && elements.awayShotMap) {
        elements.awayShotMap.src = `data:image/png;base64,${data.away_shot_map}`;
    }
    
    // Render player heatmap if available
    if (data.player_heatmap && elements.playerHeatmap) {
        elements.playerHeatmap.src = `data:image/png;base64,${data.player_heatmap}`;
        
        // Update heatmap title
        if (elements.playerHeatmapTitle && data.player_name) {
            elements.playerHeatmapTitle.textContent = `${data.player_name} - Position Heatmap`;
        }
    }
}

// Render player stats table
function renderPlayerTable(tableElement, players) {
    tableElement.innerHTML = '';
    
    players.forEach(player => {
        const row = document.createElement('tr');
        row.className = "hover:bg-blue-50 cursor-pointer";
        row.dataset.playerName = player.player_name;
        
        // Add click event to select player for heatmap
        row.addEventListener('click', () => {
            if (elements.playerSelector) {
                elements.playerSelector.value = player.player_name;
                // Trigger the change event
                const event = new Event('change');
                elements.playerSelector.dispatchEvent(event);
                
                // Switch to heatmap tab
                document.querySelector('.tab-btn[data-tab="heatmap"]').click();
            }
        });
        
        row.innerHTML = `
            <td class="py-3 px-4 text-center font-semibold">${player.jersey || '-'}</td>
            <td class="py-3 px-4">${player.player_name || '-'}</td>
            <td class="py-3 px-4">${player.position || '-'}</td>
            <td class="py-3 px-4">${Math.round(player.passes) || 0}</td>
            <td class="py-3 px-4">${player.pass_completion ? player.pass_completion.toFixed(1) + '%' : '0%'}</td>
            <td class="py-3 px-4">${Math.round(player.shots) || 0}</td>
            <td class="py-3 px-4">${Math.round(player.goals) || 0}</td>
            <td class="py-3 px-4">${player.xg ? player.xg.toFixed(2) : '0.00'}</td>
        `;
        
        tableElement.appendChild(row);
    });
}