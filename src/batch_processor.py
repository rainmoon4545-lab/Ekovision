"""
Batch video processing for EkoVision.

Process pre-recorded videos offline with progress tracking and summary reports.
"""

import os
import cv2
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("⚠ tqdm not installed. Progress bar disabled. Install with: pip install tqdm")


@dataclass
class VideoProcessingResult:
    """Result of processing a single video."""
    video_path: str
    output_path: str
    success: bool
    frames_processed: int
    classifications: int
    duration_seconds: float
    avg_fps: float
    error_message: Optional[str] = None


@dataclass
class BatchProcessingReport:
    """Summary report for batch processing."""
    start_time: str
    end_time: str
    total_duration_seconds: float
    videos_processed: int
    videos_succeeded: int
    videos_failed: int
    total_frames: int
    total_classifications: int
    avg_fps: float
    results: List[Dict]


class BatchProcessor:
    """
    Process multiple videos offline.
    
    Features:
    - Progress tracking with tqdm
    - Automatic output directory creation
    - Summary report generation
    - Error handling and recovery
    """
    
    def __init__(
        self,
        pipeline,
        output_dir: str = "batch_output",
        save_video: bool = True,
        save_json: bool = True,
        save_csv: bool = True
    ):
        """
        Initialize batch processor.
        
        Args:
            pipeline: DetectionTrackingPipeline instance
            output_dir: Directory for output files
            save_video: Save annotated video
            save_json: Save JSON classification data
            save_csv: Save CSV detection data
        """
        self.pipeline = pipeline
        self.output_dir = Path(output_dir)
        self.save_video = save_video
        self.save_json = save_json
        self.save_csv = save_csv
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Results tracking
        self.results: List[VideoProcessingResult] = []
        
    def process_video(
        self,
        video_path: str,
        output_name: Optional[str] = None,
        show_progress: bool = True
    ) -> VideoProcessingResult:
        """
        Process a single video file.
        
        Args:
            video_path: Path to input video
            output_name: Custom output name (optional)
            show_progress: Show progress bar
            
        Returns:
            VideoProcessingResult with processing statistics
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            return VideoProcessingResult(
                video_path=str(video_path),
                output_path="",
                success=False,
                frames_processed=0,
                classifications=0,
                duration_seconds=0.0,
                avg_fps=0.0,
                error_message=f"Video file not found: {video_path}"
            )
        
        # Generate output name
        if output_name is None:
            output_name = f"{video_path.stem}_processed"
        
        output_path = self.output_dir / output_name
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return VideoProcessingResult(
                video_path=str(video_path),
                output_path="",
                success=False,
                frames_processed=0,
                classifications=0,
                duration_seconds=0.0,
                avg_fps=0.0,
                error_message=f"Failed to open video: {video_path}"
            )
        
        # Get video properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Initialize video writer if needed
        video_writer = None
        if self.save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_output_path = str(output_path) + ".mp4"
            video_writer = cv2.VideoWriter(
                video_output_path,
                fourcc,
                fps,
                (frame_width, frame_height)
            )
        
        # Initialize data logger if needed
        from src.data_logger import DataLogger
        logger = None
        if self.save_json or self.save_csv:
            logger = DataLogger(output_dir=str(self.output_dir))
            logger.session_id = output_name
        
        # Reset pipeline
        self.pipeline.reset()
        
        # Processing loop
        start_time = time.time()
        frames_processed = 0
        
        # Progress bar
        pbar = None
        if show_progress and TQDM_AVAILABLE:
            pbar = tqdm(
                total=total_frames,
                desc=f"Processing {video_path.name}",
                unit="frame",
                ncols=100
            )
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Process frame
                annotated_frame, stats = self.pipeline.process_frame(frame)
                frames_processed += 1
                
                # Log data
                if logger:
                    logger.log_frame(fps=stats.get('fps', 0))
                    
                    # Log detections
                    tracks = self.pipeline.tracker.get_active_tracks()
                    for track in tracks:
                        logger.log_detection(
                            timestamp=datetime.now().isoformat(),
                            track_id=track.track_id,
                            bbox=track.bbox,
                            confidence=track.confidence,
                            state=track.state.value,
                            classification=track.classification_results
                        )
                    
                    # Log classifications
                    if stats.get('classifications', 0) > 0:
                        logger.log_classification()
                
                # Write frame
                if video_writer:
                    video_writer.write(annotated_frame)
                
                # Update progress
                if pbar:
                    pbar.update(1)
            
            # Close progress bar
            if pbar:
                pbar.close()
            
            # Calculate statistics
            duration = time.time() - start_time
            avg_fps = frames_processed / duration if duration > 0 else 0
            
            # Get final statistics
            final_stats = self.pipeline.get_statistics()
            classifications = final_stats['classification_count']
            
            # Export data
            if logger:
                if self.save_csv:
                    logger.export_csv()
                if self.save_json:
                    logger.export_json()
                logger.save_summary()
            
            # Cleanup
            cap.release()
            if video_writer:
                video_writer.release()
            
            # Create result
            result = VideoProcessingResult(
                video_path=str(video_path),
                output_path=str(output_path),
                success=True,
                frames_processed=frames_processed,
                classifications=classifications,
                duration_seconds=duration,
                avg_fps=avg_fps
            )
            
            self.results.append(result)
            return result
            
        except Exception as e:
            # Cleanup on error
            if pbar:
                pbar.close()
            cap.release()
            if video_writer:
                video_writer.release()
            
            result = VideoProcessingResult(
                video_path=str(video_path),
                output_path=str(output_path),
                success=False,
                frames_processed=frames_processed,
                classifications=0,
                duration_seconds=time.time() - start_time,
                avg_fps=0.0,
                error_message=str(e)
            )
            
            self.results.append(result)
            return result
    
    def process_directory(
        self,
        input_dir: str,
        pattern: str = "*.mp4",
        show_progress: bool = True
    ) -> List[VideoProcessingResult]:
        """
        Process all videos in a directory.
        
        Args:
            input_dir: Directory containing videos
            pattern: File pattern (e.g., "*.mp4", "*.avi")
            show_progress: Show progress bars
            
        Returns:
            List of VideoProcessingResult
        """
        input_dir = Path(input_dir)
        
        if not input_dir.exists():
            print(f"✗ Directory not found: {input_dir}")
            return []
        
        # Find all videos
        video_files = list(input_dir.glob(pattern))
        
        if not video_files:
            print(f"✗ No videos found matching pattern: {pattern}")
            return []
        
        print(f"\nFound {len(video_files)} video(s) to process")
        print(f"Output directory: {self.output_dir}")
        print()
        
        # Process each video
        results = []
        for video_file in video_files:
            result = self.process_video(
                str(video_file),
                show_progress=show_progress
            )
            results.append(result)
            
            # Print result
            if result.success:
                print(f"✓ {video_file.name}: {result.frames_processed} frames, "
                      f"{result.classifications} classifications, "
                      f"{result.avg_fps:.1f} FPS")
            else:
                print(f"✗ {video_file.name}: {result.error_message}")
        
        return results
    
    def generate_report(self) -> BatchProcessingReport:
        """
        Generate batch processing report.
        
        Returns:
            BatchProcessingReport with summary statistics
        """
        if not self.results:
            return BatchProcessingReport(
                start_time="",
                end_time="",
                total_duration_seconds=0.0,
                videos_processed=0,
                videos_succeeded=0,
                videos_failed=0,
                total_frames=0,
                total_classifications=0,
                avg_fps=0.0,
                results=[]
            )
        
        # Calculate statistics
        videos_succeeded = sum(1 for r in self.results if r.success)
        videos_failed = sum(1 for r in self.results if not r.success)
        total_frames = sum(r.frames_processed for r in self.results)
        total_classifications = sum(r.classifications for r in self.results)
        total_duration = sum(r.duration_seconds for r in self.results)
        avg_fps = total_frames / total_duration if total_duration > 0 else 0
        
        # Create report
        report = BatchProcessingReport(
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            total_duration_seconds=total_duration,
            videos_processed=len(self.results),
            videos_succeeded=videos_succeeded,
            videos_failed=videos_failed,
            total_frames=total_frames,
            total_classifications=total_classifications,
            avg_fps=avg_fps,
            results=[asdict(r) for r in self.results]
        )
        
        return report
    
    def save_report(self, filename: str = "batch_report.json"):
        """
        Save batch processing report to JSON.
        
        Args:
            filename: Output filename
        """
        report = self.generate_report()
        report_path = self.output_dir / filename
        
        with open(report_path, 'w') as f:
            json.dump(asdict(report), f, indent=2)
        
        print(f"\n✓ Report saved: {report_path}")
        return report_path
    
    def print_summary(self):
        """Print batch processing summary to console."""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("BATCH PROCESSING SUMMARY")
        print("="*60)
        print(f"Videos processed: {report.videos_processed}")
        print(f"  Succeeded: {report.videos_succeeded}")
        print(f"  Failed: {report.videos_failed}")
        print(f"\nTotal frames: {report.total_frames}")
        print(f"Total classifications: {report.total_classifications}")
        print(f"Average FPS: {report.avg_fps:.1f}")
        print(f"Total duration: {report.total_duration_seconds:.1f}s")
        print("="*60)
