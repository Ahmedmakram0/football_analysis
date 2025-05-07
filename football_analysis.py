import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from scipy.ndimage import gaussian_filter
import base64
from io import BytesIO
from typing import Dict, Any, List, Optional
import os
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, ArrayType, MapType
import json
import pandas as pd
import matplotlib

class FootballMatchAnalyzer:
    def __init__(self):
        # Initialize Spark session
        self.spark = SparkSession.builder \
            .appName("FootballAnalysis") \
            .config("spark.sql.execution.arrow.pyspark.enabled", "true") \
            .getOrCreate()
        # Set log level to reduce verbosity
        self.spark.sparkContext.setLogLevel("ERROR")
        
        # Enhanced visualization settings with better contrast
        self.viz_config = {
            'pitch_color': '#0e1117',  # Darker background for better contrast
            'line_color': (1, 1, 1, 0.8),  # White with 80% opacity (using matplotlib-compatible RGBA tuple)
            'home_color': '#3498db',  # Bright blue for home team
            'away_color': '#e74c3c',  # Bright red for away team
            'heatmap_home_cmap': 'plasma',  # High contrast colormap for home heatmaps
            'heatmap_away_cmap': 'inferno',  # High contrast colormap for away heatmaps
            'shot_goal_color': '#2ecc71',  # Bright green for goals
            'shot_miss_color': '#f39c12',  # Bright orange for missed shots
            'text_color': 'white'  # White text for better readability
        }
        
        # Update config with visualization settings
        self.config = {
            'pitch_color': self.viz_config['pitch_color'],
            'line_color': self.viz_config['line_color'],
            'home_color': self.viz_config['home_color'],
            'away_color': self.viz_config['away_color']
        }
        
    def load_data(self, file_path: str) -> Dict:
        """Load StatsBomb JSON data, And using Spark for large files."""
        try:
            # Check file size to determine whether to use Spark Or Pandas.
            file_size = os.path.getsize(file_path)
            use_spark = file_size > 10 * 1024 * 1024  # Use Spark for files larger than 10MB
            
            if use_spark:
                # Define schema for StatsBomb data
                events_schema = self._get_statsbomb_schema()
                
                # Read JSON with Spark
                df = self.spark.read.json(file_path)
                
                # Convert to Python objects for compatibility with existing code
                events = df.rdd.collect()
                events = [event.asDict() for event in events]
                return events
            else:
                # Use regular Python for smaller files
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def _get_statsbomb_schema(self):
        """Create a simplified schema for StatsBomb data."""
        # This is a simplified schema - the actual StatsBomb data is more complex
        # We'll let Spark infer the schema for most parts, but define this for reference
        return StructType([
            StructField("id", StringType(), True),
            StructField("index", IntegerType(), True),
            StructField("period", IntegerType(), True),
            StructField("timestamp", StringType(), True),
            StructField("minute", IntegerType(), True),
            StructField("second", IntegerType(), True),
            StructField("type", StructType([
                StructField("id", IntegerType(), True),
                StructField("name", StringType(), True)
            ]), True),
            StructField("possession", IntegerType(), True),
            StructField("possession_team", StructType([
                StructField("id", IntegerType(), True),
                StructField("name", StringType(), True)
            ]), True),
            StructField("team", StructType([
                StructField("id", IntegerType(), True),
                StructField("name", StringType(), True)
            ]), True),
            StructField("location", ArrayType(FloatType()), True),
        ])
        
    def extract_match_details(self, events: List[Dict]) -> Dict[str, Any]:
        """Extract basic match details (teams, formations)."""
        # Consider using Spark for this if events is large
        if len(events) > 10000:  # Arbitrary threshold
            # Convert to Spark DataFrame
            events_df = self.spark.createDataFrame(events)
            
            # Find unique teams
            teams_df = events_df.select("team.name").distinct()
            team_names = [row["name"] for row in teams_df.collect() if row["name"] is not None]
            
            if len(team_names) != 2:
                team_names = ["Team A", "Team B"] if len(team_names) < 2 else team_names[:2]
                
            home_team, away_team = team_names
            
            # Extract formations from Starting XI events
            home_formation = "Unknown"
            away_formation = "Unknown"
            
            # Filter for Starting XI events
            starting_xi_df = events_df.filter(
                (events_df["type.name"] == "Starting XI") & 
                events_df["tactics"].isNotNull()
            )
            
            for row in starting_xi_df.collect():
                team_name = row["team"]["name"] if row["team"] and "name" in row["team"] else None
                if team_name == home_team and row["tactics"] and "formation" in row["tactics"]:
                    home_formation = str(row["tactics"]["formation"])
                elif team_name == away_team and row["tactics"] and "formation" in row["tactics"]:
                    away_formation = str(row["tactics"]["formation"])
        else:
            # Use the original code for smaller datasets
            # Find unique teams
            teams = set()
            for event in events:
                if 'team' in event and 'name' in event['team'] is not None:
                    teams.add(event['team']['name'])
            
            team_names = list(teams)
            if len(team_names) != 2:
                team_names = ["Team A", "Team B"] if len(team_names) < 2 else team_names[:2]
                
            home_team, away_team = team_names
            
            # Extract formations from Starting XI events
            home_formation = "Unknown"
            away_formation = "Unknown"
            
            for event in events:
                if event.get('type', {}).get('name') == "Starting XI" and 'tactics' in event:
                    team_name = event.get('team', {}).get('name') if event.get('team', {}).get('name') is not None else None
                    if team_name == home_team and 'formation' in event['tactics']:
                        home_formation = str(event['tactics']['formation'])
                    elif team_name == away_team and 'formation' in event['tactics']:
                        away_formation = str(event['tactics']['formation'])
        
        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_formation": home_formation,
            "away_formation": away_formation
        }
    
    def calculate_match_stats(self, events: List[Dict], home_team: str, away_team: str) -> Dict[str, Any]:
        """Calculate key match statistics using PySpark for large datasets."""
        # Using PySpark for processing if the dataset is large
        if len(events) > 10000:  # Arbitrary threshold for using Spark
            # Convert events to DataFrame
            events_df = self.spark.createDataFrame(events)
            
            # Register as temporary view for SQL queries
            events_df.createOrReplaceTempView("events")
            
            # Calculate possession (count of events by possession team)
            possession_df = self.spark.sql(f"""
                SELECT 
                    possession_team.name as team_name, 
                    COUNT(*) as possession_count 
                FROM events 
                WHERE possession_team.name IS NOT NULL
                GROUP BY possession_team.name
            """)
            
            # Get possession counts
            possession_counts = {row["team_name"]: row["possession_count"] 
                               for row in possession_df.collect()}
            
            total_events = len(events)
            home_possession = possession_counts.get(home_team, 0)
            away_possession = possession_counts.get(away_team, 0)
            
            # Calculate passes and pass completion
            passes_df = self.spark.sql(f"""
                SELECT 
                    team.name as team_name,
                    COUNT(*) as passes,
                    SUM(CASE WHEN pass.outcome IS NULL THEN 1 ELSE 0 END) as completed_passes
                FROM events
                WHERE type.name = 'Pass' AND team.name IS NOT NULL
                GROUP BY team.name
            """)
            
            # Get pass statistics
            pass_stats = {row["team_name"]: {"passes": row["passes"], "completed": row["completed_passes"]} 
                         for row in passes_df.collect()}  
            #To return the teams passes as a one dictionary
            # Like this {home_team: {"passes": 0, "completed": 0}, away_team: {"passes": 0, "completed": 0}}

            home_passes = pass_stats.get(home_team, {"passes": 0, "completed": 0})["passes"]
            away_passes = pass_stats.get(away_team, {"passes": 0, "completed": 0})["passes"]
            home_completed_passes = pass_stats.get(home_team, {"passes": 0, "completed": 0})["completed"]
            away_completed_passes = pass_stats.get(away_team, {"passes": 0, "completed": 0})["completed"]
            
            # Calculate shots and goals
            shots_df = self.spark.sql(f"""
                SELECT 
                    team.name as team_name,
                    COUNT(*) as shots,
                    SUM(CASE WHEN shot.outcome.name = 'Goal' THEN 1 ELSE 0 END) as goals,
                    SUM(COALESCE(shot.statsbomb_xg, 0)) as xg
                FROM events
                WHERE type.name = 'Shot' AND team.name IS NOT NULL
                GROUP BY team.name
            """)
            
            # Get shot statistics
            shot_stats = {row["team_name"]: {"shots": row["shots"], "goals": row["goals"], "xg": row["xg"]} 
                         for row in shots_df.collect()}
            
            home_shots = shot_stats.get(home_team, {"shots": 0, "goals": 0, "xg": 0.0})["shots"]
            away_shots = shot_stats.get(away_team, {"shots": 0, "goals": 0, "xg": 0.0})["shots"]
            home_goals = shot_stats.get(home_team, {"shots": 0, "goals": 0, "xg": 0.0})["goals"]
            away_goals = shot_stats.get(away_team, {"shots": 0, "goals": 0, "xg": 0.0})["goals"]
            home_xg = shot_stats.get(home_team, {"shots": 0, "goals": 0, "xg": 0.0})["xg"]
            away_xg = shot_stats.get(away_team, {"shots": 0, "goals": 0, "xg": 0.0})["xg"]
        else:
            # Use original implementation for smaller datasets
            # Initialize counters
            total_events = len(events)
            home_possession = 0
            away_possession = 0
            home_passes = 0
            away_passes = 0
            home_completed_passes = 0
            away_completed_passes = 0
            home_shots = 0
            away_shots = 0
            home_goals = 0
            away_goals = 0
            home_xg = 0.0
            away_xg = 0.0
            
            # Process events
            for event in events:
                # Count possession
                possession_team = event.get('possession_team', {}).get('name')
                if possession_team == home_team:
                    home_possession += 1
                elif possession_team == away_team:
                    away_possession += 1
                    
                # Process by event type
                event_type = event.get('type', {}).get('name')
                team_name = event.get('team', {}).get('name')
                
                if event_type == 'Pass' and team_name:
                    # Count passes
                    if team_name == home_team:
                        home_passes += 1
                        if 'outcome' not in event.get('pass', {}):
                            home_completed_passes += 1
                    elif team_name == away_team:
                        away_passes += 1
                        if 'outcome' not in event.get('pass', {}):
                            away_completed_passes += 1
                
                elif event_type == 'Shot' and team_name:
                    # Count shots and goals
                    if team_name == home_team:
                        home_shots += 1
                        if event.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
                            home_goals += 1
                        home_xg += event.get('shot', {}).get('statsbomb_xg', 0)
                    elif team_name == away_team:
                        away_shots += 1
                        if event.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
                            away_goals += 1
                        away_xg += event.get('shot', {}).get('statsbomb_xg', 0)
        
        # Calculate percentages
        home_possession_pct = round(home_possession / total_events * 100, 1) if total_events > 0 else 50
        away_possession_pct = round(away_possession / total_events * 100, 1) if total_events > 0 else 50
        
        # Ensure they sum to 100%
        total = home_possession_pct + away_possession_pct
        if total != 100:
            home_possession_pct = round(home_possession_pct * 100 / total, 1)
            away_possession_pct = round(100 - home_possession_pct, 1)
        
        # Calculate pass completion percentages
        home_pass_completion = round(home_completed_passes / home_passes * 100, 1) if home_passes > 0 else 0
        away_pass_completion = round(away_completed_passes / away_passes * 100, 1) if away_passes > 0 else 0
        
        return {
            "possession": {
                "home": home_possession_pct,
                "away": away_possession_pct
            },
            "passes": {
                "home": home_passes, 
                "away": away_passes,
                "home_completion": home_pass_completion,
                "away_completion": away_pass_completion
            },
            "shots": {
                "home": home_shots, 
                "away": away_shots
            },
            "goals": {
                "home": home_goals, 
                "away": away_goals
            },
            "xg": {
                "home": round(home_xg, 2), 
                "away": round(away_xg, 2)
            }
        }
    
    def get_player_stats(self, events: List[Dict], team_name: str) -> List[Dict]:
        """Extract player-level statistics using PySpark for large datasets."""
        # Use Spark for large datasets
        if len(events) > 10000:  # Arbitrary threshold
            # Convert to Spark DataFrame
            events_df = self.spark.createDataFrame(events)
            events_df.createOrReplaceTempView("events")
            
            # Find players from starting XI
            lineup_df = self.spark.sql(f"""
                SELECT 
                    tactics.lineup 
                FROM events
                WHERE type.name = 'Starting XI' 
                AND team.name = '{team_name}'
                AND tactics.lineup IS NOT NULL
                LIMIT 1
            """)
            
            # Check if we found the lineup
            if lineup_df.count() > 0:
                # Extract player info from lineup
                lineup_row = lineup_df.collect()[0]
                if "lineup" in lineup_row and lineup_row["lineup"]:
                    player_info = {}
                    for player in lineup_row["lineup"]:
                        player_name = player.get("player", {}).get("name")
                        if player_name:
                            player_info[player_name] = {
                                'player_name': player_name,
                                'position': player.get("position", {}).get("name", ""),
                                'jersey': player.get("jersey_number", 0),
                                'passes': 0,
                                'successful_passes': 0,
                                'pass_completion': 0,
                                'shots': 0,
                                'goals': 0,
                                'xg': 0.0
                            }
                    
                    # Get pass statistics
                    pass_stats_df = self.spark.sql(f"""
                        SELECT 
                            player.name as player_name,
                            COUNT(*) as passes,
                            SUM(CASE WHEN pass.outcome IS NULL THEN 1 ELSE 0 END) as completed_passes
                        FROM events
                        WHERE type.name = 'Pass' 
                        AND team.name = '{team_name}'
                        AND player.name IS NOT NULL
                        GROUP BY player.name
                    """)
                    
                    # Update player info with pass statistics
                    for row in pass_stats_df.collect():
                        player_name = row["player_name"]
                        if player_name in player_info:
                            player_info[player_name]["passes"] = row["passes"]
                            player_info[player_name]["successful_passes"] = row["completed_passes"]
                    
                    # Get shot statistics
                    shot_stats_df = self.spark.sql(f"""
                        SELECT 
                            player.name as player_name,
                            COUNT(*) as shots,
                            SUM(CASE WHEN shot.outcome.name = 'Goal' THEN 1 ELSE 0 END) as goals,
                            SUM(COALESCE(shot.statsbomb_xg, 0)) as xg
                        FROM events
                        WHERE type.name = 'Shot' 
                        AND team.name = '{team_name}'
                        AND player.name IS NOT NULL
                        GROUP BY player.name
                    """)
                    
                    # Update player info with shot statistics
                    for row in shot_stats_df.collect():
                        player_name = row["player_name"]
                        if player_name in player_info:
                            player_info[player_name]["shots"] = row["shots"]
                            player_info[player_name]["goals"] = row["goals"]
                            player_info[player_name]["xg"] = row["xg"]
                    
                    # Calculate pass completion percentages
                    for player_name, stats in player_info.items():
                        if stats["passes"] > 0:
                            stats["pass_completion"] = round(stats["successful_passes"] / stats["passes"] * 100, 1)
                        stats["xg"] = round(stats["xg"], 2)  # Round xG
                    
                    return list(player_info.values())
            
            # If we couldn't get the lineup or process with Spark, fall back to the original method
        
        # Original method for smaller datasets or if Spark processing failed
        # Get player info from starting XI
        player_info = {}
        
        # Find the starting XI event for this team
        for event in events:
            if event.get('type', {}).get('name') == "Starting XI" and event.get('team', {}).get('name') == team_name:
                if 'tactics' in event and 'lineup' in event['tactics']:
                    for player in event['tactics']['lineup']:
                        player_name = player.get('player', {}).get('name', '')
                        if player_name:
                            player_info[player_name] = {
                                'player_name': player_name,
                                'position': player.get('position', {}).get('name', ''),
                                'jersey': player.get('jersey_number', 0),
                                'passes': 0,
                                'successful_passes': 0,
                                'pass_completion': 0,
                                'shots': 0,
                                'goals': 0,
                                'xg': 0.0
                            }
        
        # Process individual events
        for event in events:
            if event.get('team', {}).get('name') != team_name:
                continue
                
            player_name = event.get('player', {}).get('name')
            if not player_name or player_name not in player_info:
                continue
                
            event_type = event.get('type', {}).get('name')
            
            if event_type == 'Pass':
                player_info[player_name]['passes'] += 1
                if 'outcome' not in event.get('pass', {}):
                    player_info[player_name]['successful_passes'] += 1
            
            elif event_type == 'Shot':
                player_info[player_name]['shots'] += 1
                if event.get('shot', {}).get('outcome', {}).get('name') == 'Goal':
                    player_info[player_name]['goals'] += 1
                player_info[player_name]['xg'] += event.get('shot', {}).get('statsbomb_xg', 0)
        
        # Calculate pass completion percentages
        for player_name, stats in player_info.items():
            if stats['passes'] > 0:
                stats['pass_completion'] = round(stats['successful_passes'] / stats['passes'] * 100, 1)
            stats['xg'] = round(stats['xg'], 2)  # Round xG to 2 decimal places
        
        return list(player_info.values())
    
    def create_match_visualization(self, match_details: Dict, match_stats: Dict) -> str:
        """Create a simple visualization of match statistics"""
        home_team = match_details["home_team"]
        away_team = match_details["away_team"]
        
        # Create figure
        plt.figure(figsize=(10, 6))
        ax = plt.subplot(1, 1, 1)
        
        # Set background color
        ax.set_facecolor('#f8f9fa')
        
        # Add match score
        plt.text(0.5, 0.85, 
                f"{home_team} {match_stats['goals']['home']} - {match_stats['goals']['away']} {away_team}",
                fontsize=18, weight='bold', ha='center', transform=ax.transAxes)
        
        # Add formations
        plt.text(0.5, 0.75, 
                f"Formations: {match_details['home_formation']} vs {match_details['away_formation']}",
                fontsize=14, ha='center', transform=ax.transAxes)
        
        # Add key stats
        stats = [
            ("Possession", f"{match_stats['possession']['home']}%", f"{match_stats['possession']['away']}%", 0.65),
            ("Shots", str(match_stats['shots']['home']), str(match_stats['shots']['away']), 0.55),
            ("Expected Goals (xG)", f"{match_stats['xg']['home']}", f"{match_stats['xg']['away']}", 0.45),
            ("Total Passes", str(match_stats['passes']['home']), str(match_stats['passes']['away']), 0.35),
            ("Pass Completion", f"{match_stats['passes']['home_completion']}%", f"{match_stats['passes']['away_completion']}%", 0.25)
        ]
        
        # Draw stats
        for label, home_val, away_val, y_pos in stats:
            plt.text(0.5, y_pos, label, fontsize=12, ha='center', transform=ax.transAxes)
            plt.text(0.3, y_pos - 0.05, home_val, fontsize=12, ha='center', transform=ax.transAxes, 
                    color=self.config['home_color'])
            plt.text(0.7, y_pos - 0.05, away_val, fontsize=12, ha='center', transform=ax.transAxes, 
                    color=self.config['away_color'])
        
        # Add legend
        plt.legend(handles=[
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.config['home_color'], 
                    markersize=10, label=home_team),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.config['away_color'], 
                    markersize=10, label=away_team)
        ], loc='lower center')
        
        # Remove axes
        plt.axis('off')
        
        # Save figure as base64 for HTML embedding
        with BytesIO() as buffer:
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close()
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def create_player_heatmap(self, events: List[Dict], player_name: str, team_name: str) -> str:
        """Create a heatmap showing the positions of a specific player on the pitch."""
        # Use Spark to filter events for large datasets
        if len(events) > 10000:
            # Convert to Spark DataFrame
            events_df = self.spark.createDataFrame(events)
            
            # Filter for player events with location data
            player_events_df = events_df.filter(
                (events_df["player.name"] == player_name) & 
                (events_df["team.name"] == team_name) &
                events_df["location"].isNotNull()
            )
            
            # Convert back to Python for visualization
            player_events = [event.asDict() for event in player_events_df.collect()]
        else:
            # Use original implementation for smaller datasets
            # Filter events for the specific player
            player_events = []
            for event in events:
                if (event.get('player', {}).get('name') == player_name and 
                    event.get('team', {}).get('name') == team_name and
                    'location' in event):
                    player_events.append(event)
        
        if not player_events:
            # If no events found, create empty visualization with a message
            plt.figure(figsize=(10, 7), facecolor=self.viz_config['pitch_color'])
            ax = plt.subplot(1, 1, 1)
            self.draw_pitch(ax)
            plt.text(60, 40, f"No position data for {player_name}", 
                     ha='center', va='center', color=self.viz_config['text_color'], fontsize=16)
            
            # Save figure as base64 for HTML embedding
            with BytesIO() as buffer:
                plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', facecolor=self.viz_config['pitch_color'])
                plt.close()
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Extract x, y coordinates
        x_coords = []
        y_coords = []
        for event in player_events:
            if isinstance(event['location'], list) and len(event['location']) >= 2:
                x_coords.append(event['location'][0])
                y_coords.append(event['location'][1])
        
        # Create figure
        plt.figure(figsize=(10, 7), facecolor=self.viz_config['pitch_color'])
        ax = plt.subplot(1, 1, 1)
        
        # Draw the football pitch
        self.draw_pitch(ax)
        
        # Add title
        plt.title(f"{player_name} - Position Heatmap", color=self.viz_config['text_color'], fontsize=16, fontweight='bold')
        
        # If we have enough points, create a heatmap
        if len(x_coords) > 5:
            # Create a 2D histogram
            heatmap, xedges, yedges = np.histogram2d(
                x_coords, y_coords, bins=(12, 8), 
                range=[[0, 120], [0, 80]]
            )
            
            # Smooth the heatmap
            heatmap = gaussian_filter(heatmap, sigma=1.5)
            
            # Create event coordinates for contourf plotting
            x_pos, y_pos = np.meshgrid(
                np.linspace(0, 120, heatmap.shape[0]),
                np.linspace(0, 80, heatmap.shape[1])
            )
            
            # Use better colormaps for the heatmap based on team
            cmap = self.viz_config['heatmap_home_cmap'] if team_name == self.config['home_team'] else self.viz_config['heatmap_away_cmap']
            
            # Plot the heatmap with enhanced colors
            contour = ax.contourf(
                x_pos, y_pos, heatmap.T, 
                cmap=cmap,
                alpha=0.75, levels=20
            )
            
            # Add colorbar with better styling
            cbar = plt.colorbar(contour, ax=ax)
            cbar.set_label('Event Density', color=self.viz_config['text_color'])
            cbar.ax.yaxis.set_tick_params(color=self.viz_config['text_color'])
            plt.setp(plt.getp(cbar.ax, 'yticklabels'), color=self.viz_config['text_color'])
        else:
            # If not enough points, just scatter plot them
            team_color = self.viz_config['home_color'] if team_name == self.config['home_team'] else self.viz_config['away_color']
            ax.scatter(x_coords, y_coords, c=team_color, s=100, alpha=0.7, edgecolors='white')
            
            plt.text(60, 10, f"Limited data points ({len(x_coords)})", 
                     ha='center', va='center', color=self.viz_config['text_color'], fontsize=10)
        
        # Plot event points
        team_color = self.viz_config['home_color'] if team_name == self.config['home_team'] else self.viz_config['away_color']
        ax.scatter(x_coords, y_coords, c=team_color, s=30, alpha=0.5, edgecolors='white')
                   
        # Add player info
        plt.figtext(0.5, 0.02, f"Events: {len(player_events)} | Team: {team_name}",
                    ha="center", color=self.viz_config['text_color'], fontsize=12)
                    
        # Save figure as base64 for HTML embedding with better background
        with BytesIO() as buffer:
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', 
                       facecolor=self.viz_config['pitch_color'], edgecolor='none')
            plt.close()
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def draw_pitch(self, ax):
        """Draw a football pitch on the matplotlib axis."""
        pitch_length, pitch_width = 120, 80
        ax.set_facecolor(self.config['pitch_color'])
        
        # Draw the outline
        ax.plot([0, 0, pitch_length, pitch_length, 0], 
                [0, pitch_width, pitch_width, 0, 0], 
                color=self.config['line_color'])
        
        # Draw halfway line
        ax.plot([pitch_length/2, pitch_length/2], 
                [0, pitch_width], 
                color=self.config['line_color'])
        
        # Draw center circle
        center_circle = plt.Circle((pitch_length/2, pitch_width/2), 9.15, 
                             color=self.config['line_color'], fill=False)
        ax.add_patch(center_circle)
        
        # Draw center spot
        center_spot = plt.Circle((pitch_length/2, pitch_width/2), 0.5, 
                           color=self.config['line_color'])
        ax.add_patch(center_spot)
        
        # Draw penalty areas
        ax.plot([16.5, 16.5], [24, 56], color=self.config['line_color'])
        ax.plot([0, 16.5], [24, 24], color=self.config['line_color'])
        ax.plot([0, 16.5], [56, 56], color=self.config['line_color'])
        
        ax.plot([pitch_length-16.5, pitch_length-16.5], [24, 56], color=self.config['line_color'])
        ax.plot([pitch_length, pitch_length-16.5], [24, 24], color=self.config['line_color'])
        ax.plot([pitch_length, pitch_length-16.5], [56, 56], color=self.config['line_color'])
        
        # Draw goal areas
        ax.plot([5.5, 5.5], [36, 44], color=self.config['line_color'])
        ax.plot([0, 5.5], [36, 36], color=self.config['line_color'])
        ax.plot([0, 5.5], [44, 44], color=self.config['line_color'])
        
        ax.plot([pitch_length-5.5, pitch_length-5.5], [36, 44], color=self.config['line_color'])
        ax.plot([pitch_length, pitch_length-5.5], [36, 36], color=self.config['line_color'])
        ax.plot([pitch_length, pitch_length-5.5], [44, 44], color=self.config['line_color'])
        
        # Draw penalty spots
        penalty_spot1 = plt.Circle((11, pitch_width/2), 0.5, color=self.config['line_color'])
        penalty_spot2 = plt.Circle((pitch_length-11, pitch_width/2), 0.5, color=self.config['line_color'])
        ax.add_patch(penalty_spot1)
        ax.add_patch(penalty_spot2)
        
        # Set limits and hide axes
        ax.set_xlim(-5, pitch_length+5)
        ax.set_ylim(-5, pitch_width+5)
        ax.axis('off')
        
        return ax
    
    def create_shot_map(self, events: List[Dict], team_name: str) -> str:
        """Create a shot map visualization for a team."""
        # Use Spark for large datasets
        if len(events) > 10000:
            # Convert to Spark DataFrame
            events_df = self.spark.createDataFrame(events)
            
            # Filter for shots by the team
            shot_events_df = events_df.filter(
                (events_df["type.name"] == "Shot") & 
                (events_df["team.name"] == team_name) &
                events_df["location"].isNotNull()
            )
            
            # Convert back to Python for visualization
            shots = [event.asDict() for event in shot_events_df.collect()]
        else:
            # Use original implementation for smaller datasets
            # Filter shot events for the team
            shots = []
            for event in events:
                if (event.get('type', {}).get('name') == 'Shot' and 
                    event.get('team', {}).get('name') == team_name and
                    'location' in event):
                    shots.append(event)
                
        # Create figure with enhanced background
        plt.figure(figsize=(10, 7), facecolor=self.viz_config['pitch_color'])
        ax = plt.subplot(1, 1, 1)
        
        # Draw the football pitch
        self.draw_pitch(ax)
        
        # Add title with enhanced styling
        plt.title(f"{team_name} - Shot Map", color=self.viz_config['text_color'], 
                 fontsize=16, fontweight='bold')
        
        # Add shots to the plot with enhanced colors
        for shot in shots:
            x, y = shot['location'][0], shot['location'][1]
            is_goal = shot.get('shot', {}).get('outcome', {}).get('name') == 'Goal'
            xg = shot.get('shot', {}).get('statsbomb_xg', 0)
            
            # Size based on xG (slightly larger for better visibility)
            size = 120 + (xg * 1000)
            
            # Color based on outcome with enhanced colors
            color = self.viz_config['shot_goal_color'] if is_goal else self.viz_config['shot_miss_color']
            
            # Plot the shot with white border for better visibility
            ax.scatter(x, y, s=size, alpha=0.8, color=color, edgecolors='white', linewidths=1.5)
            
            # Add xG label if significant with improved visibility
            if xg > 0.1:
                plt.text(x, y, f"{xg:.2f}", ha='center', va='center', 
                         color='white', fontsize=9, fontweight='bold')
                
        # Add legend with enhanced styling
        goal_marker = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.viz_config['shot_goal_color'], 
                                markersize=10, label='Goal')
        miss_marker = plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=self.viz_config['shot_miss_color'], 
                                markersize=10, label='No Goal')
        legend = ax.legend(handles=[goal_marker, miss_marker], loc='lower center')
        plt.setp(legend.get_texts(), color=self.viz_config['text_color'])
        
        # Add shot count with enhanced styling
        goals = sum(1 for s in shots if s.get('shot', {}).get('outcome', {}).get('name') == 'Goal')
        plt.figtext(0.5, 0.02, f"Total Shots: {len(shots)} | Goals: {goals}",
                    ha="center", color=self.viz_config['text_color'], fontsize=12)
                    
        # Save figure as base64 for HTML embedding with enhanced background
        with BytesIO() as buffer:
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight',
                       facecolor=self.viz_config['pitch_color'], edgecolor='none')
            plt.close()
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def get_player_summary(self, player_stats: List[Dict]) -> str:
        """Create a simple text summary of player performance."""
        if not player_stats:
            return "No player data available."
            
        # Find top performers
        top_passer = max(player_stats, key=lambda x: x['passes']) if player_stats else None
        top_shooters = [p for p in player_stats if p['shots'] > 0]
        top_shooter = max(top_shooters, key=lambda x: x['shots']) if top_shooters else None
        goal_scorers = [p for p in player_stats if p['goals'] > 0]
        top_scorer = max(goal_scorers, key=lambda x: x['goals']) if goal_scorers else None
        
        summary = []
        if top_passer:
            summary.append(f"Top passer: {top_passer['player_name']} with {top_passer['passes']} passes " + 
                          f"({top_passer['pass_completion']}% completion)")
        
        if top_shooter:
            summary.append(f"Most shots: {top_shooter['player_name']} with {top_shooter['shots']} shots " + 
                          f"(xG: {top_shooter['xg']})")
            
        if top_scorer:
            summary.append(f"Top scorer: {top_scorer['player_name']} with {top_scorer['goals']} goals " + 
                          f"from {top_scorer['shots']} shots")
            
        return "\n".join(summary) if summary else "No significant statistics to highlight."
        
    def analyze_match(self, file_path: str, player_name: str = None):
        """Perform complete match analysis and return results."""
        # Load data
        events = self.load_data(file_path)
        if events is None:
            return {"error": "Failed to load match data."}
            
        # Extract match details
        match_details = self.extract_match_details(events)
        home_team = match_details["home_team"]
        away_team = match_details["away_team"]
        
        # Store team names for other methods to use
        self.config['home_team'] = home_team
        self.config['away_team'] = away_team
        
        # Calculate match statistics
        match_stats = self.calculate_match_stats(events, home_team, away_team)
        
        # Get player statistics
        home_player_stats = self.get_player_stats(events, home_team)
        away_player_stats = self.get_player_stats(events, away_team)
        
        # Create visualization
        match_visualization = self.create_match_visualization(match_details, match_stats)
        
        # Create shot maps
        home_shot_map = self.create_shot_map(events, home_team)
        away_shot_map = self.create_shot_map(events, away_team)
        
        # Create player heatmap if requested
        player_heatmap = None
        player_team = None
        if player_name:
            # Determine which team the player is on
            home_players = [p['player_name'] for p in home_player_stats]
            away_players = [p['player_name'] for p in away_player_stats]
            
            if player_name in home_players:
                player_heatmap = self.create_player_heatmap(events, player_name, home_team)
                player_team = home_team
            elif player_name in away_players:
                player_heatmap = self.create_player_heatmap(events, player_name, away_team)
                player_team = away_team
        
        # Generate player summaries
        home_summary = self.get_player_summary(home_player_stats)
        away_summary = self.get_player_summary(away_player_stats)
        
        # Return analysis results
        return {
            "match_details": match_details,
            "match_stats": match_stats,
            "home_player_stats": home_player_stats,
            "away_player_stats": away_player_stats,
            "home_summary": home_summary,
            "away_summary": away_summary,
            "match_visualization": match_visualization,
            "home_shot_map": home_shot_map,
            "away_shot_map": away_shot_map,
            "player_heatmap": player_heatmap,
            "player_name": player_name,
            "player_team": player_team
        }
    
    def __del__(self):
        """Clean up resources when the object is destroyed."""
        # Stop Spark session when the analyzer is destroyed
        if hasattr(self, 'spark'):
            self.spark.stop()
    
