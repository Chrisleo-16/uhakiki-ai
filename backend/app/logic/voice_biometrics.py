"""
Voice Biometrics Implementation - MFCC-based voice recognition system
Provides non-intrusive secondary biometric verification layer
"""

import numpy as np
import librosa
import scipy
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pickle
import os
from datetime import datetime
import logging

from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import joblib


@dataclass
class VoiceProfile:
    """Voice biometric profile for a student"""
    student_id: str
    voice_features: np.ndarray
    feature_mean: np.ndarray
    feature_std: np.ndarray
    enrollment_timestamp: datetime
    quality_score: float
    sample_count: int



    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass


    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass


    
    async def _fetch_real_data(self, context) -> Dict[str, Any]:
        """Fetch real data from Kenyan institutions"""
        print(f"📡 [DATA] Fetching real data for student {context.student_id}")
        
        # Real API calls to Kenyan institutions
        real_data = {
            "student_id": context.student_id,
            "national_id": context.national_id,
            "ingestion_timestamp": datetime.now().isoformat(),
            "sources": {},
            "data_quality": 0.0,
            "completeness": 0.0,
            "errors": []
        }
        
        # HELB API integration
        try:
            helb_data = await self._fetch_helb_data(context.national_id)
            if helb_data:
                real_data["sources"]["HELB"] = helb_data
        except Exception as e:
            real_data["errors"].append(f"HELB API error: {e}")
        
        # KUCCPS API integration
        try:
            kuccps_data = await self._fetch_kuccps_data(context.national_id)
            if kuccps_data:
                real_data["sources"]["KUCCPS"] = kuccps_data
        except Exception as e:
            real_data["errors"].append(f"KUCCPS API error: {e}")
        
        # NEMIS API integration
        try:
            nemis_data = await self._fetch_nemis_data(context.national_id)
            if nemis_data:
                real_data["sources"]["NEMIS"] = nemis_data
        except Exception as e:
            real_data["errors"].append(f"NEMIS API error: {e}")
        
        # Calculate data quality metrics
        real_data["data_quality"] = self._calculate_real_data_quality(real_data["sources"])
        real_data["completeness"] = self._calculate_completeness(real_data["sources"])
        
        return real_data
    
    async def _fetch_helb_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real HELB loan data"""
        # Integration with HELB API
        # This would connect to the actual HELB system
        pass
    
    async def _fetch_kuccps_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real KUCCPS placement data"""
        # Integration with KUCCPS API
        # This would connect to the actual KUCCPS system
        pass
    
    async def _fetch_nemis_data(self, national_id: str) -> Dict[str, Any]:
        """Fetch real NEMIS academic data"""
        # Integration with NEMIS API
        # This would connect to the actual NEMIS system
        pass

