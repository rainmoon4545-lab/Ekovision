"""
Performance monitoring system for EkoVision.

Features:
- GPU/CPU/VRAM usage tracking
- Frame time breakdown
- FPS history and graphing
- Warning indicators
- Keyboard shortcuts ('m' to toggle, 'g' to save graph)
"""

import time
import psutil
import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import cv2

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class PerformanceMetrics:
    """Container for performance metrics."""
    
    def __init__(self):
        self.fps: float = 0.0
        self.gpu_usage: float = 0.0
        self.cpu_usage: float = 0.0
        self.vram_used: float = 0.0
        self.vram_total: float = 0.0
        
        # Frame time breakdown (in milliseconds)
        self.detection_time: float = 0.0
        self.tracking_time: float = 0.0
        self.classification_time: float = 0.0
        self.rendering_time: float = 0.0
        self.total_time: float = 0.0
        
        # Warnings
        self.low_fps_warning: bool = False
        self.high_gpu_warning: bool = False
        self.high_vram_warning: bool = False


class PerformanceMonitor:
    """
    Monitor system performance metrics.
    
    Features:
    - Real-time GPU/CPU/VRAM tracking
    - Frame time breakdown
    - FPS history (last 60 seconds)
    - Warning indicators
    - Performance graph generation
    """
    
    def __init__(self, history_size: int = 60):
        """
        Initialize performance monitor.
        
        Args:
            history_size: Number of seconds to keep in FPS history
        """
        self.history_size = history_size
        self.fps_history: deque = deque(maxlen=history_size)
        self.timestamp_history: deque = deque(maxlen=history_size)
        
        # Current metrics
        self.metrics = PerformanceMetrics()
        
        # Timing
        self.last_update_time = time.time()
        self.frame_count = 0
        
        # Frame time tracking
        self.frame_times: Dict[str, float] = {
            'detection': 0.0,
            'tracking': 0.0,
            'classification': 0.0,
            'rendering': 0.0
        }
        
        # Warning thresholds
        self.fps_threshold = 10.0
        self.gpu_threshold = 95.0
        self.vram_threshold = 90.0
        
        # Display state
        self.show_overlay = False
        
        # Check GPU availability
        self.gpu_available = TORCH_AVAILABLE and torch.cuda.is_available()
        
    def update_frame_time(self, stage: str, duration_ms: float):
        """
        Update frame time for a specific stage.
        
        Args:
            stage: Stage name ('detection', 'tracking', 'classification', 'rendering')
            duration_ms: Duration in milliseconds
        """
        if stage in self.frame_times:
            self.frame_times[stage] = duration_ms
    
    def update_metrics(self):
        """Update all performance metrics."""
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        
        # Update FPS (every second)
        if elapsed >= 1.0:
            self.metrics.fps = self.frame_count / elapsed
            self.fps_history.append(self.metrics.fps)
            self.timestamp_history.append(current_time)
            
            self.frame_count = 0
            self.last_update_time = current_time
            
            # Update system metrics
            self._update_system_metrics()
            
            # Update frame time breakdown
            self.metrics.detection_time = self.frame_times['detection']
            self.metrics.tracking_time = self.frame_times['tracking']
            self.metrics.classification_time = self.frame_times['classification']
            self.metrics.rendering_time = self.frame_times['rendering']
            self.metrics.total_time = sum(self.frame_times.values())
            
            # Check warnings
            self._check_warnings()
        
        self.frame_count += 1
    
    def _update_system_metrics(self):
        """Update CPU, GPU, and VRAM metrics."""
        # CPU usage
        self.metrics.cpu_usage = psutil.cpu_percent(interval=None)
        
        # GPU metrics
        if self.gpu_available:
            try:
                # GPU usage (approximate via memory usage)
                self.metrics.vram_used = torch.cuda.memory_allocated() / (1024 ** 3)  # GB
                self.metrics.vram_total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)  # GB
                
                # GPU utilization (approximate)
                vram_percent = (self.metrics.vram_used / self.metrics.vram_total) * 100
                self.metrics.gpu_usage = vram_percent
                
            except Exception as e:
                self.metrics.gpu_usage = 0.0
                self.metrics.vram_used = 0.0
                self.metrics.vram_total = 0.0
        else:
            self.metrics.gpu_usage = 0.0
            self.metrics.vram_used = 0.0
            self.metrics.vram_total = 0.0
    
    def _check_warnings(self):
        """Check for warning conditions."""
        self.metrics.low_fps_warning = self.metrics.fps < self.fps_threshold
        self.metrics.high_gpu_warning = self.metrics.gpu_usage > self.gpu_threshold
        self.metrics.high_vram_warning = (
            self.metrics.vram_total > 0 and
            (self.metrics.vram_used / self.metrics.vram_total * 100) > self.vram_threshold
        )
    
    def toggle_overlay(self):
        """Toggle performance overlay display."""
        self.show_overlay = not self.show_overlay
    
    def get_average_fps(self) -> float:
        """Get average FPS over history."""
        if len(self.fps_history) == 0:
            return 0.0
        return sum(self.fps_history) / len(self.fps_history)
    
    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw performance overlay on frame.
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with overlay
        """
        if not self.show_overlay:
            return frame
        
        # Create overlay
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Overlay position (top-right corner)
        x_offset = w - 350
        y_offset = 10
        box_width = 340
        box_height = 280
        
        # Draw semi-transparent background
        cv2.rectangle(
            overlay,
            (x_offset, y_offset),
            (x_offset + box_width, y_offset + box_height),
            (0, 0, 0),
            -1
        )
        
        # Blend with original frame
        alpha = 0.7
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        # Text properties
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1
        line_height = 25
        
        # Title
        y = y_offset + 25
        cv2.putText(
            frame,
            "Performance Metrics",
            (x_offset + 10, y),
            font,
            0.6,
            (255, 255, 255),
            2
        )
        
        y += line_height + 5
        
        # FPS
        fps_color = (0, 0, 255) if self.metrics.low_fps_warning else (0, 255, 0)
        avg_fps = self.get_average_fps()
        cv2.putText(
            frame,
            f"FPS: {self.metrics.fps:.1f} (avg: {avg_fps:.1f})",
            (x_offset + 10, y),
            font,
            font_scale,
            fps_color,
            thickness
        )
        
        y += line_height
        
        # GPU/CPU
        gpu_color = (0, 165, 255) if self.metrics.high_gpu_warning else (255, 255, 255)
        cv2.putText(
            frame,
            f"GPU: {self.metrics.gpu_usage:.0f}% | CPU: {self.metrics.cpu_usage:.0f}%",
            (x_offset + 10, y),
            font,
            font_scale,
            gpu_color,
            thickness
        )
        
        y += line_height
        
        # VRAM
        if self.metrics.vram_total > 0:
            vram_color = (0, 165, 255) if self.metrics.high_vram_warning else (255, 255, 255)
            cv2.putText(
                frame,
                f"VRAM: {self.metrics.vram_used:.1f}/{self.metrics.vram_total:.1f} GB",
                (x_offset + 10, y),
                font,
                font_scale,
                vram_color,
                thickness
            )
            y += line_height
        
        y += 10
        
        # Frame time breakdown
        cv2.putText(
            frame,
            "Frame Time:",
            (x_offset + 10, y),
            font,
            font_scale,
            (255, 255, 255),
            thickness
        )
        
        y += line_height
        
        cv2.putText(
            frame,
            f"  Detection: {self.metrics.detection_time:.1f}ms",
            (x_offset + 10, y),
            font,
            font_scale,
            (200, 200, 200),
            thickness
        )
        
        y += line_height
        
        cv2.putText(
            frame,
            f"  Tracking: {self.metrics.tracking_time:.1f}ms",
            (x_offset + 10, y),
            font,
            font_scale,
            (200, 200, 200),
            thickness
        )
        
        y += line_height
        
        cv2.putText(
            frame,
            f"  Classification: {self.metrics.classification_time:.1f}ms",
            (x_offset + 10, y),
            font,
            font_scale,
            (200, 200, 200),
            thickness
        )
        
        y += line_height
        
        cv2.putText(
            frame,
            f"  Rendering: {self.metrics.rendering_time:.1f}ms",
            (x_offset + 10, y),
            font,
            font_scale,
            (200, 200, 200),
            thickness
        )
        
        y += line_height
        
        cv2.putText(
            frame,
            f"  Total: {self.metrics.total_time:.1f}ms",
            (x_offset + 10, y),
            font,
            0.55,
            (255, 255, 255),
            thickness + 1
        )
        
        y += line_height + 10
        
        # Controls hint
        cv2.putText(
            frame,
            "Press 'm' to hide | 'g' to save graph",
            (x_offset + 10, y),
            font,
            0.4,
            (150, 150, 150),
            thickness
        )
        
        return frame
    
    def save_performance_graph(self, output_path: Optional[str] = None) -> str:
        """
        Save FPS performance graph as PNG.
        
        Args:
            output_path: Output file path (optional)
            
        Returns:
            Path to saved graph
        """
        if len(self.fps_history) == 0:
            raise ValueError("No FPS history to plot")
        
        try:
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("matplotlib is required for graph generation. Install with: pip install matplotlib")
        
        # Generate filename if not provided
        if output_path is None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            output_path = f"performance_graph_{timestamp}.png"
        
        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Convert timestamps to relative seconds
        if len(self.timestamp_history) > 0:
            start_time = self.timestamp_history[0]
            time_seconds = [(t - start_time) for t in self.timestamp_history]
        else:
            time_seconds = list(range(len(self.fps_history)))
        
        # Plot FPS
        ax1.plot(time_seconds, list(self.fps_history), 'b-', linewidth=2, label='FPS')
        ax1.axhline(y=self.fps_threshold, color='r', linestyle='--', label=f'Warning Threshold ({self.fps_threshold})')
        ax1.set_xlabel('Time (seconds)')
        ax1.set_ylabel('FPS')
        ax1.set_title('FPS Over Time')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        
        # Plot frame time breakdown (if available)
        if self.metrics.total_time > 0:
            stages = ['Detection', 'Tracking', 'Classification', 'Rendering']
            times = [
                self.metrics.detection_time,
                self.metrics.tracking_time,
                self.metrics.classification_time,
                self.metrics.rendering_time
            ]
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A']
            
            ax2.bar(stages, times, color=colors)
            ax2.set_ylabel('Time (ms)')
            ax2.set_title('Frame Time Breakdown (Current)')
            ax2.grid(True, alpha=0.3, axis='y')
        
        # Add summary text
        avg_fps = self.get_average_fps()
        summary_text = f"Average FPS: {avg_fps:.2f}\n"
        summary_text += f"Current FPS: {self.metrics.fps:.2f}\n"
        summary_text += f"GPU Usage: {self.metrics.gpu_usage:.1f}%\n"
        summary_text += f"CPU Usage: {self.metrics.cpu_usage:.1f}%"
        
        fig.text(0.02, 0.02, summary_text, fontsize=10, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def get_summary(self) -> Dict:
        """
        Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'fps': {
                'current': self.metrics.fps,
                'average': self.get_average_fps(),
                'history_size': len(self.fps_history)
            },
            'system': {
                'gpu_usage': self.metrics.gpu_usage,
                'cpu_usage': self.metrics.cpu_usage,
                'vram_used': self.metrics.vram_used,
                'vram_total': self.metrics.vram_total
            },
            'frame_time': {
                'detection_ms': self.metrics.detection_time,
                'tracking_ms': self.metrics.tracking_time,
                'classification_ms': self.metrics.classification_time,
                'rendering_ms': self.metrics.rendering_time,
                'total_ms': self.metrics.total_time
            },
            'warnings': {
                'low_fps': self.metrics.low_fps_warning,
                'high_gpu': self.metrics.high_gpu_warning,
                'high_vram': self.metrics.high_vram_warning
            }
        }
    
    def print_summary(self):
        """Print performance summary to console."""
        summary = self.get_summary()
        
        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"\nFPS:")
        print(f"  Current: {summary['fps']['current']:.2f}")
        print(f"  Average: {summary['fps']['average']:.2f}")
        print(f"  History: {summary['fps']['history_size']} seconds")
        
        print(f"\nSystem:")
        print(f"  GPU: {summary['system']['gpu_usage']:.1f}%")
        print(f"  CPU: {summary['system']['cpu_usage']:.1f}%")
        if summary['system']['vram_total'] > 0:
            print(f"  VRAM: {summary['system']['vram_used']:.1f}/{summary['system']['vram_total']:.1f} GB")
        
        print(f"\nFrame Time:")
        print(f"  Detection: {summary['frame_time']['detection_ms']:.1f}ms")
        print(f"  Tracking: {summary['frame_time']['tracking_ms']:.1f}ms")
        print(f"  Classification: {summary['frame_time']['classification_ms']:.1f}ms")
        print(f"  Rendering: {summary['frame_time']['rendering_ms']:.1f}ms")
        print(f"  Total: {summary['frame_time']['total_ms']:.1f}ms")
        
        if any(summary['warnings'].values()):
            print(f"\nWarnings:")
            if summary['warnings']['low_fps']:
                print(f"  ⚠ Low FPS (< {self.fps_threshold})")
            if summary['warnings']['high_gpu']:
                print(f"  ⚠ High GPU usage (> {self.gpu_threshold}%)")
            if summary['warnings']['high_vram']:
                print(f"  ⚠ High VRAM usage (> {self.vram_threshold}%)")
        
        print("=" * 60 + "\n")
