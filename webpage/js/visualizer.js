/**
 * Dota 2 Events Visualizer
 * Main JavaScript functionality for visualizing game events
 */

// Global variables
let gamesData = [];
let allEvents = [];
let selectedGames = new Set();
let maxObserverWards = 2;
let showSentryWards = false;
let showSmoke = true;
let showArrows = true;
let showTime = true;
let observerOnlyMode = false;

// Initialize event listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
});

/**
 * Initialize all event listeners
 */
function initializeEventListeners() {
    // File upload handler
    document.getElementById('csvFile').addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            loadCSVFile(file);
        }
    });

    // Ward limit slider handler
    document.getElementById('wardLimitSlider').addEventListener('input', function(event) {
        maxObserverWards = parseInt(event.target.value);
        document.getElementById('wardLimitValue').textContent = maxObserverWards;
        if (gamesData.length > 0) {
            updateVisualization();
            updateStats();
        }
    });

    // Initialize tooltip positioning
    document.addEventListener('mousemove', function(e) {
        const tooltip = document.getElementById('tooltip');
        if (tooltip.style.display === 'block') {
            tooltip.style.left = e.pageX + 10 + 'px';
            tooltip.style.top = e.pageY - 10 + 'px';
        }
    });
}

/**
 * Load and parse CSV file
 */
function loadCSVFile(file) {
    showLoading(true);
    hideError();

    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const csv = e.target.result;
            parseCSVData(csv);
            showLoading(false);
            document.getElementById('dataSection').style.display = 'block';
        } catch (error) {
            showError('Error parsing CSV file: ' + error.message);
            showLoading(false);
        }
    };
    reader.readAsText(file);
}

/**
 * Convert Python tuples to JSON arrays
 */
function convertPythonTuplesToJSON(str) {
    return str.replace(/\(([^)]+)\)/g, function(match, content) {
        const parts = content.split(',').map(part => part.trim());
        if (parts.length === 2) {
            const num1 = parseFloat(parts[0]);
            const num2 = parseFloat(parts[1]);
            if (!isNaN(num1) && !isNaN(num2)) {
                return `[${num1}, ${num2}]`;
            }
        }
        return match;
    });
}

/**
 * Parse CSV data and populate game information
 */
