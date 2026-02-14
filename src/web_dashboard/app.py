"""
Flask web application for EkoVision dashboard.

Features:
- Live video stream
- Real-time statistics
- Control panel
- Configuration editor
- Data export
"""

import os
import cv2
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, Response, jsonify, request, send_file
from flask_cors import CORS


class WebDashboard:
    """
    Web dashboard for EkoVision.
    
    Provides web interface for monitoring and controlling the detection system.
    """
    
    def __init__(self, pipeline, config, logger, performance_monitor=None):
        """
        Initialize web dashboard.
        
        Args:
            pipeline: DetectionTrackingPipeline instance
            config: System configuration
            logger: DataLogger instance
            performance_monitor: PerformanceMonitor instance (optional)
        """
        self.pipeline = pipeline
        self.config = config
        self.logger = logger
        self.performance_monitor = performance_monitor
        
        # Flask app
        self.app = Flask(__name__, 
                        template_folder=str(Path(__file__).parent / 'templates'),
                        static_folder=str(Path(__file__).parent / 'static'))
        CORS(self.app)
        
        # State
        self.running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page."""
            return render_template('index.html')
        
        @self.app.route('/video_feed')
        def video_feed():
            """Video streaming route."""
            return Response(
                self._generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
        
        @self.app.route('/api/stats')
        def get_stats():
            """Get current statistics."""
            stats = self.pipeline.get_statistics()
            
            # Add performance metrics if available
            if self.performance_monitor:
                stats['performance'] = {
                    'fps': self.performance_monitor.metrics.fps,
                    'gpu_usage': self.performance_monitor.metrics.gpu_usage,
                    'cpu_usage': self.performance_monitor.metrics.cpu_usage,
                    'vram_used': self.performance_monitor.metrics.vram_used,
                    'detection_time': self.performance_monitor.metrics.detection_time,
                    'tracking_time': self.performance_monitor.metrics.tracking_time,
                    'classification_time': self.performance_monitor.metrics.classification_time,
                    'rendering_time': self.performance_monitor.metrics.rendering_time
                }
            
            # Add logger stats
            stats['logger'] = {
                'frames_logged': len(self.logger.frame_log),
                'detections_logged': len(self.logger.detection_log),
                'classifications': self.logger.classification_count,
                'is_recording': self.logger.is_recording
            }
            
            return jsonify(stats)
        
        @self.app.route('/api/tracks')
        def get_tracks():
            """Get active tracks."""
            tracks = self.pipeline.tracker.get_active_tracks()
            
            tracks_data = []
            for track in tracks:
                track_data = {
                    'track_id': track.track_id,
                    'bbox': track.bbox,
                    'confidence': track.confidence,
                    'state': track.state.value,
                    'classification': track.classification_results
                }
                tracks_data.append(track_data)
            
            return jsonify({'tracks': tracks_data})
        
        @self.app.route('/api/control/reset', methods=['POST'])
        def reset_pipeline():
            """Reset pipeline."""
            self.pipeline.reset()
            return jsonify({'status': 'success', 'message': 'Pipeline reset'})
        
        @self.app.route('/api/control/toggle_zone', methods=['POST'])
        def toggle_zone():
            """Toggle trigger zone visibility."""
            self.pipeline.toggle_trigger_zone_visibility()
            return jsonify({
                'status': 'success',
                'show_zone': self.pipeline.show_trigger_zone
            })
        
        @self.app.route('/api/control/export_csv', methods=['POST'])
        def export_csv():
            """Export data to CSV."""
            filepath = self.logger.export_csv()
            return jsonify({
                'status': 'success',
                'filepath': str(filepath)
            })
        
        @self.app.route('/api/control/export_json', methods=['POST'])
        def export_json():
            """Export data to JSON."""
            filepath = self.logger.export_json()
            return jsonify({
                'status': 'success',
                'filepath': str(filepath)
            })
        
        @self.app.route('/api/control/recording', methods=['POST'])
        def toggle_recording():
            """Toggle video recording."""
            data = request.json
            action = data.get('action', 'toggle')
            
            if action == 'start' and not self.logger.is_recording:
                self.logger.start_recording(
                    self.pipeline.frame_width,
                    self.pipeline.frame_height,
                    fps=30
                )
                return jsonify({'status': 'success', 'recording': True})
            
            elif action == 'stop' and self.logger.is_recording:
                self.logger.stop_recording()
                return jsonify({'status': 'success', 'recording': False})
            
            elif action == 'toggle':
                if self.logger.is_recording:
                    self.logger.stop_recording()
                    return jsonify({'status': 'success', 'recording': False})
                else:
                    self.logger.start_recording(
                        self.pipeline.frame_width,
                        self.pipeline.frame_height,
                        fps=30
                    )
                    return jsonify({'status': 'success', 'recording': True})
            
            return jsonify({'status': 'error', 'message': 'Invalid action'})
        
        @self.app.route('/api/config')
        def get_config():
            """Get current configuration."""
            # Convert config to dict (simplified)
            config_dict = {
                'camera': {
                    'index': self.config.camera.index,
                    'width': self.config.camera.width,
                    'height': self.config.camera.height
                },
                'detection': {
                    'confidence_threshold': self.config.detection.confidence_threshold
                },
                'trigger_zone': {
                    'x_offset_pct': self.config.trigger_zone.x_offset_pct,
                    'y_offset_pct': self.config.trigger_zone.y_offset_pct,
                    'width_pct': self.config.trigger_zone.width_pct,
                    'height_pct': self.config.trigger_zone.height_pct
                }
            }
            return jsonify(config_dict)
        
        @self.app.route('/api/exports')
        def list_exports():
            """List available export files."""
            export_dir = Path(self.logger.output_dir)
            
            if not export_dir.exists():
                return jsonify({'files': []})
            
            files = []
            for file in export_dir.iterdir():
                if file.is_file():
                    files.append({
                        'name': file.name,
                        'size': file.stat().st_size,
                        'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
            
            # Sort by modified time (newest first)
            files.sort(key=lambda x: x['modified'], reverse=True)
            
            return jsonify({'files': files})
        
        @self.app.route('/api/download/<filename>')
        def download_file(filename):
            """Download export file."""
            filepath = Path(self.logger.output_dir) / filename
            
            if not filepath.exists():
                return jsonify({'error': 'File not found'}), 404
            
            return send_file(str(filepath), as_attachment=True)
    
    def _generate_frames(self):
        """Generate frames for video stream."""
        while True:
            with self.frame_lock:
                if self.current_frame is None:
                    time.sleep(0.1)
                    continue
                
                frame = self.current_frame.copy()
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
    
    def update_frame(self, frame):
        """
        Update current frame for streaming.
        
        Args:
            frame: New frame (BGR format)
        """
        with self.frame_lock:
            self.current_frame = frame
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """
        Run Flask server.
        
        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        print(f"\n{'='*60}")
        print("WEB DASHBOARD STARTING")
        print(f"{'='*60}")
        print(f"URL: http://{host}:{port}")
        print(f"Access from browser to view dashboard")
        print(f"{'='*60}\n")
        
        self.running = True
        self.app.run(host=host, port=port, debug=debug, threaded=True)
    
    def stop(self):
        """Stop Flask server."""
        self.running = False
