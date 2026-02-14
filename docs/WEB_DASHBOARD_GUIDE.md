# Web Dashboard Guide

## Overview

The Web Dashboard provides a browser-based interface for monitoring and controlling the EkoVision detection system. Access the system from any device on your network without needing to install software.

## Features

- **Live Video Stream**: Real-time video feed with annotations via WebSocket
- **System Statistics**: FPS, classifications, tracks, reduction percentage
- **Performance Metrics**: GPU/CPU usage, VRAM, frame time breakdown
- **Active Tracks**: View all currently tracked bottles with classifications
- **Control Panel**: Reset, toggle zone, export data, record video
- **Recent Exports**: Download CSV/JSON exports directly from browser
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Updates**: WebSocket-based live data streaming

## Quick Start

### Start Dashboard

```bash
python run_web_dashboard.py
```

### Access Dashboard

Open your browser and navigate to:

```
http://localhost:5000
```

Or from another device on the same network:

```
http://<your-ip-address>:5000
```

## Installation

### Dependencies

The web dashboard requires additional packages:

```bash
pip install flask flask-socketio python-socketio
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "import flask, flask_socketio; print('✓ Web dashboard dependencies installed')"
```

## Configuration

### Port Configuration

Edit `run_web_dashboard.py` to change the port:

```python
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
```

### Network Access

**Local Only** (default):

```python
socketio.run(app, host='127.0.0.1', port=5000)
```

**Network Access**:

```python
socketio.run(app, host='0.0.0.0', port=5000)
```

**Custom Port**:

```python
socketio.run(app, host='0.0.0.0', port=8080)
```

## Dashboard Interface

### Main Sections

#### 1. Video Feed

- **Location**: Top center
- **Features**:
  - Live video stream with bounding boxes
  - Color-coded tracks (yellow/cyan/green/red)
  - Trigger zone overlay
  - FPS counter
- **Controls**:
  - Click to focus
  - Fullscreen mode (browser feature)

#### 2. System Statistics

- **Location**: Top right
- **Metrics**:
  - Current FPS
  - Total frames processed
  - Total classifications
  - Computational reduction %
  - Active tracks count
  - Cache hit rate

#### 3. Performance Metrics

- **Location**: Middle right
- **Metrics**:
  - GPU usage (%)
  - CPU usage (%)
  - VRAM usage (GB)
  - Frame time breakdown:
    - Detection time
    - Tracking time
    - Classification time
    - Rendering time

#### 4. Active Tracks

- **Location**: Bottom right
- **Display**:
  - Track ID
  - State (NEW/TRACKED/CLASSIFIED/FAILED)
  - Classification results (8 attributes)
  - Confidence score
  - Position (bbox)

#### 5. Control Panel

- **Location**: Bottom left
- **Buttons**:
  - **Reset Pipeline**: Clear cache and tracking
  - **Toggle Zone**: Show/hide trigger zone
  - **Export CSV**: Download detection data
  - **Export JSON**: Download classification data
  - **Start/Stop Recording**: Toggle video recording

#### 6. Recent Exports

- **Location**: Bottom center
- **Features**:
  - List of recent exports (CSV/JSON/Video)
  - Download links
  - File size and timestamp
  - Auto-refresh on new exports

## Usage Examples

### Example 1: Remote Monitoring

Monitor the system from your phone or tablet:

1. Start dashboard on main computer:

   ```bash
   python run_web_dashboard.py
   ```

2. Find your computer's IP address:

   ```bash
   # Windows
   ipconfig

   # Linux/Mac
   ifconfig
   ```

3. Open browser on mobile device:

   ```
   http://192.168.1.100:5000
   ```

4. View live feed and statistics

### Example 2: Export Data Remotely

Export and download data without physical access:

1. Open dashboard in browser
2. Click "Export CSV" button
3. Wait for export to complete
4. Click download link in "Recent Exports" section
5. File downloads to your device

### Example 3: Multi-User Monitoring

Multiple users can view the same system:

1. Start dashboard once
2. Share URL with team members
3. Each user opens dashboard in their browser
4. All users see the same live feed
5. Controls work for all users (be careful!)

### Example 4: Production Monitoring

Set up dashboard for production monitoring:

1. Configure network access (0.0.0.0)
2. Set up firewall rules for port 5000
3. Create bookmark for easy access
4. Monitor from control room
5. Export data periodically

## API Endpoints