if __name__ == "__main__":
    # This is a standalone test mode for the analyzer
    # For web application usage, the analyzer is called via server.py
    import sys
    
    analyzer = FootballMatchAnalyzer()
    
    # Allow file path as command line argument
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Default to an example file in the uploads folder if available
        available_files = [f for f in os.listdir('uploads') if f.endswith('.json')]
        if available_files:
            file_path = os.path.join('uploads', available_files[0])
            print(f"Using default file: {file_path}")
        else:
            print("No JSON files found in uploads folder. Please specify a file path.")
            sys.exit(1)
    
    # Optional player name as second argument
    player_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Analyzing match file: {file_path}{' for player: ' + player_name if player_name else ''}")
    analysis_results = analyzer.analyze_match(file_path, player_name)
    print(f"Analysis complete for {file_path}")
    
    # Print a summary of the results
    if "error" not in analysis_results:
        match_details = analysis_results["match_details"]
        match_stats = analysis_results["match_stats"]
        print(f"\nMatch: {match_details['home_team']} vs {match_details['away_team']}")
        print(f"Score: {match_stats['goals']['home']} - {match_stats['goals']['away']}")
        print(f"Possession: {match_stats['possession']['home']}% - {match_stats['possession']['away']}%")
    else:
        print(f"Error: {analysis_results['error']}")
    
    # Clean up Spark session
    analyzer.spark.stop()
