#!/usr/bin/env python3
"""
Containerized Web-based YAML Editor for services.yaml
A Flask application that provides a web interface to edit a YAML file
with syntax validation and backup functionality - optimized for Docker.
"""

from flask import Flask, render_template, request, jsonify
import yaml
import os
import shutil
import hashlib
from datetime import datetime
import logging
from pathlib import Path

app = Flask(__name__, template_folder='../templates')

# Configuration - Using environment variables for containerization
YAML_FILE_PATH = os.getenv('YAML_FILE_PATH', '/data/services.yaml')
BACKUP_DIR = os.getenv('BACKUP_DIR', '/data/backups')
PORT = int(os.getenv('PORT', 8080))
HOST = os.getenv('HOST', '0.0.0.0')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Create necessary directories if they don't exist"""
    try:
        os.makedirs(os.path.dirname(YAML_FILE_PATH), exist_ok=True)
        os.makedirs(BACKUP_DIR, exist_ok=True)
        logger.info(f"Directories ensured: {os.path.dirname(YAML_FILE_PATH)}, {BACKUP_DIR}")
    except Exception as e:
        logger.error(f"Error creating directories: {e}")

def get_file_hash(content):
    """Get SHA256 hash of content for comparison"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def create_backup():
    """Create a timestamped backup of the current YAML file"""
    try:
        if os.path.exists(YAML_FILE_PATH):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"services_{timestamp}.yaml"
            backup_path = os.path.join(BACKUP_DIR, backup_filename)
            shutil.copy2(YAML_FILE_PATH, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_filename
        return None
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return None

def content_changed(new_content):
    """Check if the new content is different from the current file"""
    try:
        if os.path.exists(YAML_FILE_PATH):
            with open(YAML_FILE_PATH, 'r', encoding='utf-8') as f:
                current_content = f.read()
            return get_file_hash(new_content) != get_file_hash(current_content)
        return True  # File doesn't exist, so it's a change
    except Exception as e:
        logger.error(f"Error checking file changes: {e}")
        return True  # Assume changed if we can't check

def validate_yaml(content):
    """Validate YAML syntax and return any errors"""
    try:
        yaml.safe_load(content)
        return True, None
    except yaml.YAMLError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def read_yaml_file():
    """Read the YAML file content"""
    try:
        if os.path.exists(YAML_FILE_PATH):
            with open(YAML_FILE_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
                logger.info(f"Successfully read YAML file: {len(content)} characters")
                return content
        else:
            # Create empty file if it doesn't exist
            default_content = """# Homepage Services Configuration
# This file defines the services displayed on your homepage dashboard
# Documentation: https://gethomepage.dev/en/configs/services/

# Example service configuration:
# - Group Name:
#     - Service Name:
#         href: http://localhost:8080
#         description: Service description
#         icon: service-icon

- Development:
    - YAML Editor:
        href: http://localhost:8080
        description: Edit services configuration
        icon: mdi-pencil

# Add your services below:
"""
            with open(YAML_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(default_content)
            logger.info(f"Created new YAML file with default content")
            return default_content
    except Exception as e:
        logger.error(f"Error reading YAML file: {e}")
        return f"# Error reading file: {e}\n# Please check file permissions and try again.\n"

def write_yaml_file(content):
    """Write content to the YAML file"""
    try:
        with open(YAML_FILE_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Successfully wrote YAML file: {len(content)} characters")
        return True, None
    except Exception as e:
        logger.error(f"Error writing YAML file: {e}")
        return False, str(e)

@app.route('/')
def index():
    """Main editor page"""
    content = read_yaml_file()
    return render_template('editor.html', content=content, file_path=YAML_FILE_PATH)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Basic health checks
        yaml_exists = os.path.exists(YAML_FILE_PATH)
        backup_dir_exists = os.path.exists(BACKUP_DIR)
        
        return jsonify({
            'status': 'healthy',
            'yaml_file_exists': yaml_exists,
            'backup_dir_exists': backup_dir_exists,
            'yaml_file_path': YAML_FILE_PATH,
            'backup_dir': BACKUP_DIR
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/validate', methods=['POST'])
def validate():
    """Validate YAML content"""
    try:
        content = request.json.get('content', '')
        is_valid, error = validate_yaml(content)
        return jsonify({
            'valid': is_valid,
            'error': error
        })
    except Exception as e:
        logger.error(f"Validation error: {e}")
        return jsonify({
            'valid': False,
            'error': f'Server error during validation: {str(e)}'
        }), 500

@app.route('/save', methods=['POST'])
def save():
    """Save the YAML content"""
    try:
        content = request.json.get('content', '')
        
        # Validate first
        is_valid, error = validate_yaml(content)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'YAML syntax error: {error}'
            }), 400
        
        # Check if content has actually changed
        if not content_changed(content):
            logger.info("No changes detected, skipping save and backup")
            return jsonify({
                'success': True,
                'message': 'No changes detected - file already up to date',
                'no_changes': True
            })
        
        # Create backup before saving
        backup_name = create_backup()
        
        # Save the file
        success, error = write_yaml_file(content)
        
        if success:
            message = 'File saved successfully.'
            if backup_name:
                message += f' Backup created: {backup_name}'
            logger.info(f"File saved with changes. Backup: {backup_name}")
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Error saving file: {error}'
            }), 500
    except Exception as e:
        logger.error(f"Save error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error during save: {str(e)}'
        }), 500

@app.route('/reload')
def reload():
    """Reload the file content"""
    try:
        content = read_yaml_file()
        return jsonify({'content': content})
    except Exception as e:
        logger.error(f"Reload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/backups')
def list_backups():
    """List available backups"""
    try:
        backups = []
        if os.path.exists(BACKUP_DIR):
            for filename in sorted(os.listdir(BACKUP_DIR), reverse=True):
                if filename.endswith('.yaml'):
                    filepath = os.path.join(BACKUP_DIR, filename)
                    if os.path.isfile(filepath):
                        stat = os.stat(filepath)
                        backups.append({
                            'filename': filename,
                            'size': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        })
        return jsonify({'backups': backups})
    except Exception as e:
        logger.error(f"List backups error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/restore/<filename>')
def restore_backup(filename):
    """Restore from a backup file"""
    try:
        # Security check - ensure filename is safe
        if '..' in filename or '/' in filename or not filename.endswith('.yaml'):
            return jsonify({'error': 'Invalid filename'}), 400
            
        backup_path = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(backup_path):
            return jsonify({'error': 'Backup file not found'}), 404
        
        # Create a backup of current file before restoring
        current_backup = create_backup()
        
        # Copy backup to main file
        shutil.copy2(backup_path, YAML_FILE_PATH)
        
        # Read the restored content
        content = read_yaml_file()
        
        message = f'Restored from backup: {filename}'
        if current_backup:
            message += f'. Current version backed up as: {current_backup}'
            
        return jsonify({
            'success': True,
            'content': content,
            'message': message
        })
    except Exception as e:
        logger.error(f"Restore backup error: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info(f"Starting YAML Editor on {HOST}:{PORT}")
    logger.info(f"Target file: {YAML_FILE_PATH}")
    logger.info(f"Backup directory: {BACKUP_DIR}")
    
    ensure_directories()
    
    # Run the app
    app.run(host=HOST, port=PORT, debug=False, threaded=True)
