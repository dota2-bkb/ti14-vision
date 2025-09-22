# Dota 2 Vision Analysis - TI14 Teams

A Python-based tool for analyzing vision control (ward placement, smoke usage) in professional Dota 2 matches, specifically focused on TI14 (The International 2014) teams Falcon and Team Parivision.

## Overview

This project processes HTML match data from DOTABUFF to extract and visualize vision-related events (Observer Ward placements, destructions, and Smoke of Deceit usage) on the Dota 2 map. It generates comprehensive analysis reports and visualizations to help understand team vision strategies across different game phases.

## Features

- **Vision Event Extraction**: Parse Observer Ward placements, destructions, and Smoke usage from DOTABUFF HTML files
- **Timeline Analysis**: Categorize events by game phases (pre-game, 0-6min, 6-12min, 12-20min, 20-40min, 40+min)
- **Team-based Visualization**: Generate separate analysis for Radiant/Dire sides
- **Multi-game Comparison**: Overlay multiple games to identify patterns
- **Individual Game Analysis**: Detailed single-game vision analysis with enemy ward destruction tracking

## Data Source

The HTML data files are downloaded from **DOTABUFF**, specifically from the "Vision" tab of match pages. I use the browser to open the link (https://www.dotabuff.com/matches/8461854486/vision)[https://www.dotabuff.com/matches/8461854486/vision], replace the number with the **Game Match ID**  Each HTML file contains detailed match logs with vision events including:

- Observer Ward placements with exact map coordinates
- Observer Ward destructions
- Smoke of Deceit activations
- Timestamps and hero information
- Side (Radiant/Dire) information

## Project Structure

```
dota2/
├── data_falcon/          # Falcon team match HTML files
├── data_pari/           # Team Pari match HTML files
├── output_falcon/       # Generated Falcon analysis results
├── output_pari/         # Generated Team Pari analysis results
├── game_falcon.csv      # Falcon match metadata
├── game_pari.csv        # Team Pari match metadata
├── dota2_map.jpg        # Base Dota 2 map image
├── history_vision.py    # Main batch analysis script
├── single_game_vision.py # Single game analysis script
└── requirements.txt     # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dota2
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Batch Analysis (Multiple Games)

Analyze all games for a specific team:

```bash
# Analyze Falcon team games
python history_vision.py --team falcon

# Analyze Team Pari games
python history_vision.py --team pari
```

This generates:
- **CSV files**: Individual game event data (`{Side}_{GameID}.csv`)
- **Vision heatmaps**: Ward placement patterns by time phases
- **Smoke analysis**: Smoke usage patterns across different game periods

### Single Game Analysis

Analyze a specific match with detailed enemy vision tracking:

```bash
python single_game_vision.py --team falcon --game_id 8461854486 --our_side Dire --enemy_team pari
```

Parameters:
- `--team`: Your team (falcon/pari)
- `--game_id`: Specific match ID to analyze
- `--our_side`: Your team's side (Radiant/Dire)
- `--enemy_team`: Enemy team name (falcon/pari)

## Output Files

### Generated Visualizations

1. **Time-based Ward Maps**: `{Side}_before_{minutes}_minutes.jpg`
   - Shows ward placements for specific time periods
   - Color-coded by different games
   - Includes hero names and timestamps

2. **Smoke Analysis Maps**: `{Team}Smoke-{Side} {time_range}.jpg`
   - Smoke usage patterns across game phases
   - Filtered to avoid spam (minimum 1-minute intervals)

3. **Single Game Analysis**: `{team}-{side}-{game_id}.jpg`
   - Combined view of enemy wards and your ward destructions
   - Red circles: Enemy ward placements
   - Blue circles: Enemy smoke usage
   - Green circles: Your ward destructions

### Data Files

- **Event CSV**: Contains parsed events with columns:
  - `time`: Game timestamp
  - `action`: Raw event description
  - `key_action`: Categorized action (placed/destroyed/smoke)
  - `side`: Team side (Radiant/Dire)
  - `hero`: Hero name
  - `position`: Map coordinates (percentage and pixels)

## Game Data Format

The CSV files (`game_falcon.csv`, `game_pari.csv`) contain match metadata:
- `场次`: Match description
- `{Team} 天辉/夜魇`: Team's side (Radiant/Dire in Chinese)
- `胜者`: Winner
- `比赛id`: Match ID (corresponds to DOTABUFF match ID)

## Technical Details

### Vision Event Detection

The parser identifies three key event types:
1. **Ward Placement**: "placed Observer Ward" events
2. **Ward Destruction**: "destroyed Observer Ward" events  
3. **Smoke Usage**: "activated" events (Smoke of Deceit)

### Coordinate System

- HTML percentages are converted to pixel coordinates on the Dota 2 map
- Map dimensions are extracted from `dota2_map.jpg`
- Coordinates represent exact in-game positions

### Time Processing

- Supports both MM:SS and HH:MM:SS formats
- Pre-game events (negative timestamps) are handled separately
- Events are filtered and grouped by configurable time slots

## Customization

### Time Slots
Modify `vis_time_slots` in the scripts to change analysis periods:
```python
vis_time_slots = [0, 6, 12, 20, 40, 100]  # minutes
```

### Colors
Game colors can be customized in the `game_color` array for better visualization.

### Hero Name Mapping
Update `hero_dict` in `single_game_vision.py` for custom hero name display.

## Dependencies

- **opencv-python**: Image processing and visualization
- **pandas**: Data manipulation and CSV handling
- **beautifulsoup4**: HTML parsing for DOTABUFF data

## Contributing

1. Ensure HTML files are properly downloaded from DOTABUFF Vision pages
2. Update CSV metadata files when adding new matches
3. Test visualization outputs for clarity and accuracy
4. Follow existing naming conventions for consistency

## Notes

- The project is specifically designed for TI14 analysis of Falcon and Team Pari
- HTML files must be downloaded manually from DOTABUFF
- Generated images include "Made by SPACE" watermark
- Color coding helps distinguish between different games in overlay visualizations

## Future Enhancements

- Automated DOTABUFF data fetching
- Interactive web-based visualizations
- Advanced statistical analysis of vision patterns
- Support for additional teams and tournaments
- Real-time match analysis integration