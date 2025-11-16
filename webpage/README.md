# Dota 2 Events Visualizer

A web-based visualization tool for analyzing Dota 2 game events including ward placements and smoke usage.

## File Structure

```
dota2/                  # Root directory
├── index.html          # Main HTML file (GitHub Pages entry point)
└── webpage/
    ├── css/
    │   └── styles.css  # All CSS styles
    ├── js/
    │   └── visualizer.js # All JavaScript functionality
    └── README.md       # This file
```

## Features

- **CSV Data Loading**: Load events_summary.csv files to visualize game events
- **Game Selection**: Filter by Radiant/Dire sides with individual game selection
- **Event Filtering**: 
  - Observer ward limit slider (1-20 wards per game)
  - Toggle sentry wards visibility
  - Toggle smoke events visibility
  - Toggle time labels visibility
  - Toggle path arrows (hero movement connections)
  - Observer-only mode (show specific ward placement only)
- **Interactive Map**: Hover tooltips with detailed event information
- **Statistics**: Real-time stats showing selected games and event counts
- **Responsive Design**: Modern UI with glassmorphism effects

## Usage

1. Open the root `index.html` in a web browser (or visit the GitHub Pages URL)
2. Click "Choose CSV File" and select your `events_summary.csv` file
3. Use the game selection checkboxes to choose which games to visualize
4. Adjust visualization settings using the control buttons and slider
5. Hover over markers on the map for detailed information

## Event Types

- **Observer Wards**: Yellow circles with placement numbers
- **Sentry Wards**: Blue squares (toggleable)
- **Smoke Events**: Purple diamonds (toggleable)
- **Path Arrows**: Colored lines showing hero movement between events (toggleable)

## Browser Compatibility

- Modern browsers supporting ES6+ features
- Chrome, Firefox, Safari, Edge (latest versions)

## Dependencies

- No external libraries required
- Pure HTML5, CSS3, and JavaScript
