#!/usr/bin/env python3
"""
Test script to validate UhakikiAI models with CASIA dataset
Tests forgery detection and liveness detection on real dataset images
"""

import os
import sys
import time
import asyncio
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import cv2
from PIL import Image

# Add backend to path
sys.path.append('/home/cb-fx/uhakiki-ai/backend')

from app.logic.forgery_detector import detect_pixel_anomalies
from app.logic.liveness_detector import MBICSystem
from app.logic.face_extractor import face_extractor

class CASIATestRunner:
    def __init__(self):
        self.casia_path = Path("/home/cb-fx/uhakiki-ai/casia")
        self.results = {
            'authentic_tests': [],
            'spoofed_tests': [],
            'summary': {}
        }
        
    def get_test_images(self, max_per_category: int = 10) -> Tuple[List[str], List[str]]:
        """Get sample images from CASIA datasets"""
        authentic_images = []
        spoofed_images = []
        
        # CASIA1 authentic images
        casia1_au = self.casia_path / "CASIA1" / "Au"
        if casia1_au.exists():
            au_files = list(casia1_au.glob("*.jpg"))[:max_per_category//2]
            authentic_images.extend([str(f) for f in au_files])
        
        # CASIA2 authentic images
        casia2_au = self.casia_path / "CASIA2" / "Au"
        if casia2_au.exists():
            au_files = list(casia2_au.glob("*.jpg"))[:max_per_category//2]
            authentic_images.extend([str(f) for f in au_files])
        
        # CASIA1 spoofed images
        casia1_sp = self.casia_path / "CASIA1" / "Sp"
        if casia1_sp.exists():
            sp_files = list(casia1_sp.glob("*.jpg"))[:max_per_category//2]
            spoofed_images.extend([str(f) for f in sp_files])
        
        # CASIA2 spoofed images
        casia2_tp = self.casia_path / "CASIA2" / "Tp"
        if casia2_tp.exists():
            tp_files = list(casia2_tp.glob("*.jpg"))[:max_per_category//2]
            spoofed_images.extend([str(f) for f in tp_files])
            # Also try TIF files
            tp_files = list(casia2_tp.glob("*.tif"))[:max_per_category//2]
            spoofed_images.extend([str(f) for f in tp_files])
        
        return authentic_images[:max_per_category], spoofed_images[:max_per_category]
    
    async def test_forgery_detection(self, image_path: str, expected_type: str) -> Dict:
        """Test forgery detection on a single image"""
        try:
            # Create a mock UploadFile object
            class MockUploadFile:
                def __init__(self, filepath):
                    self.filepath = filepath
                    self.filename = os.path.basename(filepath)
                
                async def read(self):
                    with open(self.filepath, 'rb') as f:
                        return f.read()
            
            mock_file = MockUploadFile(image_path)
            start_time = time.time()
            
            # Run forgery detection
            result = await detect_pixel_anomalies(mock_file)
            processing_time = time.time() - start_time
            
            # Extract key metrics
            forgery_prob = result.get('forgery_probability', 0.0)
            is_forgery = result.get('is_forgery', False)
            confidence = result.get('confidence', 0.0)
            
            # Determine if detection was correct
            expected_forgery = (expected_type == 'spoofed')
            detection_correct = is_forgery == expected_forgery
            
            return {
                'image_path': image_path,
                'expected_type': expected_type,
                'detected_as_forgery': is_forgery,
                'forgery_probability': forgery_prob,
                'confidence': confidence,
                'processing_time': processing_time,
                'detection_correct': detection_correct,
                'error': None
            }
            
        except Exception as e:
            return {
                'image_path': image_path,
                'expected_type': expected_type,
                'detected_as_forgery': False,
                'forgery_probability': 0.0,
                'confidence': 0.0,
                'processing_time': 0.0,
                'detection_correct': False,
                'error': str(e)
            }
    
    def test_liveness_detection(self, image_path: str) -> Dict:
        """Test liveness detection on a single image"""
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Initialize MBIC system
            mbic = MBICSystem()
            start_time = time.time()
            
            # Process image for liveness
            result = mbic.process_mbic_frame(img, known_encoding=None)
            processing_time = time.time() - start_time
            
            return {
                'image_path': image_path,
                'liveness_status': result.get('status', 'unknown'),
                'face_detected': result.get('face_detected', False),
                'challenge_met': result.get('challenge_met', False),
                'processing_time': processing_time,
                'error': None
            }
            
        except Exception as e:
            return {
                'image_path': image_path,
                'liveness_status': 'error',
                'face_detected': False,
                'challenge_met': False,
                'processing_time': 0.0,
                'error': str(e)
            }
    
    async def run_tests(self, max_images: int = 20):
        """Run comprehensive tests on CASIA dataset"""
        print("🧪 Starting CASIA Dataset Validation Tests...")
        print("=" * 60)
        
        # Get test images
        authentic_imgs, spoofed_imgs = self.get_test_images(max_images // 2)
        
        print(f"📊 Test Dataset:")
        print(f"   Authentic images: {len(authentic_imgs)}")
        print(f"   Spoofed images: {len(spoofed_imgs)}")
        print(f"   Total images: {len(authentic_imgs) + len(spoofed_imgs)}")
        print()
        
        # Test authentic images
        print("🔍 Testing Authentic Images...")
        for i, img_path in enumerate(authentic_imgs):
            print(f"   Testing {i+1}/{len(authentic_imgs)}: {os.path.basename(img_path)}")
            
            # Test forgery detection
            forgery_result = await self.test_forgery_detection(img_path, 'authentic')
            self.results['authentic_tests'].append(forgery_result)
            
            # Test liveness detection
            liveness_result = self.test_liveness_detection(img_path)
            forgery_result['liveness_result'] = liveness_result
            
            if forgery_result['error']:
                print(f"      ❌ Forgery detection failed: {forgery_result['error']}")
            else:
                status = "✅" if forgery_result['detection_correct'] else "❌"
                print(f"      {status} Forgery: {forgery_result['forgery_probability']:.3f}")
            
            if liveness_result['error']:
                print(f"      ❌ Liveness detection failed: {liveness_result['error']}")
            else:
                print(f"      ✅ Liveness: {liveness_result['liveness_status']}")
        
        print()
        print("🎭 Testing Spoofed Images...")
        for i, img_path in enumerate(spoofed_imgs):
            print(f"   Testing {i+1}/{len(spoofed_imgs)}: {os.path.basename(img_path)}")
            
            # Test forgery detection
            forgery_result = await self.test_forgery_detection(img_path, 'spoofed')
            self.results['spoofed_tests'].append(forgery_result)
            
            # Test liveness detection
            liveness_result = self.test_liveness_detection(img_path)
            forgery_result['liveness_result'] = liveness_result
            
            if forgery_result['error']:
                print(f"      ❌ Forgery detection failed: {forgery_result['error']}")
            else:
                status = "✅" if forgery_result['detection_correct'] else "❌"
                print(f"      {status} Forgery: {forgery_result['forgery_probability']:.3f}")
            
            if liveness_result['error']:
                print(f"      ❌ Liveness detection failed: {liveness_result['error']}")
            else:
                print(f"      ✅ Liveness: {liveness_result['liveness_status']}")
        
        # Calculate summary statistics
        self.calculate_summary()
        
    def calculate_summary(self):
        """Calculate test summary statistics"""
        authentic_tests = self.results['authentic_tests']
        spoofed_tests = self.results['spoofed_tests']
        
        # Forgery detection accuracy
        authentic_correct = sum(1 for t in authentic_tests if t['detection_correct'])
        spoofed_correct = sum(1 for t in spoofed_tests if t['detection_correct'])
        
        total_authentic = len(authentic_tests)
        total_spoofed = len(spoofed_tests)
        total_tests = total_authentic + total_spoofed
        
        authentic_accuracy = (authentic_correct / total_authentic * 100) if total_authentic > 0 else 0
        spoofed_accuracy = (spoofed_correct / total_spoofed * 100) if total_spoofed > 0 else 0
        overall_accuracy = ((authentic_correct + spoofed_correct) / total_tests * 100) if total_tests > 0 else 0
        
        # Processing times
        all_times = [t['processing_time'] for t in authentic_tests + spoofed_tests if t['processing_time'] > 0]
        avg_processing_time = np.mean(all_times) if all_times else 0
        
        # Liveness detection
        liveness_success = sum(1 for t in authentic_tests + spoofed_tests 
                             if t.get('liveness_result', {}).get('face_detected', False))
        liveness_accuracy = (liveness_success / total_tests * 100) if total_tests > 0 else 0
        
        self.results['summary'] = {
            'total_tests': total_tests,
            'authentic_images': total_authentic,
            'spoofed_images': total_spoofed,
            'authentic_accuracy': authentic_accuracy,
            'spoofed_accuracy': spoofed_accuracy,
            'overall_accuracy': overall_accuracy,
            'avg_processing_time': avg_processing_time,
            'liveness_accuracy': liveness_accuracy,
            'true_positives': spoofed_correct,
            'true_negatives': authentic_correct,
            'false_positives': total_authentic - authentic_correct,
            'false_negatives': total_spoofed - spoofed_correct
        }
    
    def print_summary(self):
        """Print test summary"""
        summary = self.results['summary']
        
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        print(f"🔢 Total Images Tested: {summary['total_tests']}")
        print(f"   Authentic: {summary['authentic_images']}")
        print(f"   Spoofed: {summary['spoofed_images']}")
        print()
        
        print("🎯 FORGERY DETECTION ACCURACY:")
        print(f"   Authentic Images: {summary['authentic_accuracy']:.1f}%")
        print(f"   Spoofed Images: {summary['spoofed_accuracy']:.1f}%")
        print(f"   Overall Accuracy: {summary['overall_accuracy']:.1f}%")
        print()
        
        print("⚡ PERFORMANCE:")
        print(f"   Avg Processing Time: {summary['avg_processing_time']:.3f}s")
        print(f"   Liveness Detection: {summary['liveness_accuracy']:.1f}%")
        print()
        
        print("📈 CONFUSION MATRIX:")
        print(f"   True Positives:  {summary['true_positives']:3d} (correctly detected spoofed)")
        print(f"   True Negatives:  {summary['true_negatives']:3d} (correctly detected authentic)")
        print(f"   False Positives: {summary['false_positives']:3d} (authentic marked as spoofed)")
        print(f"   False Negatives: {summary['false_negatives']:3d} (spoofed marked as authentic)")
        
        # Calculate additional metrics
        precision = summary['true_positives'] / (summary['true_positives'] + summary['false_positives']) if (summary['true_positives'] + summary['false_positives']) > 0 else 0
        recall = summary['true_positives'] / (summary['true_positives'] + summary['false_negatives']) if (summary['true_positives'] + summary['false_negatives']) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print()
        print("📊 DERIVED METRICS:")
        print(f"   Precision: {precision:.3f}")
        print(f"   Recall: {recall:.3f}")
        print(f"   F1-Score: {f1_score:.3f}")
        
        print("\n" + "=" * 60)

async def main():
    """Main test runner"""
    runner = CASIATestRunner()
    await runner.run_tests(max_images=20)
    runner.print_summary()

if __name__ == "__main__":
    asyncio.run(main())
