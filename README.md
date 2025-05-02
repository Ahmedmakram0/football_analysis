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
├── server.py             # Flask web server
├── index.html            # Web interface
├── script.js             # Frontend JavaScript
├── styles.css            # CSS styling
├── uploads/              # Directory for uploaded JSON files
├── README.md             # This documentation
└── __pycache__/          # Python cache directory
```

## Data Format

This tool is designed to work with StatsBomb format JSON files, which contain detailed event data for football matches. Each event represents actions like passes, shots, tackles, etc., with location coordinates, player information, and additional metadata.

Example files are provided in the `uploads/` directory to help you get started.

## Technologies Used

### Backend
- **Python**: Core programming language
- **Flask**: Web server framework
- **Pandas**: Data manipulation and analysis
- **Matplotlib**: Data visualization and plotting
- **NumPy/SciPy**: Scientific computing and statistical analysis

### Frontend
- **HTML/CSS/JavaScript**: Frontend interface
- **Tailwind CSS**: Styling framework
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