### HTTP Endpoints

#### GET /

Main dashboard page

#### GET /video_feed

MJPEG video stream

#### POST /api/reset

Reset pipeline

```bash
curl -X POST http://localhost:5000/api/reset
```

#### POST /api/toggle_zone

Toggle trigger zone visibility

```bash
curl -X POST http://localhost:5000/api/toggle_zone
```

#### POST /api/export_csv

Export CSV data

```bash
curl -X POST http://localhost:5000/api/export_csv
```

#### POST /api/export_json

Export JSON data

```bash
curl -X POST http://localhost:5000/api/export_json
```

#### POST /api/toggle_recording

Toggle video recording

```bash
curl -X POST http://localhost:5000/api/toggle_recording
```

#### GET /api/stats

Get current statistics (JSON)

```bash
curl http://localhost:5000/api/stats
```

#### GET /api/exports

List recent exports (JSON)

```bash
curl http://localhost:5000/api/exports
```

#### GET /download/<filename>

Download export file

```bash
curl -O http://localhost:5000/download/ekovision_2026-02-12_10-30-45.csv
```

### WebSocket Events

#### Client → Server

**connect**: Client connected

```javascript
socket.on("connect", function () {
  console.log("Connected to server");
});
```

**disconnect**: Client disconnected

#### Server → Client

**stats_update**: System statistics update (every 1 second)

```javascript
socket.on("stats_update", function (data) {
  // data = {fps, frames, classifications, reduction, ...}
});
```

**tracks_update**: Active tracks update (every 1 second)

```javascript
socket.on("tracks_update", function (data) {
  // data = [{track_id, state, classification, ...}, ...]
});
```

**performance_update**: Performance metrics update (every 1 second)

```javascript
socket.on("performance_update", function (data) {
  // data = {gpu_usage, cpu_usage, vram, frame_times, ...}
});
```

**export_complete**: Export operation completed

```javascript
socket.on("export_complete", function (data) {
  // data = {type, filename, size}
});
```

## Security Considerations

### Network Security

**⚠️ WARNING**: The dashboard has no authentication by default.

**Recommendations**:

1. **Firewall**: Restrict access to trusted IPs
2. **VPN**: Use VPN for remote access
3. **Reverse Proxy**: Use nginx with authentication
4. **HTTPS**: Use SSL/TLS for encrypted connections

### Firewall Configuration

**Windows Firewall**:

```powershell
netsh advfirewall firewall add rule name="EkoVision Dashboard" dir=in action=allow protocol=TCP localport=5000
```

**Linux (ufw)**:

```bash
sudo ufw allow 5000/tcp
```

**Linux (iptables)**:

```bash
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
```

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name ekovision.local;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Performance Considerations

### Network Bandwidth

Video streaming requires bandwidth:

| Quality | Resolution | FPS | Bandwidth |
| ------- | ---------- | --- | --------- |
| Low     | 320x240    | 10  | ~500 KB/s |
| Medium  | 640x480    | 15  | ~1.5 MB/s |
| High    | 1280x720   | 20  | ~3 MB/s   |

**Optimization**:

- Reduce frame rate for remote access
- Lower resolution for mobile devices
- Use local network for best performance

### Server Load

Dashboard adds minimal overhead:

| Component      | CPU Impact | Memory      |
| -------------- | ---------- | ----------- |
| Flask Server   | < 5%       | ~50 MB      |
| WebSocket      | < 2%       | ~20 MB      |
| Video Encoding | < 10%      | ~30 MB      |
| **Total**      | **< 17%**  | **~100 MB** |

### Concurrent Users

The dashboard supports multiple concurrent users:

| Users    | CPU Impact | Bandwidth |
| -------- | ---------- | --------- |
| 1 user   | Baseline   | 1x        |
| 2 users  | +5%        | 2x        |
| 5 users  | +15%       | 5x        |
| 10 users | +30%       | 10x       |

**Recommendation**: Limit to 5 concurrent users for best performance.

## Troubleshooting

### Dashboard Won't Start

**Problem**: `python run_web_dashboard.py` fails

**Solutions**:

1. Check dependencies:

   ```bash
   pip install flask flask-socketio python-socketio
   ```

2. Check port availability:

   ```bash
   # Windows
   netstat -ano | findstr :5000

   # Linux/Mac
   lsof -i :5000
   ```

3. Try different port:
   ```python
   socketio.run(app, port=8080)
   ```

