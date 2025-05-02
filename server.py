from flask import Flask, request, jsonify, send_from_directory
import os
import webbrowser
from threading import Timer
from flask_cors import CORS
from football_analysis import FootballMatchAnalyzer
from werkzeug.utils import secure_filename
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)  # Enable CORS for all routes

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize analyzer once to avoid recreating it for each request
analyzer = FootballMatchAnalyzer()

@app.route('/', methods=['GET'])
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/list-files', methods=['GET'])
def list_files():
    # Get JSON files from root directory
    root_files = glob.glob('*.json')
    
    # Get JSON files from uploads directory
    upload_files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.json')]
    
    # Combine the lists
    all_files = root_files + upload_files
    
    return jsonify({
        "files": all_files
    })

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    
    # If user does not select file, browser also submits an empty file
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        # Secure the filename to prevent security issues
        filename = secure_filename(file.filename)
        
        # Save the file to the upload folder
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        logger.info(f"File uploaded successfully: {file_path}")
        return jsonify({
            "message": "File successfully uploaded",
            "file_path": file_path
        })

@app.route('/analyze', methods=['GET'])
def analyze_match():
    # Get file path from query parameter
    file_path = request.args.get('file')
    
    # Get player name if provided
    player_name = request.args.get('player')
    
    if not file_path:
        return jsonify({"error": "No file specified"}), 400
    
    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({"error": f"File {file_path} not found"}), 404
    
    try:
        logger.info(f"Analyzing match file: {file_path} {' for player: ' + player_name if player_name else ''}")
        
        # Analyze the match
        results = analyzer.analyze_match(file_path, player_name)
        
        logger.info(f"Analysis complete for: {file_path}")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error analyzing match: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def open_browser():
    webbrowser.open('http://localhost:5000/')

if __name__ == '__main__':
    # Open browser after a short delay to ensure server is running
    Timer(1.0, open_browser).start()
    
    # Run with threaded=False to avoid thread-related issues with matplotlib
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=False)