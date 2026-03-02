"""
Dataset Management Module - Centralized dataset handling for UhakikiAI

This module provides a unified interface for managing:
1. Training Datasets - For model training (forgery detection, biometrics, OCR)
2. Verification Vault - Real-time document/identity verification data
3. Analytics Data - Dashboard and reporting metrics

Clear Data Flow:
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ External APIs   │────▶│ Data Ingestion   │────▶│ Training Pipeline   │
│ (HELB, KUCCPS,  │     │ Agent            │     │ (Model Training)    │
│  NEMIS, KNDR)   │     │                  │     │                     │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
                                                            │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Dashboard       │◀────│ Analytics        │◀────│ Verification        │
│ (Frontend)      │     │ Service          │     │ Service             │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DatasetCategory(Enum):
    """Categories of datasets in the system"""
    FORGERY_DETECTION = "forgery_detection"
    BIOMETRIC = "biometric"
    KENYAN_EDUCATION = "kenyan_education"
    OCR = "ocr"
    VERIFICATION_VAULT = "verification_vault"


class DatasetStatus(Enum):
    """Status of dataset availability"""
    NOT_DOWNLOADED = "not_downloaded"
    DOWNLOADING = "downloading"
    READY = "ready"
    CORRUPTED = "corrupted"


@dataclass
class DatasetInfo:
    """Information about a dataset"""
    name: str
    category: DatasetCategory
    path: Path
    description: str
    expected_files: int = 0
    actual_files: int = 0
    status: DatasetStatus = DatasetStatus.NOT_DOWNLOADED
    last_updated: Optional[datetime] = None
    source_url: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetManagerConfig:
    """Configuration for dataset manager"""
    base_data_dir: Path = Path(__file__).parent.parent.parent / "data"
    real_datasets_dir: Path = None
    training_dir: Path = None
    config_file: Path = None
    
    def __post_init__(self):
        if self.real_datasets_dir is None:
            self.real_datasets_dir = self.base_data_dir / "real_datasets"
        if self.training_dir is None:
            self.training_dir = self.base_data_dir / "training"
        if self.config_file is None:
            self.config_file = self.real_datasets_dir / "config" / "dataset_config.json"


class DatasetManager:
    """
    Centralized dataset management for UhakikiAI.
    
    Provides a clear separation between:
    - Training data (static datasets for model development)
    - Verification data (real-time processed documents)
    - Analytics data (metrics and reporting)
    """
    
    # Dataset definitions with their expected paths and descriptions
    DATASET_DEFINITIONS: Dict[str, DatasetInfo] = {}
    
    def __init__(self, config: Optional[DatasetManagerConfig] = None):
        self.config = config or DatasetManagerConfig()
        self._initialize_datasets()
    
    def _initialize_datasets(self):
        """Initialize dataset definitions with correct paths"""
        base = self.config.real_datasets_dir
        
        self.DATASET_DEFINITIONS = {
            # Forgery Detection Datasets
            "casia": DatasetInfo(
                name="CASIA Image Tampering Dataset",
                category=DatasetCategory.FORGERY_DETECTION,
                path=base / "forgery_detection" / "casia",
                description="Authentic and tampered images for forgery detection training",
                expected_files=12000,  # CASIA1 + CASIA2 combined
                source_url="https://www.kaggle.com/datasets/sophatvathana/casia-dataset"
            ),
            "columbia": DatasetInfo(
                name="Columbia Image Splicing Dataset",
                category=DatasetCategory.FORGERY_DETECTION,
                path=base / "forgery_detection" / "columbia",
                description="Columbia Uncompressed Image Splicing Detection Dataset",
                expected_files=4000,
                source_url="https://www.kaggle.com/datasets/columbia/columbia-uncompressed-image-splicing"
            ),
            
            # Biometric Datasets
            "face_recognition": DatasetInfo(
                name="Face Recognition Dataset",
                category=DatasetCategory.BIOMETRIC,
                path=base / "biometric" / "face_recognition",
                description="Face images for biometric verification",
                expected_files=10000,
                source_url="https://www.kaggle.com/datasets/vijaykumar17913/face-recognition-dataset"
            ),
            "voice_biometrics": DatasetInfo(
                name="Voice Biometric Dataset",
                category=DatasetCategory.BIOMETRIC,
                path=base / "biometric" / "voice",
                description="Voice samples for speaker verification",
                expected_files=5000,
                source_url="https://archive.ics.uci.edu/ml/datasets/speaker+identification+dataset"
            ),
            
            # Kenyan Education Datasets
            "kenyan_schools": DatasetInfo(
                name="Kenyan Schools Database",
                category=DatasetCategory.KENYAN_EDUCATION,
                path=base / "kenyan_education" / "schools",
                description="Database of Kenyan schools for verification",
                expected_files=1000,
                source_url="https://www.kuccps.net/"
            ),
            "kuccps_data": DatasetInfo(
                name="KUCCPS Placement Data",
                category=DatasetCategory.KENYAN_EDUCATION,
                path=base / "kenyan_education" / "kuccps",
                description="University/college placement data",
                expected_files=500,
                source_url="https://www.kuccps.ac.ke/"
            ),
            
            # OCR Datasets
            "icdar": DatasetInfo(
                name="ICDAR Document Dataset",
                category=DatasetCategory.OCR,
                path=base / "ocr" / "icdar",
                description="Document OCR and text recognition training data",
                expected_files=5000,
                source_url="https://rrc.cvc.uab.cat/?ch=13&com=download"
            ),
            "kenyan_documents": DatasetInfo(
                name="Kenyan Document Templates",
                category=DatasetCategory.OCR,
                path=base / "kenyan_documents",
                description="Templates for Kenyan ID, KCSE, birth certificates etc.",
                expected_files=10,
                source_url="N/A - Custom templates"
            ),
        }
    
    def scan_dataset(self, dataset_key: str) -> DatasetInfo:
        """
        Scan a specific dataset and return its current status.
        
        Args:
            dataset_key: Key identifying the dataset (e.g., 'casia', 'face_recognition')
            
        Returns:
            DatasetInfo with current file count and status
        """
        if dataset_key not in self.DATASET_DEFINITIONS:
            raise ValueError(f"Unknown dataset: {dataset_key}")
        
        dataset = self.DATASET_DEFINITIONS[dataset_key]
        
        if not dataset.path.exists():
            dataset.status = DatasetStatus.NOT_DOWNLOADED
            dataset.actual_files = 0
            return dataset
        
        # Count files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.wav', '.mp3'}
        count = 0
        for f in dataset.path.rglob('*'):
            if f.is_file() and f.suffix.lower() in image_extensions:
                count += 1
        
        dataset.actual_files = count
        dataset.last_updated = datetime.fromtimestamp(dataset.path.stat().st_mtime) if dataset.path.exists() else None
        
        if count == 0:
            dataset.status = DatasetStatus.NOT_DOWNLOADED
        elif count < dataset.expected_files * 0.5:  # Less than 50% of expected
            dataset.status = DatasetStatus.CORRUPTED
        else:
            dataset.status = DatasetStatus.READY
        
        return dataset
    
    def get_all_datasets(self) -> Dict[str, DatasetInfo]:
        """Scan all datasets and return their status"""
        results = {}
        for key in self.DATASET_DEFINITIONS:
            results[key] = self.scan_dataset(key)
        return results
    
    def get_dataset_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all datasets for the dashboard.
        
        Returns:
            Dictionary with dataset categories and totals
        """
        datasets = self.get_all_datasets()
        
        summary = {
            "total_datasets": len(datasets),
            "ready_datasets": sum(1 for d in datasets.values() if d.status == DatasetStatus.READY),
            "missing_datasets": sum(1 for d in datasets.values() if d.status == DatasetStatus.NOT_DOWNLOADED),
            "by_category": {},
            "datasets": {},
            "download_instructions": self._get_download_instructions()
        }
        
        # Group by category
        for key, dataset in datasets.items():
            cat = dataset.category.value
            if cat not in summary["by_category"]:
                summary["by_category"][cat] = {
                    "count": 0,
                    "total_files": 0,
                    "ready": 0
                }
            summary["by_category"][cat]["count"] += 1
            summary["by_category"][cat]["total_files"] += dataset.actual_files
            if dataset.status == DatasetStatus.READY:
                summary["by_category"][cat]["ready"] += 1
            
            summary["datasets"][key] = {
                "name": dataset.name,
                "status": dataset.status.value,
                "files": dataset.actual_files,
                "expected": dataset.expected_files,
                "path": str(dataset.path.relative_to(self.config.base_data_dir))
            }
        
        return summary
    
    def _get_download_instructions(self) -> str:
        """Get instructions for downloading datasets"""
        return """
To download real datasets:
1. Sign up for Kaggle at https://www.kaggle.com
2. Install Kaggle API: pip install kaggle
3. Create API token in Kaggle account settings
4. Run: python backend/scripts/download_datasets.py

For Kenyan education data:
- Contact KUCCPS, HELB, or NEMIS for API access
- Update API credentials in backend/.env.local
"""
    
    def get_training_stats(self) -> Dict[str, Any]:
        """
        Get statistics specifically for model training.
        
        Returns:
            Dictionary with training-ready dataset counts
        """
        datasets = self.get_all_datasets()
        
        training_ready = {
            "forgery_detection": 0,
            "biometric": 0,
            "ocr": 0,
            "total": 0
        }
        
        for key, dataset in datasets.items():
            if dataset.category in [DatasetCategory.FORGERY_DETECTION, DatasetCategory.BIOMETRIC, DatasetCategory.OCR]:
                if dataset.status == DatasetStatus.READY:
                    training_ready[dataset.category.value] += dataset.actual_files
                    training_ready["total"] += dataset.actual_files
        
        return training_ready
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """
        Get statistics for the verification vault.
        
        This reads from Milvus vector database, not from file datasets.
        
        Returns:
            Dictionary with vault statistics
        """
        stats = {
            "total_documents": 0,
            "total_faces": 0,
            "total_identities": 0,
            "last_verification": None
        }
        
        try:
            from app.db.milvus_client import get_milvus_client
            client = get_milvus_client()
            if client and hasattr(client, 'get_collection_count'):
                stats["total_documents"] = client.get_collection_count("documents") or 0
                stats["total_faces"] = client.get_collection_count("faces") or 0
                stats["total_identities"] = client.get_collection_count("identities") or 0
        except Exception:
            pass  # Milvus may not be available
        
        return stats


# Singleton instance for easy import
_dataset_manager: Optional[DatasetManager] = None


def get_dataset_manager() -> DatasetManager:
    """Get the global dataset manager instance"""
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = DatasetManager()
    return _dataset_manager
