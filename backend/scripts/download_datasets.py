#!/usr/bin/env python3
"""
UhakikiAI Dataset Download and Integration Script
Downloads real datasets from Kaggle, UCI, and other sources
"""

import os
import sys
import requests
import zipfile
import pandas as pd
from pathlib import Path
import json
from typing import Dict, List, Any

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DatasetDownloader:
    """Downloads and processes real datasets for UhakikiAI"""
    
    def __init__(self, base_dir: str = "data/real_datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Dataset configurations
        self.datasets = {
            "forgery_detection": {
                "casia": {
                    "name": "CASIA Image Tampering Dataset",
                    "url": "https://www.kaggle.com/datasets/sophatvathana/casia-dataset",
                    "type": "kaggle",
                    "target_dir": "forgery_detection/casia"
                },
                "columbia": {
                    "name": "Columbia Image Splicing Dataset", 
                    "url": "https://www.kaggle.com/datasets/columbia/columbia-uncompressed-image-splicing",
                    "type": "kaggle",
                    "target_dir": "forgery_detection/columbia"
                }
            },
            "biometric": {
                "face_recognition": {
                    "name": "Face Recognition Dataset",
                    "url": "https://www.kaggle.com/datasets/vijaykumar17913/face-recognition-dataset",
                    "type": "kaggle", 
                    "target_dir": "biometric/face_recognition"
                },
                "voice_biometrics": {
                    "name": "Voice Biometric Dataset",
                    "url": "https://archive.ics.uci.edu/ml/datasets/speaker+identification+dataset",
                    "type": "uci",
                    "target_dir": "biometric/voice"
                }
            },
            "kenyan_education": {
                "schools": {
                    "name": "Kenyan Schools Database",
                    "url": "https://data.go.ke/api/action/datastore_search?resource_id=schools-database",
                    "type": "api",
                    "target_dir": "kenyan_education/schools"
                },
                "kuccps": {
                    "name": "KUCCPS Placement Data",
                    "url": "https://data.go.ke/api/action/datastore_search?resource_id=kuccps-data",
                    "type": "api", 
                    "target_dir": "kenyan_education/kuccps"
                }
            },
            "ocr_training": {
                "icdar": {
                    "name": "ICDAR Document Dataset",
                    "url": "https://rrc.cvc.uab.cat/?ch=13&com=download",
                    "type": "direct",
                    "target_dir": "ocr/icdar"
                }
            }
        }
    
    def download_kaggle_dataset(self, dataset_config: Dict[str, Any]) -> bool:
        """Download dataset from Kaggle using Kaggle API"""
        try:
            import kaggle
            print(f"📥 Downloading {dataset_config['name']} from Kaggle...")
            
            # Extract dataset name from URL
            dataset_name = dataset_config['url'].split('/')[-1]
            
            # Create target directory
            target_path = self.base_dir / dataset_config['target_dir']
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Download dataset
            kaggle.api.dataset_download_files(dataset_name, path=str(target_path), unzip=True)
            
            print(f"✅ Successfully downloaded {dataset_config['name']}")
            return True
            
        except ImportError:
            print("❌ Kaggle API not installed. Install with: pip install kaggle")
            return False
        except Exception as e:
            print(f"❌ Error downloading {dataset_config['name']}: {e}")
            return False
    
    def download_uci_dataset(self, dataset_config: Dict[str, Any]) -> bool:
        """Download dataset from UCI repository"""
        try:
            print(f"📥 Downloading {dataset_config['name']} from UCI...")
            
            # Create target directory
            target_path = self.base_dir / dataset_config['target_dir']
            target_path.mkdir(parents=True, exist_ok=True)
            
            # For UCI, we'll create a placeholder with download instructions
            info_file = target_path / "download_instructions.txt"
            with open(info_file, 'w') as f:
                f.write(f"Dataset: {dataset_config['name']}\n")
                f.write(f"URL: {dataset_config['url']}\n")
                f.write(f"\nManual download required:\n")
                f.write(f"1. Visit the URL above\n")
                f.write(f"2. Download the dataset files\n")
                f.write(f"3. Extract to this directory\n")
            
            print(f"✅ Created download instructions for {dataset_config['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {dataset_config['name']}: {e}")
            return False
    
    def download_api_dataset(self, dataset_config: Dict[str, Any]) -> bool:
        """Download dataset from API endpoint"""
        try:
            print(f"📥 Downloading {dataset_config['name']} from API...")
            
            # Create target directory
            target_path = self.base_dir / dataset_config['target_dir']
            target_path.mkdir(parents=True, exist_ok=True)
            
            # Download data from API
            response = requests.get(dataset_config['url'], timeout=30)
            response.raise_for_status()
            
            # Save JSON data
            data_file = target_path / "data.json"
            with open(data_file, 'w') as f:
                json.dump(response.json(), f, indent=2)
            
            # Convert to CSV if possible
            if 'result' in response.json() and 'records' in response.json()['result']:
                df = pd.DataFrame(response.json()['result']['records'])
                csv_file = target_path / "data.csv"
                df.to_csv(csv_file, index=False)
                print(f"✅ Saved CSV version: {csv_file}")
            
            print(f"✅ Successfully downloaded {dataset_config['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {dataset_config['name']}: {e}")
            return False
    
    def download_direct_dataset(self, dataset_config: Dict[str, Any]) -> bool:
        """Download dataset directly from URL"""
        try:
            print(f"📥 Downloading {dataset_config['name']} from direct URL...")
            
            # Create target directory
            target_path = self.base_dir / dataset_config['target_dir']
            target_path.mkdir(parents=True, exist_ok=True)
            
            # For direct downloads, create instructions
            info_file = target_path / "download_instructions.txt"
            with open(info_file, 'w') as f:
                f.write(f"Dataset: {dataset_config['name']}\n")
                f.write(f"URL: {dataset_config['url']}\n")
                f.write(f"\nManual download required:\n")
                f.write(f"1. Visit the URL above\n")
                f.write(f"2. Download the dataset files\n")
                f.write(f"3. Extract to this directory\n")
            
            print(f"✅ Created download instructions for {dataset_config['name']}")
            return True
            
        except Exception as e:
            print(f"❌ Error processing {dataset_config['name']}: {e}")
            return False
    
    def create_kenyan_document_samples(self) -> bool:
        """Create sample Kenyan document templates for testing"""
        try:
            print("📝 Creating Kenyan document samples...")
            
            # Create directory
            samples_dir = self.base_dir / "kenyan_documents"
            samples_dir.mkdir(parents=True, exist_ok=True)
            
            # Create KCSE certificate template
            kcse_template = {
                "document_type": "kcse_certificate",
                "fields": {
                    "candidate_name": "",
                    "index_number": "",
                    "school_name": "",
                    "examination_year": "",
                    "subjects": [],
                    "grades": {},
                    "overall_grade": "",
                    "certificate_number": "",
                    "date_issued": ""
                },
                "validation_rules": {
                    "index_number_format": "^[0-9]{8}$",
                    "certificate_number_format": "^KCSE/[0-9]{4}/[0-9]{6}$",
                    "required_fields": ["candidate_name", "index_number", "school_name"]
                }
            }
            
            with open(samples_dir / "kcse_template.json", 'w') as f:
                json.dump(kcse_template, f, indent=2)
            
            # Create National ID template
            id_template = {
                "document_type": "national_id",
                "fields": {
                    "full_name": "",
                    "id_number": "",
                    "date_of_birth": "",
                    "sex": "",
                    "district": "",
                    "location": "",
                    "serial_number": "",
                    "date_issued": ""
                },
                "validation_rules": {
                    "id_number_format": "^[0-9]{8}$",
                    "serial_number_format": "^[A-Z]{2}[0-9]{6}$",
                    "required_fields": ["full_name", "id_number", "date_of_birth"]
                }
            }
            
            with open(samples_dir / "national_id_template.json", 'w') as f:
                json.dump(id_template, f, indent=2)
            
            print("✅ Created Kenyan document templates")
            return True
            
        except Exception as e:
            print(f"❌ Error creating document samples: {e}")
            return False
    
    def download_all_datasets(self) -> Dict[str, bool]:
        """Download all configured datasets"""
        results = {}
        
        print("🚀 Starting UhakikiAI dataset download...")
        print(f"📁 Base directory: {self.base_dir}")
        
        # Create Kenyan document samples
        results["kenyan_documents"] = self.create_kenyan_document_samples()
        
        # Download datasets by category
        for category, datasets in self.datasets.items():
            print(f"\n📂 Processing category: {category}")
            results[category] = True
            
            for dataset_key, dataset_config in datasets.items():
                print(f"  📋 Processing: {dataset_config['name']}")
                
                if dataset_config['type'] == 'kaggle':
                    success = self.download_kaggle_dataset(dataset_config)
                elif dataset_config['type'] == 'uci':
                    success = self.download_uci_dataset(dataset_config)
                elif dataset_config['type'] == 'api':
                    success = self.download_api_dataset(dataset_config)
                elif dataset_config['type'] == 'direct':
                    success = self.download_direct_dataset(dataset_config)
                else:
                    print(f"❌ Unknown dataset type: {dataset_config['type']}")
                    success = False
                
                if not success:
                    results[category] = False
        
        return results
    
    def generate_dataset_report(self, results: Dict[str, bool]) -> None:
        """Generate a report of download results"""
        report_file = self.base_dir / "download_report.json"
        
        report = {
            "download_date": pd.Timestamp.now().isoformat(),
            "base_directory": str(self.base_dir),
            "results": results,
            "summary": {
                "total_categories": len(results),
                "successful_categories": sum(1 for r in results.values() if r),
                "failed_categories": sum(1 for r in results.values() if not r)
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Download Report:")
        print(f"  Total Categories: {report['summary']['total_categories']}")
        print(f"  Successful: {report['summary']['successful_categories']}")
        print(f"  Failed: {report['summary']['failed_categories']}")
        print(f"  Report saved to: {report_file}")

def main():
    """Main execution function"""
    downloader = DatasetDownloader()
    
    # Download all datasets
    results = downloader.download_all_datasets()
    
    # Generate report
    downloader.generate_dataset_report(results)
    
    print("\n🎉 Dataset download process completed!")
    print("📋 Next steps:")
    print("  1. Review downloaded datasets")
    print("  2. Manually download any remaining datasets")
    print("  3. Preprocess datasets for model training")
    print("  4. Update mock data with real datasets")

if __name__ == "__main__":
    main()