### Cannot Access from Other Devices

**Problem**: Dashboard works on localhost but not from other devices

**Solutions**:

1. Check host setting:

   ```python
   socketio.run(app, host='0.0.0.0', port=5000)
   ```

2. Check firewall:

   ```bash
   # Windows: Allow port 5000
   # Linux: sudo ufw allow 5000
   ```

3. Verify IP address:
   ```bash
   # Use correct IP, not 127.0.0.1
   http://192.168.1.100:5000
   ```

### Video Feed Not Loading

**Problem**: Dashboard loads but video feed is black or not updating

**Solutions**:

1. Check camera connection
2. Restart dashboard
3. Check browser console for errors (F12)
4. Try different browser (Chrome recommended)
5. Clear browser cache

### WebSocket Connection Failed

**Problem**: "WebSocket connection failed" error

**Solutions**:

1. Check browser compatibility (use modern browser)
2. Disable browser extensions (ad blockers)
3. Check network connectivity
4. Restart dashboard server

### High CPU Usage

**Problem**: Dashboard causes high CPU usage

**Solutions**:

1. Reduce video frame rate
2. Lower video resolution
3. Limit concurrent users
4. Close unused browser tabs
5. Use hardware acceleration in browser

### Exports Not Appearing

**Problem**: Export buttons work but files don't appear

**Solutions**:

1. Check `exports/` directory exists
2. Verify write permissions
3. Check disk space
4. Refresh browser page
5. Check browser console for errors

## Advanced Features

### Custom Styling

Edit `src/web_dashboard/templates/index.html` to customize appearance:

```html
<style>
  :root {
    --primary-color: #2196f3; /* Change primary color */
    --background-color: #1a1a1a; /* Change background */
  }
</style>
```

### Custom Metrics

Add custom metrics to dashboard:

1. Edit `src/web_dashboard/app.py`
2. Add metric to stats dictionary
3. Emit via WebSocket
4. Update HTML template to display

### Integration with Other Systems

Use API endpoints to integrate with other systems:

```python
import requests

# Get statistics
response = requests.get('http://localhost:5000/api/stats')
stats = response.json()

# Export data
requests.post('http://localhost:5000/api/export_csv')

# Reset pipeline
requests.post('http://localhost:5000/api/reset')
```

## Mobile Access

### Responsive Design

Dashboard automatically adapts to mobile devices:

- **Portrait**: Stacked layout
- **Landscape**: Side-by-side layout
- **Touch**: Large buttons for easy tapping

### Mobile Optimization

For best mobile experience:

1. Use WiFi (not cellular data)
2. Reduce video quality
3. Close other apps
4. Use landscape orientation
5. Add to home screen for quick access

### Add to Home Screen

**iOS**:

1. Open dashboard in Safari
2. Tap Share button
3. Select "Add to Home Screen"

**Android**:

1. Open dashboard in Chrome
2. Tap menu (⋮)
3. Select "Add to Home screen"

## Best Practices

1. **Single Instance**: Run only one dashboard instance per system
2. **Network Security**: Use firewall and VPN for remote access
3. **Monitor Performance**: Check CPU/memory usage regularly
4. **Limit Users**: Keep concurrent users under 5
5. **Regular Exports**: Export data periodically to prevent data loss
6. **Browser Choice**: Use Chrome or Firefox for best compatibility
7. **Network Quality**: Use wired connection for main computer
8. **Backup Config**: Keep backup of configuration files

## FAQ

**Q: Can I access dashboard from the internet?**  
A: Not recommended without VPN or reverse proxy with authentication.

**Q: Does dashboard work offline?**  
A: Yes, but only on the local machine (localhost).

**Q: Can I customize the dashboard?**  
A: Yes, edit HTML/CSS in `src/web_dashboard/templates/`.

**Q: How many users can access simultaneously?**  
A: Technically unlimited, but recommended max 5 for performance.

**Q: Does dashboard work on mobile?**  
A: Yes, responsive design works on all devices.

**Q: Can I embed dashboard in iframe?**  
A: Yes, but WebSocket may require additional configuration.

**Q: Is there a dark mode?**  
A: Yes, dashboard uses dark theme by default.

**Q: Can I change the port?**  
A: Yes, edit `run_web_dashboard.py` and change port number.

---

**Last Updated**: February 12, 2026  
**Version**: 1.0.0  
**Author**: EkoVision Development Team
