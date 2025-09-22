# Homepage Editor

A web-based YAML editor specifically designed for editing [Homepage](https://gethomepage.dev/) services configuration files. Features real-time YAML validation, automatic backups, and a clean, modern interface.

## Features

- **Real-time YAML validation** with detailed error messages
- **Automatic timestamped backups** before every save
- **Duplicate save detection** - won't create unnecessary backups
- **Message history** - track all your editing activity
- **One-click backup restoration** - easily restore from any previous version
- **Responsive design** - works on desktop and mobile
- **Docker-ready** - simple deployment with Docker Compose
- **Secure** - runs as non-root user with proper permissions

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Create a docker-compose.yml file:**
```yaml
version: '3.8'

services:
  homepage-editor:
    image: your-registry/homepage-editor:latest
    container_name: homepage-editor
    ports:
      - "8080:8080"
    volumes:
      - ./homepage/config/services.yaml:/data/services.yaml
      - ./homepage/config/backups:/data/backups
    environment:
      - YAML_FILE_PATH=/data/services.yaml
      - BACKUP_DIR=/data/backups
      - PORT=8080
      - HOST=0.0.0.0
      - FLASK_ENV=production
    user: "1000:1000"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/health').read()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

2. **Start the container:**
```bash
docker-compose up -d
```

3. **Open your browser:** http://localhost:8080

### Option 2: Docker Run

```bash
docker run -d \
  --name homepage-editor \
  -p 8080:8080 \
  -v $(pwd)/services.yaml:/data/services.yaml \
  -v $(pwd)/backups:/data/backups \
  --user 1000:1000 \
  --restart unless-stopped \
  your-registry/homepage-editor:latest
```

### Option 3: Build from Source

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/homepage-editor.git
cd homepage-editor
```

2. **Build and run:**
```bash
docker-compose build
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `YAML_FILE_PATH` | `/data/services.yaml` | Path to your services.yaml file inside container |
| `BACKUP_DIR` | `/data/backups` | Directory for backup files |
| `PORT` | `8080` | Port the web server listens on |
| `HOST` | `0.0.0.0` | Host interface to bind to |

### Volume Mounts

- **services.yaml**: Your Homepage services configuration file
- **backups directory**: Automatic backup storage location

### User Permissions

The container runs as user ID 1000. Make sure your mounted files are accessible:

```bash
# Fix permissions if needed
sudo chown -R 1000:1000 ./homepage/config/
sudo chmod 755 ./homepage/config/backups
```

## Usage

### Web Interface

- **Edit** your YAML in the main editor area
- **Real-time validation** shows status in the top bar
- **Save** with Ctrl+S or the Save button  
- **Reload** from disk with Ctrl+R or Reload button
- **View history** click the History button to see recent messages
- **Restore backups** click any backup in the sidebar to restore

### Keyboard Shortcuts

- `Ctrl+S` (or `Cmd+S`): Save file
- `Ctrl+R` (or `Cmd+R`): Reload file from disk

### Message Types

- **Green**: Successful save with backup created
- **Blue**: No changes detected (duplicate save)
- **Red**: Error occurred (YAML invalid, permissions, etc.)

## Integration with Homepage

This editor works seamlessly with your existing Homepage setup. Simply mount your Homepage's `services.yaml` file and backup directory:

```yaml
# In your existing Homepage docker-compose.yml
services:
  homepage:
    # ... your existing homepage config ...
    
  homepage-editor:
    image: your-registry/homepage-editor:latest
    ports:
      - "8080:8080"
    volumes:
      - ./homepage/config/services.yaml:/data/services.yaml
      - ./homepage/config/backups:/data/backups
    user: "1000:1000"
    restart: unless-stopped
```

## Development

### Building Locally

```bash
git clone https://github.com/your-username/homepage-editor.git
cd homepage-editor
docker build -t homepage-editor:local .
```

### File Structure

```
homepage-editor/
├── app/
│   └── yaml_editor.py          # Flask application
├── templates/
│   └── editor.html             # Web interface
├── Dockerfile                  # Container definition
├── docker-compose.yml          # Docker Compose config
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with `docker-compose up --build`
5. Submit a pull request

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose logs homepage-editor

# Common issues:
# - Port 8080 already in use
# - File permission problems
# - Invalid volume paths
```

### Can't Save Files
```bash
# Fix file permissions
sudo chown 1000:1000 /path/to/your/services.yaml
sudo chmod 755 /path/to/your/backup/directory
```

### Health Check Failing
```bash
# Test health endpoint
curl http://localhost:8080/health

# Should return:
# {"status":"healthy","yaml_file_exists":true,...}
```

## Security

- Runs as non-root user (UID 1000)
- No external network access required
- Only accesses mounted files
- Built-in health monitoring
- Input validation and sanitization

## Homepage Services Format

Your services.yaml should follow the Homepage format:

```yaml
- Infrastructure:
    - Service Name:
        href: http://localhost:8080
        description: Service description
        icon: service-icon
        ping: optional-ping-host
        widget:
          type: service-type
          # widget-specific config

- Development:
    - Another Service:
        href: https://example.com
        description: Another service
        icon: mdi-example
```

## License

MIT License - see LICENSE file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/homepage-editor/issues)
- **Documentation**: [Homepage Docs](https://gethomepage.dev/en/configs/services/)
- **Docker Hub**: [your-registry/homepage-editor](https://hub.docker.com/r/your-registry/homepage-editor)

---

Built for the [Homepage](https://gethomepage.dev/) community ❤️
