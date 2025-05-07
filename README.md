# Football Match Analysis Tool

A comprehensive web application for analyzing football (soccer) match data using StatsBomb-format JSON files, providing detailed visualizations, statistics, and player performance metrics.

![Football Analysis Dashboard](https://media.giphy.com/media/1b7C0msGxlBSM/giphy.gif?cid=ecf05e47jjll9rfvnm8uagu6uxlwza1i8qbbawemuv4yk8bl&ep=v1_gifs_search&rid=giphy.gif&ct=g)


## Features

- **Match Statistics**: Analyze possession, shots, expected goals (xG), passes, and pass completion percentages
- **Visual Representation**: View interactive match visualizations including:
  - Overview dashboard with key match statistics
  - Shot maps showing location and expected goal value of each shot
  - Player position heatmaps showing movement patterns
- **Player Analysis**: Detailed player statistics tables and performance summaries
- **File Management**: Upload and analyze your own StatsBomb format JSON files
- **Player Focus**: Ability to analyze specific player performances within a match

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [File Structure](#file-structure)
- [Server Architecture](#server-architecture)
- [Data Format](#data-format)
- [Technologies Used](#technologies-used)
- [Future Development](#future-development)
- [Acknowledgements](#acknowledgements)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/username/football_analysis.git
   cd football_analysis
   ```

2. Install the required dependencies:
   ```bash
   pip install flask flask-cors pandas matplotlib numpy scipy
   ```

3. Create the uploads directory if it doesn't exist:
   ```bash
   mkdir -p uploads
   ```

## Usage

1. Run the server:
   ```bash
   python server.py
   ```

2. The application will automatically open in your default web browser at http://localhost:5000

3. Upload a StatsBomb format JSON file using the "Upload JSON" button

4. Select the uploaded file from the dropdown and click "Analyze Match"

5. Explore the various visualizations and analysis:
   - Match overview and statistics
   - Shot maps for both teams
   - Player position heatmaps (select a player from the dropdown)
   - Detailed player statistics for each team

## File Structure

```
football_analysis/
├── football_analysis.py  # Core analysis functionality
├── server.py             # Flask web server (see detailed explanation below)
├── templates/            # HTML templates for web pages
│   ├── index.html        # Home page showing file selection
│   ├── analysis.html     # Match analysis visualization page
│   └── player_analysis.html # Player-focused analysis page
├── uploads/              # Directory for uploaded JSON files
│   ├── 19802.json        # Example match file
│   └── ...               # Other match files
├── __pycache__/          # Python cache directory
└── README.md             # This documentation
```

## Server Architecture

The `server.py` file is the core of our web application, built with Flask. It handles all HTTP requests, file management, and interfaces with the analysis engine. Here's a detailed breakdown:

### Overview

`server.py` creates a web server that allows users to upload football match JSON files, select files for analysis, and view visualizations of match and player data through both web UI and programmatic API endpoints.

### Key Components

#### Configuration and Setup
- Configures upload directory and file size limits (16MB max)
- Creates necessary folder structure on startup
- Initializes the FootballMatchAnalyzer class that performs the actual data processing

#### Endpoints

1. **Home Page (`/`)** 
   - Lists all available JSON files for analysis
   - Renders the index.html template
   - Entry point for users to select files for analysis

2. **File Upload (`/upload`)**
   - Handles POST requests for file uploads
   - Validates file extensions (only .json accepted)
   - Saves valid files to the uploads directory
   - Redirects users back to the home page after successful upload

3. **Match Analysis (`/analyze`)**
   - Takes filename and optional player_name as parameters
   - Validates file existence
   - Processes match data through the FootballMatchAnalyzer
   - Renders the analysis.html template with match statistics:
     - Match details (teams, score, date)
     - Overall match statistics (possession, shots, etc.)
     - Home and away player statistics
     - Player-specific metrics when a player is specified

4. **Player Analysis (`/player_analysis`)**
   - Similar to the match analysis endpoint but focused on a specific player
   - Requires both filename and player_name parameters
   - Renders the player_analysis.html template with player-focused data

5. **API Endpoints**
   - `/api/analyze`: Programmatic access to analysis data in JSON format
   - `/list_files`: Returns a list of available JSON files for analysis

#### Error Handling
- Validates required parameters for each endpoint
- Checks file existence and returns appropriate HTTP status codes
- Handles analysis errors and returns meaningful error messages

#### Development Server
- Runs in debug mode for easier development (automatic reloading)
- Creates required folders if they don't exist
- Listens on localhost:5000 by default

### Execution Flow

1. User uploads a match file through the web interface or selects an existing file
2. Server validates the file and passes it to the analysis engine
3. Analysis engine processes the data and returns structured results
4. Server formats the data and renders the appropriate HTML template
5. User views the analysis results and can interact with visualizations

### Integration Points

- **FootballMatchAnalyzer**: The server interfaces with this class to perform the actual data analysis
- **Templates**: Renders HTML templates with analysis results for web display
- **File System**: Manages uploaded files and ensures they're available for analysis
- **API Clients**: Provides JSON endpoints for programmatic access to analysis data

## Data Format

This tool is designed to work with StatsBomb format JSON files, which contain detailed event data for football matches. Each event represents actions like passes, shots, tackles, etc., with location coordinates, player information, and additional metadata.

Example files are provided in the `uploads/` directory to help you get started.

## Technologies Used

### Backend
- **Python**: Core programming language
- **Flask**: Web server framework
- **Pandas/PySpark**: Data manipulation and analysis
- **Matplotlib**: Data visualization and plotting
- **NumPy/SciPy**: Scientific computing and statistical analysis


### Frontend
- **HTML**: Frontend interface
- **Bootstrap**: Styling framework
- **Chart.js**: Interactive charts and visualizations
- **Font Awesome**: Icon library

## Future Development

Potential future enhancements:
- Team and player comparison across multiple matches
- Advanced tactical analysis (passing networks, defensive coverage)
- Match timeline visualization
- Video integration for key events
- Machine learning integration for predictive analytics

## Acknowledgements

- Data format based on [StatsBomb Open Data](https://github.com/statsbomb/open-data)
- Visualization techniques inspired by leading football analytics platforms
- This project is intended for educational and analytical purposes

---

© 2025 Football Analysis Dashboard
