"""
Data Logger for EkoVision Detection-Tracking-Trigger System

Handles CSV export, JSON export, video recording, and session summaries.
"""
import os
import csv
import json
import cv2
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict


@dataclass
class DetectionRecord:
    """Single detection record for logging."""
    timestamp: str
    track_id: int
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    state: str
    product: str = "UNKNOWN"
    grade: str = "UNKNOWN"
    cap: str = "UNKNOWN"
    label: str = "UNKNOWN"
    brand: str = "UNKNOWN"
    type: str = "UNKNOWN"
    subtype: str = "UNKNOWN"
    volume: str = "UNKNOWN"


@dataclass
class BottleHistory:
    """Complete history for a single bottle."""
    track_id: int
    first_seen: str
    last_seen: str
    state: str
    frames_tracked: int
    classification_attempts: int
    classification: Optional[Dict[str, str]] = None


class DataLogger:
    """
    Data logger for detection, classification, and performance data.
    
    Features:
    - CSV export with all detection data
    - JSON export with classification history
    - Video recording with annotations
    - Session summary generation
    """
    
    def __init__(self, output_dir: str = "exports"):
        """
        Initialize data logger.
        
        Args:
            output_dir: Directory for exported files
        """
        self.output_dir = output_dir
        self.detection_records: List[DetectionRecord] = []
        self.bottle_histories: Dict[int, BottleHistory] = {}
        self.session_start = datetime.now()
        
        # Video recording
        self.is_recording = False
        self.video_writer: Optional[cv2.VideoWriter] = None
        self.recording_path: Optional[str] = None
        
        # Statistics
        self.total_frames = 0
        self.total_classifications = 0
        self.fps_history: List[float] = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
    
    def log_detection(
        self,
        timestamp: str,
        track_id: int,
        bbox: tuple,
        confidence: float,
        state: str,
        classification: Optional[Dict[str, str]] = None
    ):
        """
        Log a detection event.
        
        Args:
            timestamp: ISO format timestamp
            track_id: Bottle ID
            bbox: Bounding box (x1, y1, x2, y2)
            confidence: Detection confidence
            state: Tracking state (NEW, TRACKED, CLASSIFIED, FAILED)
            classification: Classification results dict (8 attributes)
        """
        x1, y1, x2, y2 = map(int, bbox)
        
        # Create detection record
        record = DetectionRecord(
            timestamp=timestamp,
            track_id=track_id,
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            confidence=confidence,
            state=state
        )
        
        # Add classification if available
        if classification:
            record.product = classification.get('product', 'UNKNOWN')
            record.grade = classification.get('grade', 'UNKNOWN')
            record.cap = classification.get('cap', 'UNKNOWN')
            record.label = classification.get('label', 'UNKNOWN')
            record.brand = classification.get('brand', 'UNKNOWN')
            record.type = classification.get('type', 'UNKNOWN')
            record.subtype = classification.get('subtype', 'UNKNOWN')
            record.volume = classification.get('volume', 'UNKNOWN')
        
        self.detection_records.append(record)
        
        # Update bottle history
        if track_id not in self.bottle_histories:
            self.bottle_histories[track_id] = BottleHistory(
                track_id=track_id,
                first_seen=timestamp,
                last_seen=timestamp,
                state=state,
                frames_tracked=1,
                classification_attempts=0,
                classification=classification if classification else None
            )
        else:
            history = self.bottle_histories[track_id]
            history.last_seen = timestamp
            history.state = state
            history.frames_tracked += 1
            if classification:
                history.classification = classification
                history.classification_attempts += 1
    
    def log_frame(self, fps: float):
        """
        Log frame processing.
        
        Args:
            fps: Current FPS
        """
        self.total_frames += 1
        self.fps_history.append(fps)
    
    def log_classification(self):
        """Log a classification event."""
        self.total_classifications += 1
    
    def start_recording(
        self,
        frame_width: int,
        frame_height: int,
        fps: int = 30
    ) -> bool:
        """
        Start video recording.
        
        Args:
            frame_width: Video frame width
            frame_height: Video frame height
            fps: Recording frame rate
            
        Returns:
            True if recording started, False otherwise
        """
        if self.is_recording:
            print("⚠ Recording already in progress")
            return False
        
        # Generate filename
        filename = self._generate_filename("mp4")
        self.recording_path = os.path.join(self.output_dir, filename)
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.recording_path,
            fourcc,
            fps,
            (frame_width, frame_height)
        )
        
        if not self.video_writer.isOpened():
            print("✗ Failed to start video recording")
            self.video_writer = None
            self.recording_path = None
            return False
        
        self.is_recording = True
        print(f"✓ Recording started: {self.recording_path}")
        return True
    
    def stop_recording(self) -> Optional[str]:
        """
        Stop video recording.
        
        Returns:
            Path to saved video file, or None if not recording
        """
        if not self.is_recording:
            print("⚠ No recording in progress")
            return None
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.is_recording = False
        path = self.recording_path
        self.recording_path = None
        
        print(f"✓ Recording stopped: {path}")
        return path
    
    def write_frame(self, frame):
        """
        Write frame to video file if recording is active.
        
        Args:
            frame: Frame to write (BGR format)
        """
        if self.is_recording and self.video_writer:
            self.video_writer.write(frame)
    
    def export_csv(self) -> str:
        """
        Export detection data to CSV file.
        
        Returns:
            Path to generated CSV file
        """
        filename = self._generate_filename("csv")
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header
            writer.writerow([
                'timestamp', 'track_id', 'x1', 'y1', 'x2', 'y2',
                'confidence', 'state',
                'product', 'grade', 'cap', 'label',
                'brand', 'type', 'subtype', 'volume'
            ])
            
            # Data
            for record in self.detection_records:
                writer.writerow([
                    record.timestamp,
                    record.track_id,
                    record.x1,
                    record.y1,
                    record.x2,
                    record.y2,
                    f"{record.confidence:.3f}",
                    record.state,
                    record.product,
                    record.grade,
                    record.cap,
                    record.label,
                    record.brand,
                    record.type,
                    record.subtype,
                    record.volume
                ])
        
        print(f"✓ CSV exported: {filepath}")
        print(f"  Total records: {len(self.detection_records)}")
        return filepath
    
    def export_json(self) -> str:
        """
        Export classification history to JSON file.
        
        Returns:
            Path to generated JSON file
        """
        filename = self._generate_filename("json")
        filepath = os.path.join(self.output_dir, filename)
        
        # Build JSON structure
        data = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "total_bottles": len(self.bottle_histories),
            "total_frames": self.total_frames,
            "total_classifications": self.total_classifications,
            "bottles": []
        }
        
        # Add bottle histories
        for history in self.bottle_histories.values():
            bottle_data = {
                "track_id": history.track_id,
                "first_seen": history.first_seen,
                "last_seen": history.last_seen,
                "state": history.state,
                "frames_tracked": history.frames_tracked,
                "classification_attempts": history.classification_attempts,
                "classification": history.classification
            }
            data["bottles"].append(bottle_data)
        
        # Write JSON
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ JSON exported: {filepath}")
        print(f"  Total bottles: {len(self.bottle_histories)}")
        return filepath
    
    def generate_session_summary(self) -> Dict[str, Any]:
        """
        Generate session summary report.
        
        Returns:
            Dict with session statistics
        """
        session_duration = (datetime.now() - self.session_start).total_seconds()
        avg_fps = sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0
        
        # Count states
        state_counts = {
            'NEW': 0,
            'TRACKED': 0,
            'CLASSIFIED': 0,
            'FAILED': 0
        }
        
        for history in self.bottle_histories.values():
            state_counts[history.state] = state_counts.get(history.state, 0) + 1
        
        # Calculate reduction percentage
        if self.total_frames > 0:
            reduction_pct = (1 - self.total_classifications / self.total_frames) * 100
        else:
            reduction_pct = 0
        
        summary = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "duration_seconds": session_duration,
            "total_frames": self.total_frames,
            "total_bottles": len(self.bottle_histories),
            "total_classifications": self.total_classifications,
            "computational_reduction_pct": reduction_pct,
            "average_fps": avg_fps,
            "state_distribution": state_counts,
            "detection_records": len(self.detection_records)
        }
        
        return summary
    
    def print_summary(self):
        """Print session summary to console."""
        summary = self.generate_session_summary()
        
        print("\n" + "="*60)
        print("SESSION SUMMARY")
        print("="*60)
        print(f"Duration: {summary['duration_seconds']:.1f} seconds")
        print(f"Total frames: {summary['total_frames']}")
        print(f"Total bottles: {summary['total_bottles']}")
        print(f"Total classifications: {summary['total_classifications']}")
        print(f"Computational reduction: {summary['computational_reduction_pct']:.1f}%")
        print(f"Average FPS: {summary['average_fps']:.1f}")
        print(f"\nState Distribution:")
        for state, count in summary['state_distribution'].items():
            print(f"  {state}: {count}")
        print("="*60)
    
    def save_summary(self) -> str:
        """
        Save session summary to JSON file.
        
        Returns:
            Path to summary file
        """
        summary = self.generate_session_summary()
        
        filename = self._generate_filename("summary.json")
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✓ Summary saved: {filepath}")
        return filepath
    
    def _generate_filename(self, extension: str) -> str:
        """
        Generate timestamped filename.
        
        Args:
            extension: File extension (e.g., "csv", "json", "mp4")
            
        Returns:
            Filename in format: ekovision_YYYY-MM-DD_HH-MM-SS.ext
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        return f"ekovision_{timestamp}.{extension}"
    
    def reset(self):
        """Reset logger state (clear all data)."""
        self.detection_records.clear()
        self.bottle_histories.clear()
        self.session_start = datetime.now()
        self.total_frames = 0
        self.total_classifications = 0
        self.fps_history.clear()
        
        # Stop recording if active
        if self.is_recording:
            self.stop_recording()
        
        print("✓ Data logger reset")


if __name__ == "__main__":
    # Test data logger
    print("Testing DataLogger...")
    print()
    
    logger = DataLogger(output_dir="test_exports")
    
    # Log some detections
    for i in range(5):
        logger.log_detection(
            timestamp=datetime.now().isoformat(),
            track_id=100 + i,
            bbox=(100, 100, 200, 200),
            confidence=0.95,
            state="CLASSIFIED",
            classification={
                'product': 'Aqua',
                'grade': 'Premium',
                'cap': 'Blue',
                'label': 'Clear',
                'brand': 'Danone',
                'type': 'Water',
                'subtype': 'Still',
                'volume': '600ml'
            }
        )
        logger.log_frame(fps=17.5)
        logger.log_classification()
    
    # Export data
    logger.export_csv()
    logger.export_json()
    logger.save_summary()
    logger.print_summary()
    
    print()
    print("✓ DataLogger test complete")
