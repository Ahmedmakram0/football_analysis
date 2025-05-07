from flask import Flask, request, jsonify, send_from_directory, render_template, redirect, url_for
import os
from football_analysis import FootballMatchAnalyzer

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'json'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Create a static folder structure if it doesn't exist
os.makedirs('static', exist_ok=True)

# Initialize analyzer
analyzer = FootballMatchAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get list of available JSON files
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.json')]
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return redirect(url_for('index'))
    return 'Invalid file type', 400

@app.route('/analyze', methods=['GET'])
def analyze():
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    if not filename:
        return 'Filename required', 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return 'File not found', 404
    
    # Run analysis
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return result['error'], 500
    
    # Return HTML visualization
    return render_template('analysis.html', 
                          result=result, 
                          filename=filename,
                          match_details=result['match_details'],
                          match_stats=result['match_stats'],
                          home_players=result['home_player_stats'],
                          away_players=result['away_player_stats'],
                          player_name=player_name)

@app.route('/player_analysis', methods=['GET'])
def player_analysis():
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    if not filename or not player_name:
        return 'Filename and player name required', 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return 'File not found', 404
    
    # Run analysis with player focus
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return result['error'], 500
    
    # Return HTML visualization focusing on the player
    return render_template('player_analysis.html', 
                          result=result, 
                          filename=filename,
                          player_name=player_name)

@app.route('/api/analyze', methods=['GET'])
def api_analyze():
    """JSON API endpoint for programmatic access"""
    filename = request.args.get('filename')
    player_name = request.args.get('player_name')
    
    if not filename:
        return jsonify({'error': 'Filename required'}), 400
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # Run analysis
    result = analyzer.analyze_match(filepath, player_name)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500
    
    return jsonify(result)

@app.route('/list_files', methods=['GET'])
def list_files():
    """API endpoint to list available JSON files"""
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith('.json')]
    return jsonify(files)

if __name__ == '__main__':
    # Make sure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    app.run(debug=True)
