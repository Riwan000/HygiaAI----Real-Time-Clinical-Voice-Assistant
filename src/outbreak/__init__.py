"""
Outbreak Detection Module

Handles:
- Advanced clustering-based outbreak detection
- Anomaly detection in patient data
- Alert generation and threshold configuration
- Spatial and temporal clustering
"""

from .outbreak_detector import (
    OutbreakDetector,
    OutbreakAlert,
    OutbreakCluster,
    DetectionMethod,
    AlertLevel,
    OutbreakDetectionOptions,
    OutbreakDetectionResult
)

__all__ = [
    "OutbreakDetector",
    "OutbreakAlert",
    "OutbreakCluster",
    "DetectionMethod",
    "AlertLevel",
    "OutbreakDetectionOptions",
    "OutbreakDetectionResult"
]

