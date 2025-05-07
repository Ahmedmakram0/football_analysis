"""
Football Match Analysis Web Application
---------------------------------------
This Flask web application allows users to upload, view, and analyze football match data 
stored in JSON format. The app provides both web UI and API endpoints for data analysis.
"""

# Import required libraries
from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for
import os
from football_analysis import FootballMatchAnalyzer

# Configuration constants
UPLOAD_FOLDER = 'uploads'  # Folder where uploaded JSON files will be stored
ALLOWED_EXTENSIONS = {'json'}  # Only allow JSON file uploads

# Initialize Flask application
app = Flask(__name__)
# Configure application settings
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Set the upload directory
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size to prevent server overload

# Create required directory structure
# 'static' folder is used by Flask to serve static files like CSS, JavaScript, images
os.makedirs('static', exist_ok=True)

# Initialize the analyzer that will process football match data
analyzer = FootballMatchAnalyzer()

# Helper function to validate file extensions
def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension (.json)
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ENDPOINT: Home page
@app.route('/')
def index():
    """
    Home page endpoint that displays a list of available JSON files for analysis
    
    Returns:
        HTML: Rendered index.html template with list of available files
    """
    # Get list of available JSON files from the uploads folder
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.json')]
    return render_template('index.html', files=files)

# ENDPOINT: File upload handler
@app.route('/upload', methods=['POST'])
def upload_file():
    """
    Handles file uploads from the web interface
    
    Returns:
        Redirect to index page on success
        Error message with status code on failure
    """
    # Check if the request contains a file part
    if 'file' not in request.files:
        return 'No file part', 400
    
    file = request.files['file']
    
    # Check if a file was actually selected
    if file.filename == '':
        return 'No selected file', 400
    
    # Validate and save the file
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Redirect back to the index page after successful upload
        return redirect(url_for('index'))
    
    return 'Invalid file type', 400

# ENDPOINT: Match analysis page
@app.route('/analyze', methods=['GET'])
def analyze():
    """
    Generates and displays match analysis results
    
    Query Parameters:
        filename (str): Name of the JSON file to analyze
        player_name (str, optional): Player to focus analysis on
    
    Returns:
        HTML: Rendered analysis.html template with match statistics
        Error message with status code on failure
    """
    # Get query parameters
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    # Validate required parameters
    if not filename:
        return 'Filename required', 400
    
    # Construct file path and check if file exists
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return 'File not found', 404
    
    # Run analysis using the FootballMatchAnalyzer
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return result['error'], 500
    
    # Return HTML visualization with all match data
    return render_template('analysis.html', 
                          result=result, 
                          filename=filename,
                          match_details=result['match_details'],
                          match_stats=result['match_stats'],
                          home_players=result['home_player_stats'],
                          away_players=result['away_player_stats'],
                          player_name=player_name)

# ENDPOINT: Individual player analysis page
@app.route('/player_analysis', methods=['GET'])
def player_analysis():
    """
    Generates and displays analysis focused on a specific player
    
    Query Parameters:
        filename (str): Name of the JSON file to analyze
        player_name (str): Player to focus analysis on
    
    Returns:
        HTML: Rendered player_analysis.html template with player-focused statistics
        Error message with status code on failure
    """
    # Get query parameters
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    # Validate required parameters - both filename and player_name are required
    if not filename or not player_name:
        return 'Filename and player name required', 400
    
    # Construct file path and check if file exists
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return 'File not found', 404
    
    # Run analysis with player focus using the FootballMatchAnalyzer
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return result['error'], 500
    
    # Return HTML visualization focused on the specific player
    return render_template('player_analysis.html', 
                          result=result, 
                          filename=filename,
                          player_name=player_name)

# ENDPOINT: API for programmatic access to analysis
@app.route('/api/analyze', methods=['GET'])
def api_analyze():
    """
    JSON API endpoint for programmatic access to match analysis
    
    Query Parameters:
        filename (str): Name of the JSON file to analyze
        player_name (str, optional): Player to focus analysis on
    
    Returns:
        JSON: Analysis results as JSON data
        JSON error object with status code on failure
    """
    # Get query parameters
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    # Validate required parameters
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    # Construct file path and check if file exists
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # Run analysis using the FootballMatchAnalyzer
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500
    
    # Return the full analysis results as JSON for API clients
    return jsonify(result)

# ENDPOINT: API to list available files
@app.route('/list_files', methods=['GET'])
def list_files():
    """
    API endpoint to list all available JSON files for analysis
    
    Returns:
        JSON: Array of filenames available in the uploads folder
    """
    # Get list of JSON files from uploads folder
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.json')]
    return jsonify(files)

# Application entry point
if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True)