function parseCSVData(csv) {
    const lines = csv.trim().split('\n');
    const headers = lines[0].split(',');
    
    gamesData = [];
    allEvents = [];

    for (let i = 1; i < lines.length; i++) {
        const line = lines[i];
        if (!line.trim()) continue;

        const parts = parseCSVLine(line);
        if (parts.length < 6) continue;

        const eventsStr = parts[0].replace(/^"|"$/g, '');
        const heroPlayersStr = parts[1].replace(/^"|"$/g, '');
        const heroPlayersAgainstStr = parts[2].replace(/^"|"$/g, '');
        const side = parts[3];
        const gameId = parts[4];
        const gameTime = parts[5];

        try {
            let jsonStr = eventsStr.replace(/'/g, '"');
            jsonStr = convertPythonTuplesToJSON(jsonStr);
            
            const eventsData = JSON.parse(jsonStr);
            
            let heroPlayers = {};
            let heroPlayersAgainst = {};
            
            try {
                heroPlayers = JSON.parse(heroPlayersStr.replace(/'/g, '"'));
                heroPlayersAgainst = JSON.parse(heroPlayersAgainstStr.replace(/'/g, '"'));
            } catch (e) {
                console.warn('Failed to parse hero players for game', gameId, ':', e);
            }
            
            const gameInfo = {
                gameId: gameId,
                side: side,
                events: eventsData,
                heroPlayers: heroPlayers,
                heroPlayersAgainst: heroPlayersAgainst,
                gameTime: gameTime
            };

            gamesData.push(gameInfo);

            Object.keys(eventsData).forEach(hero => {
                eventsData[hero].forEach(event => {
                    allEvents.push({
                        ...event,
                        hero: hero,
                        gameId: gameId,
                        side: side
                    });
                });
            });
        } catch (e) {
            console.error('Failed to parse events for game', gameId, ':', e);
            continue;
        }
    }
    
    if (gamesData.length === 0) {
        showError('No games could be parsed from the CSV file. Please check the file format.');
        return;
    }
    
    populateGamesList();
    populatePlayerNames();
    updateVisualization();
    updateStats();
}

/**
 * Parse CSV line handling quoted content
 */
function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    let i = 0;

    while (i < line.length) {
        const char = line[i];
        
        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                current += '"';
                i += 2;
                continue;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
            i++;
            continue;
        } else {
            current += char;
        }
        i++;
    }
    
    result.push(current);
    return result;
}

/**
 * Populate the games list with checkboxes
 */
function populateGamesList() {
    const gamesList = document.getElementById('gamesList');
    gamesList.innerHTML = '';

    const gamesBySide = {
        radiant: [],
        dire: []
    };

    gamesData.forEach((game, index) => {
        gamesBySide[game.side].push({ ...game, originalIndex: index });
    });

    ['radiant', 'dire'].forEach(side => {
        if (gamesBySide[side].length === 0) return;

        const sideSection = document.createElement('div');
        sideSection.className = `side-section ${side}`;

        const sideHeader = document.createElement('h4');
        sideHeader.textContent = `${side.charAt(0).toUpperCase() + side.slice(1)} (${gamesBySide[side].length} games)`;
        sideSection.appendChild(sideHeader);

        const sideControls = document.createElement('div');
        sideControls.className = 'side-controls';

        const selectAllBtn = document.createElement('button');
        selectAllBtn.className = 'side-btn';
        selectAllBtn.textContent = 'Select All';
        selectAllBtn.onclick = () => selectAllSide(side);

        const deselectAllBtn = document.createElement('button');
        deselectAllBtn.className = 'side-btn deselect';
        deselectAllBtn.textContent = 'Deselect All';
        deselectAllBtn.onclick = () => deselectAllSide(side);

        sideControls.appendChild(selectAllBtn);
        sideControls.appendChild(deselectAllBtn);
        sideSection.appendChild(sideControls);

        const sideGames = document.createElement('div');
        sideGames.className = 'side-games';

        gamesBySide[side].forEach((game, sideIndex) => {
            const gameItem = document.createElement('div');
            gameItem.className = 'game-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `game_${game.originalIndex}`;
            checkbox.checked = game.originalIndex < 3;
            checkbox.addEventListener('change', function() {
                if (this.checked) {
                    selectedGames.add(game.gameId);
                } else {
                    selectedGames.delete(game.gameId);
                }
                updateVisualization();
                updateStats();
            });

            const label = document.createElement('label');
            label.htmlFor = `game_${game.originalIndex}`;
            
            const gameDate = new Date(game.gameTime);
            const localDateTime = gameDate.toLocaleString();
            
            const opponentNames = Object.values(game.heroPlayersAgainst || {});
            const opponentDisplay = opponentNames.length > 0 ? opponentNames.join(', ') : 'Unknown';
            
            label.innerHTML = `
                <div class="game-info">
                    <div class="game-main-info">${localDateTime}</div>
                    <div class="game-sub-info">
                        Match ${game.gameId} vs <span class="opponent-name">${opponentDisplay}</span>
                    </div>
                </div>
            `;

            gameItem.appendChild(checkbox);
            gameItem.appendChild(label);
            sideGames.appendChild(gameItem);

            if (game.originalIndex < 3) {
                selectedGames.add(game.gameId);
            }
        });

        sideSection.appendChild(sideGames);
        gamesList.appendChild(sideSection);
    });
}

/**
 * Populate player names section with unique team players
 */
function populatePlayerNames() {
    const playerNamesSection = document.getElementById('playerNamesSection');
    const playerNamesList = document.getElementById('playerNamesList');
    
    if (!playerNamesSection || !playerNamesList) return;
    
    // Collect all unique player names from all games
    const allPlayerNames = new Set();
    
    gamesData.forEach(game => {
        if (game.heroPlayers && typeof game.heroPlayers === 'object') {
            Object.values(game.heroPlayers).forEach(playerName => {
                if (playerName && playerName.trim()) {
                    allPlayerNames.add(playerName.trim());
                }
            });
        }
    });
    
    // Clear existing content
    playerNamesList.innerHTML = '';
    
    if (allPlayerNames.size === 0) {
        playerNamesSection.style.display = 'none';
        return;
    }
    
    // Sort player names alphabetically and create comma-separated sentence
    const sortedPlayerNames = Array.from(allPlayerNames).sort();
    const playerSentence = sortedPlayerNames.join(', ');
    
    // Display as a single sentence
    playerNamesList.textContent = playerSentence;
    
    // Show the section
    playerNamesSection.style.display = 'block';
}

/**
 * Select all games for a specific side
 */
function selectAllSide(side) {
    gamesData.forEach(game => {
        if (game.side === side) {
            selectedGames.add(game.gameId);
        }
    });
    
    document.querySelectorAll('#gamesList input[type="checkbox"]').forEach(cb => {
        const gameIndex = parseInt(cb.id.replace('game_', ''));
        const game = gamesData[gameIndex];
        if (game && game.side === side) {
            cb.checked = true;
        }
    });
    
    updateVisualization();
    updateStats();
}

/**
 * Deselect all games for a specific side
 */
function deselectAllSide(side) {
    gamesData.forEach(game => {
        if (game.side === side) {
            selectedGames.delete(game.gameId);
        }
    });
    
    document.querySelectorAll('#gamesList input[type="checkbox"]').forEach(cb => {
        const gameIndex = parseInt(cb.id.replace('game_', ''));
        const game = gamesData[gameIndex];
        if (game && game.side === side) {
            cb.checked = false;
        }
    });
    
    updateVisualization();
    updateStats();
}

/**
 * Toggle sentry wards visibility
 */
function toggleSentryWards() {
    showSentryWards = !showSentryWards;
    const toggleBtn = document.getElementById('sentryToggle');
    
    if (showSentryWards) {
        toggleBtn.textContent = '🔵 Hide Sentry Wards';
        toggleBtn.classList.add('active');
    } else {
        toggleBtn.textContent = '🔵 Show Sentry Wards';
        toggleBtn.classList.remove('active');
    }
    
    if (gamesData.length > 0) {
        updateVisualization();
        updateStats();
    }
}

/**
 * Toggle path arrows visibility
 */
function toggleArrows() {
    showArrows = !showArrows;
    const toggleBtn = document.getElementById('arrowToggle');
    
    if (showArrows) {
        toggleBtn.textContent = '🏹 Hide Path';
        toggleBtn.classList.add('active');
    } else {
        toggleBtn.textContent = '🏹 Show Path';
        toggleBtn.classList.remove('active');
    }
    
    if (gamesData.length > 0) {
        updateVisualization();
        updateStats();
    }
}

/**
 * Toggle smoke events visibility
 */
function toggleSmoke() {
    showSmoke = !showSmoke;
    const toggleBtn = document.getElementById('smokeToggle');
    
    if (showSmoke) {
        toggleBtn.textContent = '🟣 Hide Smoke';
        toggleBtn.classList.add('active');
    } else {
        toggleBtn.textContent = '🟣 Show Smoke';
        toggleBtn.classList.remove('active');
    }
    
    if (gamesData.length > 0) {
        updateVisualization();
        updateStats();
    }
}

/**
 * Toggle time labels visibility
 */
function toggleTime() {
    showTime = !showTime;
    const toggleBtn = document.getElementById('timeToggle');
    
    if (showTime) {
        toggleBtn.textContent = '🕐 Hide Time';
        toggleBtn.classList.add('active');
    } else {
        toggleBtn.textContent = '🕐 Show Time';
        toggleBtn.classList.remove('active');
    }
    
    if (gamesData.length > 0) {
        updateVisualization();
        updateStats();
    }
}

/**
 * Toggle observer-only mode
 */
function toggleObserverOnly() {
    observerOnlyMode = !observerOnlyMode;
    const toggleBtn = document.getElementById('observerOnlyToggle');
    
    if (observerOnlyMode) {
        toggleBtn.textContent = '🟡 Show All Events';
        toggleBtn.classList.add('active');
    } else {
        toggleBtn.textContent = '🟡 Show This Ward Only';
        toggleBtn.classList.remove('active');
    }
    
    if (gamesData.length > 0) {
        updateVisualization();
        updateStats();
    }
}

/**
 * Update the main visualization
 */
function updateVisualization() {
    const mapContainer = document.getElementById('mapContainer');
    
    // Remove existing markers, time labels, and arrows
    document.querySelectorAll('.event-marker').forEach(marker => marker.remove());
    document.querySelectorAll('.event-time').forEach(timeLabel => timeLabel.remove());
    document.querySelectorAll('.path-arrow').forEach(arrow => arrow.remove());

    // Filter events based on selected games and ward limits
    let filteredEvents = filterEventsByWardLimit(allEvents.filter(event => selectedGames.has(event.gameId)));
    
    // Apply observer-only mode if enabled
    if (observerOnlyMode) {
        filteredEvents = filterObserverOnlyMode(filteredEvents);
    }

    // Group events by game and hero for path drawing
    const eventsByGameAndHero = {};
    filteredEvents.forEach(event => {
        const key = `${event.gameId}_${event.hero}`;
        if (!eventsByGameAndHero[key]) {
            eventsByGameAndHero[key] = [];
        }
        eventsByGameAndHero[key].push(event);
    });

    // Sort events by time within each hero group
    Object.keys(eventsByGameAndHero).forEach(key => {
        eventsByGameAndHero[key].sort((a, b) => {
            return parseTime(a.time) - parseTime(b.time);
        });
    });

    // Draw path arrows first (so they appear behind markers)
    if (showArrows) {
        Object.values(eventsByGameAndHero).forEach(heroEvents => {
            drawHeroPath(heroEvents, mapContainer);
        });
    }

    // Count observer wards per game for labeling
    const observerWardCounts = {};
    const sortedFilteredEvents = [...filteredEvents].sort((a, b) => {
        if (a.gameId !== b.gameId) {
            return a.gameId.localeCompare(b.gameId);
        }
        return parseTime(a.time) - parseTime(b.time);
    });

    // Deduplicate smoke events for visualization
    const seenSmokeEvents = new Set();
    const eventsToVisualize = sortedFilteredEvents.filter(event => {
        if (event.key_action === 'smoke') {
            const smokeKey = `${event.gameId}_${event.time}_${event.position.left_percent}_${event.position.top_percent}`;
            if (seenSmokeEvents.has(smokeKey)) {
                return false;
            }
            seenSmokeEvents.add(smokeKey);
        }
        return true;
    });

    // Add markers and time labels for filtered events
    eventsToVisualize.forEach(event => {
        if (event.position && event.position.left_percent !== undefined && event.position.top_percent !== undefined) {
            if (event.key_action === 'placed_observer') {
                if (!observerWardCounts[event.gameId]) {
                    observerWardCounts[event.gameId] = 0;
                }
                observerWardCounts[event.gameId]++;
                event.observerWardNumber = observerWardCounts[event.gameId];
            }
            
            const { marker, timeLabel } = createEventMarker(event);
            mapContainer.appendChild(marker);
            mapContainer.appendChild(timeLabel);
        }
    });

    updateLegendVisibility();
}

/**
 * Update legend visibility based on current settings
 */
function updateLegendVisibility() {
    const observerLegend = document.querySelector('.legend-item:nth-child(1)');
    const sentryLegend = document.querySelector('.legend-item:nth-child(2)');
    const smokeLegend = document.querySelector('.legend-item:nth-child(3)');
    
    if (observerOnlyMode) {
        if (observerLegend) observerLegend.style.display = 'flex';
        if (sentryLegend) sentryLegend.style.display = 'none';
        if (smokeLegend) smokeLegend.style.display = 'none';
    } else {
        if (observerLegend) observerLegend.style.display = 'flex';
        if (sentryLegend) sentryLegend.style.display = showSentryWards ? 'flex' : 'none';
        if (smokeLegend) smokeLegend.style.display = showSmoke ? 'flex' : 'none';
    }
}

/**
 * Create event marker and time label
 */
function createEventMarker(event) {
    const marker = document.createElement('div');
    marker.className = `event-marker ${event.key_action.replace('placed_', '')}`;
    
    const left = Math.max(0, Math.min(100, event.position.left_percent));
    const top = Math.max(0, Math.min(100, event.position.top_percent));
    
    marker.style.left = `${left}%`;
    marker.style.top = `${top}%`;

    const timeLabel = document.createElement('div');
    timeLabel.className = 'event-time';
    
    if (event.key_action === 'placed_observer' && event.observerWardNumber) {
        timeLabel.textContent = `${event.time} [${event.observerWardNumber}]`;
    } else {
        timeLabel.textContent = event.time;
    }
    
    timeLabel.style.left = `${left}%`;
    timeLabel.style.top = `${top}%`;
    
    if (!showTime) {
        timeLabel.style.display = 'none';
    }

    marker.addEventListener('mouseenter', function(e) {
        showTooltip(e, event);
    });

    marker.addEventListener('mouseleave', function() {
        hideTooltip();
    });

    return { marker, timeLabel };
}

/**
 * Show tooltip on hover
 */
function showTooltip(e, event) {
    const tooltip = document.getElementById('tooltip');
    const actionText = event.key_action === 'smoke' ? 'Smoke of Deceit' : 
                      event.key_action === 'placed_observer' ? 'Observer Ward' : 'Sentry Ward';
    
    tooltip.innerHTML = `
        <strong>${event.hero}</strong><br>
        ${actionText}<br>
        Time: ${event.time}<br>
        Game: ${event.gameId} (${event.side})<br>
        Position: ${event.position.left_percent}%, ${event.position.top_percent}%
    `;
    
    tooltip.style.display = 'block';
    tooltip.style.left = e.pageX + 10 + 'px';
    tooltip.style.top = e.pageY - 10 + 'px';
}

/**
 * Hide tooltip
 */
function hideTooltip() {
    document.getElementById('tooltip').style.display = 'none';
}

/**
 * Filter events by ward limit and time cutoff
 */
function filterEventsByWardLimit(events) {
    const eventsByGame = {};
    events.forEach(event => {
        const gameId = event.gameId;
        if (!eventsByGame[gameId]) {
            eventsByGame[gameId] = [];
        }
        eventsByGame[gameId].push(event);
    });

    const filteredEvents = [];
    Object.values(eventsByGame).forEach(gameEvents => {
        gameEvents.sort((a, b) => parseTime(a.time) - parseTime(b.time));
        
        let observerWardCount = 0;
        let cutoffTime = null;
        
        for (let event of gameEvents) {
            if (event.key_action === 'placed_observer') {
                observerWardCount++;
                if (observerWardCount === maxObserverWards) {
                    cutoffTime = parseTime(event.time);
                    break;
                }
            }
        }
        
        if (cutoffTime === null) {
            gameEvents.forEach(event => {
                if (event.key_action === 'placed_sentry') {
                    if (showSentryWards) {
                        filteredEvents.push(event);
                    }
                } else if (event.key_action === 'smoke') {
                    if (showSmoke) {
                        filteredEvents.push(event);
                    }
                } else {
                    filteredEvents.push(event);
                }
            });
        } else {
            gameEvents.forEach(event => {
                const eventTime = parseTime(event.time);
                if (eventTime <= cutoffTime) {
                    if (event.key_action === 'placed_sentry') {
                        if (showSentryWards) {
                            filteredEvents.push(event);
                        }
                    } else if (event.key_action === 'smoke') {
                        if (showSmoke) {
                            filteredEvents.push(event);
                        }
                    } else {
                        filteredEvents.push(event);
                    }
                }
            });
        }
    });

    return filteredEvents;
}

/**
 * Filter events for observer-only mode
 */
function filterObserverOnlyMode(events) {
    const eventsByGame = {};
    events.forEach(event => {
        const gameId = event.gameId;
        if (!eventsByGame[gameId]) {
            eventsByGame[gameId] = [];
        }
        eventsByGame[gameId].push(event);
    });

    const filteredEvents = [];
    Object.values(eventsByGame).forEach(gameEvents => {
        gameEvents.sort((a, b) => parseTime(a.time) - parseTime(b.time));
        
        let observerWardCount = 0;
        
        for (let event of gameEvents) {
            if (event.key_action === 'placed_observer') {
                observerWardCount++;
                if (observerWardCount === maxObserverWards) {
                    filteredEvents.push(event);
                    break;
                }
            }
        }
    });
    return filteredEvents;
}

/**
 * Parse time string to seconds
 */
function parseTime(timeStr) {
    const negative = timeStr.startsWith('-');
    const cleanTime = timeStr.replace('-', '');
    const parts = cleanTime.split(':');
    let seconds = 0;
    
    if (parts.length === 2) {
        seconds = parseInt(parts[0]) * 60 + parseInt(parts[1]);
    } else if (parts.length === 3) {
        seconds = parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseInt(parts[2]);
    }
    
    return negative ? -seconds : seconds;
}

/**
 * Draw path arrows for hero movement
 */
function drawHeroPath(heroEvents, container) {
    if (heroEvents.length < 2) return;
    
    for (let i = 0; i < heroEvents.length - 1; i++) {
        const fromEvent = heroEvents[i];
        const toEvent = heroEvents[i + 1];
        
        if (!fromEvent.position || !toEvent.position) continue;
        
        const fromX = fromEvent.position.left_percent;
        const fromY = fromEvent.position.top_percent;
        const toX = toEvent.position.left_percent;
        const toY = toEvent.position.top_percent;
        
        if (Math.abs(fromX - toX) < 1 && Math.abs(fromY - toY) < 1) continue;
        if (fromX < 0 || fromX > 100 || toX < 0 || toX > 100) continue;
        if (fromY < 0 || fromY > 100 || toY < 0 || toY > 100) continue;
        
        drawArrow(container, fromX, fromY, toX, toY, getHeroColor(fromEvent.hero, fromEvent.gameId));
    }
}

/**
 * Draw SVG arrow between two points
 */
function drawArrow(container, fromX, fromY, toX, toY, color) {
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('path-arrow');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', `${fromX}%`);
    line.setAttribute('y1', `${fromY}%`);
    line.setAttribute('x2', `${toX}%`);
    line.setAttribute('y2', `${toY}%`);
    line.setAttribute('stroke', color);
    line.setAttribute('stroke-width', '2');
    line.setAttribute('opacity', '0.7');
    
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    const arrowId = `arrow-${Math.random().toString(36).substr(2, 9)}`;
    
    marker.setAttribute('id', arrowId);
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '8');
    marker.setAttribute('refY', '3');
    marker.setAttribute('orient', 'auto');
    marker.setAttribute('markerUnits', 'strokeWidth');
    
    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '0,0 0,6 9,3');
    polygon.setAttribute('fill', color);
    polygon.setAttribute('opacity', '0.7');
    
    marker.appendChild(polygon);
    defs.appendChild(marker);
    svg.appendChild(defs);
    
    line.setAttribute('marker-end', `url(#${arrowId})`);
    svg.appendChild(line);
    
    container.appendChild(svg);
}

/**
 * Get consistent color for hero-game combination
 */
function getHeroColor(heroName, gameId) {
    const colors = [
        '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
        '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
        '#F8C471', '#82E0AA', '#F1948A', '#85C1E9', '#D7BDE2'
    ];
    
    const hash = (heroName + gameId).split('').reduce((a, b) => {
        a = ((a << 5) - a) + b.charCodeAt(0);
        return a & a;
    }, 0);
    
    return colors[Math.abs(hash) % colors.length];
}

/**
 * Update statistics display
 */
function updateStats() {
    const selectedEvents = allEvents.filter(event => selectedGames.has(event.gameId));
    let filteredEvents = filterEventsByWardLimit(selectedEvents);
    
    if (observerOnlyMode) {
        filteredEvents = filterObserverOnlyMode(filteredEvents);
    }
    
    const uniqueSmokeEvents = new Set();
    const smokeEvents = filteredEvents.filter(e => e.key_action === 'smoke');
    smokeEvents.forEach(event => {
        const smokeKey = `${event.gameId}_${event.time}`;
        uniqueSmokeEvents.add(smokeKey);
    });
    
    const stats = {
        totalEvents: filteredEvents.length - smokeEvents.length + uniqueSmokeEvents.size,
        observerWards: filteredEvents.filter(e => e.key_action === 'placed_observer').length,
        sentryWards: filteredEvents.filter(e => e.key_action === 'placed_sentry').length,
        smokeEvents: uniqueSmokeEvents.size,
        selectedGames: selectedGames.size,
        totalGames: gamesData.length
    };

    const statsSection = document.getElementById('statsSection');
    statsSection.innerHTML = `
        <div class="stat-card">
            <div class="stat-number">${stats.selectedGames}/${stats.totalGames}</div>
            <div class="stat-label">Games Selected</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.totalEvents}</div>
            <div class="stat-label">Total Events</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.observerWards}</div>
            <div class="stat-label">Observer Wards</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.sentryWards}</div>
            <div class="stat-label">Sentry Wards</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">${stats.smokeEvents}</div>
            <div class="stat-label">Smoke Events</div>
        </div>
    `;
}

/**
 * Show/hide loading indicator
 */
function showLoading(show) {
    document.getElementById('loadingSection').style.display = show ? 'block' : 'none';
}

/**
 * Show error message
 */
function showError(message) {
    const errorSection = document.getElementById('errorSection');
    errorSection.textContent = message;
    errorSection.style.display = 'block';
}

/**
 * Hide error message
 */
function hideError() {
    document.getElementById('errorSection').style.display = 'none';
}