class VoiceBiometricsSystem:
    """
    Advanced voice biometrics system using MFCC features
    Implements voiceprint creation, verification, and anti-spoofing measures
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Audio processing parameters
        self.sample_rate = 16000  # 16kHz for voice processing
        self.n_mfcc = 13  # Number of MFCC coefficients
        self.n_fft = 2048  # FFT window size
        self.hop_length = 512  # Hop length for STFT
        self.n_mels = 40  # Number of mel filter banks
        
        # Feature extraction parameters
        self.delta_window = 2  # Delta coefficients window
        self.delta_delta_window = 2  # Delta-delta coefficients window
        
        # Verification thresholds
        self.similarity_threshold = 0.85  # Cosine similarity threshold
        self.min_audio_length = 3.0  # Minimum audio length in seconds
        self.max_audio_length = 30.0  # Maximum audio length in seconds
        
        # Voice activity detection parameters
        self.vad_threshold = 0.3  # Voice activity threshold
        self.min_speech_ratio = 0.6  # Minimum ratio of speech in audio
        
        # Anti-spoofing parameters
        self.silence_ratio_threshold = 0.8  # Maximum allowed silence ratio
        self.energy_variance_threshold = 0.01  # Minimum energy variance
        
        # Storage paths
        self.profiles_dir = "backend/data/voice_profiles"
        self.models_dir = "backend/data/voice_models"
        
        # Create directories if they don't exist
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)
        
        # Load or initialize models
        self.scaler = self._load_or_create_scaler()
        
        # Load background model for spoofing detection
        self.background_model = self._load_background_model()
    
    def _load_or_create_scaler(self) -> StandardScaler:
        """Load or create feature scaler"""
        scaler_path = os.path.join(self.models_dir, "voice_feature_scaler.pkl")
        
        if os.path.exists(scaler_path):
            try:
                return joblib.load(scaler_path)
            except Exception as e:
                self.logger.warning(f"Failed to load scaler: {e}")
        
        # Create new scaler
        return StandardScaler()
    
    def _load_background_model(self) -> Optional[np.ndarray]:
        """Load background voice model for spoofing detection"""
        model_path = os.path.join(self.models_dir, "background_voice_model.npy")
        
        if os.path.exists(model_path):
            try:
                return np.load(model_path)
            except Exception as e:
                self.logger.warning(f"Failed to load background model: {e}")
        
        return None
    
    def extract_voice_features(self, audio_data: np.ndarray, sample_rate: int = None) -> Optional[np.ndarray]:
        """
        Extract comprehensive voice features using MFCC and derivatives
        """
        try:
            if sample_rate is None:
                sample_rate = self.sample_rate
            
            # Resample if necessary
            if sample_rate != self.sample_rate:
                audio_data = librosa.resample(audio_data, orig_sr=sample_rate, target_sr=self.sample_rate)
            
            # Pre-emphasis filter
            pre_emphasis = 0.97
            emphasized_signal = np.append(audio_data[0], audio_data[1:] - pre_emphasis * audio_data[:-1])
            
            # Extract MFCC features
            mfcc_features = librosa.feature.mfcc(
                y=emphasized_signal,
                sr=self.sample_rate,
                n_mfcc=self.n_mfcc,
                n_fft=self.n_fft,
                hop_length=self.hop_length,
                n_mels=self.n_mels
            )
            
            # Add delta and delta-delta features
            delta_features = librosa.feature.delta(mfcc_features, width=self.delta_window)
            delta_delta_features = librosa.feature.delta(mfcc_features, width=self.delta_delta_window, order=2)
            
            # Combine all features
            combined_features = np.vstack([mfcc_features, delta_features, delta_delta_features])
            
            # Apply voice activity detection
            vad_mask = self._detect_voice_activity(emphasized_signal)
            if vad_mask is not None:
                # Filter features based on voice activity
                active_frames = combined_features[:, vad_mask]
                if active_frames.shape[1] > 0:
                    combined_features = active_frames
            
            # Compute statistical features (mean, std, min, max, etc.)
            feature_stats = []
            for i in range(combined_features.shape[0]):
                feature_vector = combined_features[i, :]
                
                stats = [
                    np.mean(feature_vector),
                    np.std(feature_vector),
                    np.min(feature_vector),
                    np.max(feature_vector),
                    np.median(feature_vector),
                    np.percentile(feature_vector, 25),
                    np.percentile(feature_vector, 75)
                ]
                
                feature_stats.extend(stats)
            
            return np.array(feature_stats)
            
        except Exception as e:
            self.logger.error(f"Feature extraction failed: {e}")
            return None
    
    def _detect_voice_activity(self, audio_signal: np.ndarray) -> Optional[np.ndarray]:
        """
        Detect voice activity in audio signal
        Returns boolean mask for frames containing speech
        """
        try:
            # Compute short-time energy
            frame_length = int(0.025 * self.sample_rate)  # 25ms frames
            hop_length = int(0.010 * self.sample_rate)    # 10ms hop
            
            # Compute energy
            energy = librosa.feature.rms(
                y=audio_signal,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Normalize energy
            if np.max(energy) > 0:
                energy = energy / np.max(energy)
            
            # Simple VAD: energy threshold
            vad_mask = energy > self.vad_threshold
            
            # Apply minimum speech duration filter
            min_speech_frames = int(0.3 * self.sample_rate / hop_length)  # 0.3 seconds minimum
            
            # Remove short speech segments
            filtered_mask = self._filter_short_segments(vad_mask, min_speech_frames)
            
            return filtered_mask
            
        except Exception as e:
            self.logger.error(f"VAD failed: {e}")
            return None
    
    def _filter_short_segments(self, mask: np.ndarray, min_length: int) -> np.ndarray:
        """Filter out short segments in boolean mask"""
        filtered = np.zeros_like(mask, dtype=bool)
        
        i = 0
        while i < len(mask):
            if mask[i]:
                start = i
                while i < len(mask) and mask[i]:
                    i += 1
                end = i
                
                if (end - start) >= min_length:
                    filtered[start:end] = True
            else:
                i += 1
        
        return filtered
    
    def create_voice_profile(self, student_id: str, audio_samples: List[np.ndarray]) -> Dict[str, Any]:
        """
        Create voice profile from multiple audio samples
        """
        try:
            if len(audio_samples) < 3:
                return {
                    "success": False,
                    "error": "Minimum 3 audio samples required for enrollment"
                }
            
            all_features = []
            quality_scores = []
            
            for i, audio_data in enumerate(audio_samples):
                # Validate audio length
                duration = len(audio_data) / self.sample_rate
                if duration < self.min_audio_length or duration > self.max_audio_length:
                    quality_scores.append(0.0)
                    continue
                
                # Extract features
                features = self.extract_voice_features(audio_data)
                if features is None:
                    quality_scores.append(0.0)
                    continue
                
                # Assess audio quality
                quality = self._assess_audio_quality(audio_data)
                quality_scores.append(quality)
                
                if quality > 0.5:  # Only use good quality samples
                    all_features.append(features)
            
            if len(all_features) < 2:
                return {
                    "success": False,
                    "error": "Insufficient high-quality audio samples"
                }
            
            # Convert to numpy array
            features_array = np.array(all_features)
            
            # Fit scaler if this is the first enrollment
            if not hasattr(self.scaler, 'mean_') or self.scaler.mean_ is None:
                self.scaler.fit(features_array)
                # Save scaler
                scaler_path = os.path.join(self.models_dir, "voice_feature_scaler.pkl")
                joblib.dump(self.scaler, scaler_path)
            
            # Normalize features
            normalized_features = self.scaler.transform(features_array)
            
            # Compute voice profile (mean of normalized features)
            voice_profile_mean = np.mean(normalized_features, axis=0)
            voice_profile_std = np.std(normalized_features, axis=0)
            
            # Calculate overall quality score
            overall_quality = np.mean(quality_scores)
            
            # Create voice profile object
            voice_profile = VoiceProfile(
                student_id=student_id,
                voice_features=voice_profile_mean,
                feature_mean=voice_profile_mean,
                feature_std=voice_profile_std,
                enrollment_timestamp=datetime.now(),
                quality_score=overall_quality,
                sample_count=len(all_features)
            )
            
            # Save profile
            profile_path = os.path.join(self.profiles_dir, f"{student_id}_voice_profile.pkl")
            with open(profile_path, 'wb') as f:
                pickle.dump(voice_profile, f)
            
            # Update background model
            self._update_background_model(normalized_features)
            
            return {
                "success": True,
                "profile_id": student_id,
                "quality_score": overall_quality,
                "samples_used": len(all_features),
                "enrollment_timestamp": voice_profile.enrollment_timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Voice profile creation failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_voice(self, student_id: str, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Verify voice against stored profile
        """
        try:
            # Load voice profile
            profile_path = os.path.join(self.profiles_dir, f"{student_id}_voice_profile.pkl")
            
            if not os.path.exists(profile_path):
                return {
                    "success": False,
                    "error": "Voice profile not found",
                    "match_score": 0.0,
                    "verified": False
                }
            
            with open(profile_path, 'rb') as f:
                voice_profile = pickle.load(f)
            
            # Validate audio length
            duration = len(audio_data) / self.sample_rate
            if duration < self.min_audio_length or duration > self.max_audio_length:
                return {
                    "success": False,
                    "error": f"Audio duration {duration:.2f}s outside valid range [{self.min_audio_length}s, {self.max_audio_length}s]",
                    "match_score": 0.0,
                    "verified": False
                }
            
            # Extract features
            features = self.extract_voice_features(audio_data)
            if features is None:
                return {
                    "success": False,
                    "error": "Feature extraction failed",
                    "match_score": 0.0,
                    "verified": False
                }
            
            # Assess audio quality
            quality_score = self._assess_audio_quality(audio_data)
            if quality_score < 0.3:
                return {
                    "success": False,
                    "error": f"Audio quality too low: {quality_score:.2f}",
                    "match_score": 0.0,
                    "verified": False
                }
            
            # Normalize features
            normalized_features = self.scaler.transform(features.reshape(1, -1))
            
            # Calculate similarity scores
            cosine_sim = cosine_similarity(
                normalized_features.reshape(1, -1),
                voice_profile.voice_features.reshape(1, -1)
            )[0][0]
            
            # Calculate Mahalanobis distance
            diff = normalized_features.flatten() - voice_profile.voice_features
            mahalanobis_dist = np.sqrt(np.sum((diff ** 2) / (voice_profile.feature_std ** 2 + 1e-6)))
            
            # Convert Mahalanobis distance to similarity score
            mahalanobis_sim = 1.0 / (1.0 + mahalanobis_dist)
            
            # Combined similarity score
            combined_similarity = 0.7 * cosine_sim + 0.3 * mahalanobis_sim
            
            # Anti-spoofing check
            spoofing_score = self._detect_spoofing(audio_data, normalized_features.flatten())
            
            # Final verification decision
            verified = (combined_similarity >= self.similarity_threshold and 
                       spoofing_score < 0.5 and
                       quality_score >= 0.5)
            
            return {
                "success": True,
                "verified": verified,
                "match_score": float(combined_similarity),
                "cosine_similarity": float(cosine_sim),
                "mahalanobis_similarity": float(mahalanobis_sim),
                "quality_score": float(quality_score),
                "spoofing_score": float(spoofing_score),
                "threshold": self.similarity_threshold,
                "profile_quality": voice_profile.quality_score
            }
            
        except Exception as e:
            self.logger.error(f"Voice verification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "match_score": 0.0,
                "verified": False
            }
    
    def _assess_audio_quality(self, audio_data: np.ndarray) -> float:
        """Assess audio quality based on multiple metrics"""
        
        quality_metrics = []
        
        try:
            # Signal-to-noise ratio estimation
            signal_power = np.mean(audio_data ** 2)
            noise_floor = np.percentile(np.abs(audio_data), 10)
            noise_power = noise_floor ** 2
            
            if noise_power > 0:
                snr = 10 * np.log10(signal_power / noise_power)
                quality_metrics.append(min(max(snr / 30, 0), 1))  # Normalize to 0-1
            else:
                quality_metrics.append(0.5)
            
            # Zero crossing rate (too high = noise, too low = silence)
            zcr = librosa.feature.zero_crossing_rate(audio_data)[0]
            mean_zcr = np.mean(zcr)
            optimal_zcr = 0.1  # Typical for speech
            zcr_score = 1.0 - abs(mean_zcr - optimal_zcr) / optimal_zcr
            quality_metrics.append(max(min(zcr_score, 1), 0))
            
            # Spectral centroid (speech typically has characteristic range)
            spectral_centroids = librosa.feature.spectral_centroid(y=audio_data, sr=self.sample_rate)[0]
            mean_centroid = np.mean(spectral_centroids)
            optimal_centroid = 2000  # Hz, typical for speech
            centroid_score = 1.0 - abs(mean_centroid - optimal_centroid) / optimal_centroid
            quality_metrics.append(max(min(centroid_score, 1), 0))
            
            # Energy variance (speech should have varying energy)
            energy = librosa.feature.rms(y=audio_data)[0]
            energy_var = np.var(energy)
            if energy_var > self.energy_variance_threshold:
                quality_metrics.append(1.0)
            else:
                quality_metrics.append(energy_var / self.energy_variance_threshold)
            
            # Overall quality score
            return np.mean(quality_metrics)
            
        except Exception as e:
            self.logger.error(f"Audio quality assessment failed: {e}")
            return 0.0
    
    def _detect_spoofing(self, audio_data: np.ndarray, features: np.ndarray) -> float:
        """
        Detect potential spoofing attacks (replay, synthesis, etc.)
        Returns spoofing probability (0 = genuine, 1 = spoofed)
        """
        try:
            spoofing_indicators = []
            
            # Check for replay attack indicators
            silence_ratio = self._calculate_silence_ratio(audio_data)
            if silence_ratio > self.silence_ratio_threshold:
                spoofing_indicators.append(0.7)  # High silence ratio suspicious
            
            # Check against background model
            if self.background_model is not None:
                background_sim = cosine_similarity(
                    features.reshape(1, -1),
                    self.background_model.reshape(1, -1)
                )[0][0]
                
                if background_sim > 0.9:  # Too similar to background
                    spoofing_indicators.append(0.6)
            
            # Check for synthetic speech patterns
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio_data, sr=self.sample_rate)[0]
            rolloff_variance = np.var(spectral_rolloff)
            if rolloff_variance < 0.01:  # Too consistent = potentially synthetic
                spoofing_indicators.append(0.5)
            
            # Check for unusual periodicity
            autocorr = np.correlate(audio_data, audio_data, mode='full')
            peaks = scipy.signal.find_peaks(autocorr, height=0.1)[0]
            if len(peaks) > 0:
                peak_intervals = np.diff(peaks)
                if len(peak_intervals) > 0:
                    interval_consistency = 1.0 - (np.std(peak_intervals) / np.mean(peak_intervals))
                    if interval_consistency > 0.95:  # Too consistent = potentially synthetic
                        spoofing_indicators.append(0.4)
            
            # Overall spoofing probability
            if spoofing_indicators:
                return np.mean(spoofing_indicators)
            else:
                return 0.1  # Low default probability
            
        except Exception as e:
            self.logger.error(f"Spoofing detection failed: {e}")
            return 0.5  # Default to uncertain
    
    def _calculate_silence_ratio(self, audio_data: np.ndarray) -> float:
        """Calculate ratio of silence in audio"""
        
        # Use energy-based silence detection
        frame_length = int(0.025 * self.sample_rate)
        hop_length = int(0.010 * self.sample_rate)
        
        energy = librosa.feature.rms(y=audio_data, frame_length=frame_length, hop_length=hop_length)[0]
        
        # Normalize energy
        if np.max(energy) > 0:
            energy = energy / np.max(energy)
        
        # Count silent frames
        silent_frames = np.sum(energy < 0.01)  # Very low energy threshold
        total_frames = len(energy)
        
        return silent_frames / total_frames if total_frames > 0 else 1.0
    
    def _update_background_model(self, new_features: np.ndarray):
        """Update background voice model with new features"""
        
        try:
            if self.background_model is None:
                # Initialize with current features
                self.background_model = np.mean(new_features, axis=0)
            else:
                # Update with exponential moving average
                alpha = 0.1  # Learning rate
                self.background_model = (1 - alpha) * self.background_model + alpha * np.mean(new_features, axis=0)
            
            # Save updated model
            model_path = os.path.join(self.models_dir, "background_voice_model.npy")
            np.save(model_path, self.background_model)
            
        except Exception as e:
            self.logger.error(f"Background model update failed: {e}")


# Singleton instance for system-wide use
voice_biometrics = VoiceBiometricsSystem()
