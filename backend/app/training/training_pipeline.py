"""
UhakikiAI — Unified Training Pipeline v2
=========================================
Merges:
  - Original: RAD Autoencoder (PyTorch), Biometric Verifier, Fraud Detector (sklearn)
  - New:      OCR correction logging, noise pattern learning, fine-tuning dataset export

Key improvements over both originals:
  1. Shared scan_id ties image-level models to OCR-level corrections
  2. RAD MSE scores feed into per-field confidence signals
  3. Fraud detector features auto-populated from real scan outcomes
  4. Correction events can trigger incremental model retraining
  5. model_index.json tracks both PyTorch and sklearn models together
  6. export_finetune_dataset() injects noise hints learned from real scans
"""

import os
import sys
import json
import uuid
import csv
import logging
import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Optional
from PIL import Image
import torchvision.transforms as transforms
from torch.utils.data import DataLoader, Dataset
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import re

# ── Add backend to path if running standalone ────────────────────────────────
backend_path = str(Path(__file__).parent.parent)
if backend_path not in sys.path:
    sys.path.append(backend_path)

try:
    from app.logic.rad_model import RADAutoencoder
except ImportError:
    # Fallback stub so this file can run standalone
    class RADAutoencoder(nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Conv2d(1, 16, 3, stride=2, padding=1),
                nn.ReLU(),
                nn.Conv2d(16, 32, 3, stride=2, padding=1),
                nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.ConvTranspose2d(32, 16, 3, stride=2, padding=1, output_padding=1),
                nn.ReLU(),
                nn.ConvTranspose2d(16, 1, 3, stride=2, padding=1, output_padding=1),
                nn.Sigmoid(),
            )
        def forward(self, x):
            return self.decoder(self.encoder(x))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# FILE PATHS
# ═══════════════════════════════════════════════════════════════════════════════

TRAINING_DIR    = Path("training_data")
RAW_SCANS_FILE  = TRAINING_DIR / "raw_scans.jsonl"
CORRECTIONS_FILE = TRAINING_DIR / "corrections.jsonl"
NOISE_FILE      = TRAINING_DIR / "noise_patterns.json"
FINETUNE_JSONL  = TRAINING_DIR / "finetune_dataset.jsonl"
FINETUNE_CSV    = TRAINING_DIR / "finetune_dataset.csv"
STATS_FILE      = TRAINING_DIR / "stats.json"

# Fine-tuning fields
NATIONAL_ID_FIELDS = [
    "name", "id_number", "date_of_birth", "expiry_date",
    "sex", "nationality", "district",
]

SYSTEM_PROMPT = (
    "You are an expert Kenyan National ID document parser. "
    "Given raw OCR text from a scanned ID card, extract the correct field values. "
    "Ignore OCR noise, artefacts, and non-field text. "
    "Return a JSON object with keys: name, id_number, date_of_birth, expiry_date, "
    "sex, nationality, district. Use empty string for any missing field."
)


# ═══════════════════════════════════════════════════════════════════════════════
# DATASET CLASSES  (from original pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

class DocumentDataset(Dataset):
    """Image dataset for RAD Autoencoder training."""
    def __init__(self, image_paths: list, transform=None):
        self.image_paths = image_paths
        self.transform   = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        try:
            img = Image.open(self.image_paths[idx]).convert("L")
            if self.transform:
                img = self.transform(img)
            return img, 0
        except Exception as e:
            logger.warning(f"Image load error {self.image_paths[idx]}: {e}")
            return torch.zeros(1, 224, 224), 0


# ═══════════════════════════════════════════════════════════════════════════════
# NOISE PATTERN TRACKER  (from new pipeline)
# ═══════════════════════════════════════════════════════════════════════════════

class NoisePatternTracker:
    """
    Learns OCR garbage tokens from corrections.
    Grows a vocabulary per document type; injects hints into fine-tuning prompts.
    """
    def __init__(self):
        self.data: dict = self._load()

    def _load(self) -> dict:
        if NOISE_FILE.exists():
            with open(NOISE_FILE) as f:
                return json.load(f)
        return {}

    def _save(self):
        TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        with open(NOISE_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def infer_noise(self, ocr_text: str, correct_fields: dict,
                    doc_type: str = "national_id") -> list:
        KNOWN_KEYWORDS = {
            "SURNAME", "GIVEN", "NAME", "SEX", "DATE", "BIRTH", "PLACE",
            "ISSUE", "EXPIRY", "NATIONALITY", "SERIAL", "NUMBER", "ID",
            "REPUBLIC", "KENYA", "NATIONAL", "IDENTITY", "CARD", "OF",
            "JAMHURI", "KITAMBULISHO", "TAIFA", "MAISHA", "NAMBA",
            "KEN", "MALE", "FEMALE",
        }
        correct_tokens: set = set()
        for v in correct_fields.values():
            if isinstance(v, str):
                for tok in re.findall(r"[A-Z]+", v.upper()):
                    correct_tokens.add(tok)
        ocr_tokens = set(re.findall(r"\b[A-Z]{2,}\b", ocr_text.upper()))
        return [t for t in ocr_tokens if t not in KNOWN_KEYWORDS and t not in correct_tokens]

    def record_noise(self, tokens: list, doc_type: str = "national_id"):
        if doc_type not in self.data:
            self.data[doc_type] = {}
        for tok in tokens:
            self.data[doc_type][tok] = self.data[doc_type].get(tok, 0) + 1
        self._save()

    def get_top_noise(self, doc_type: str = "national_id",
                      min_count: int = 2, top_n: int = 50) -> list:
        vocab = self.data.get(doc_type, {})
        filtered = {k: v for k, v in vocab.items() if v >= min_count}
        return sorted(filtered, key=lambda x: -filtered[x])[:top_n]

    def summary(self) -> dict:
        return {
            doc_type: {
                "unique_noise_tokens": len(tokens),
                "top_10": sorted(tokens, key=lambda x: -tokens[x])[:10],
            }
            for doc_type, tokens in self.data.items()
        }


# ═══════════════════════════════════════════════════════════════════════════════
# UNIFIED TRAINER
# ═══════════════════════════════════════════════════════════════════════════════

class UnifiedTrainer:
    """
    Single entry point for all UhakikiAI training:
      - RAD Autoencoder (visual forgery)
      - Biometric Verifier (face liveness)
      - Fraud Detector (behavioural signals)
      - OCR Fine-tuning Dataset (field extraction)
    """

    def __init__(self, base_path: str = "/home/cb-fx/uhakiki-ai"):
        self.base_path    = Path(base_path)
        self.data_path    = self.base_path / "backend/data/training"
        self.models_path  = self.base_path / "backend/models"
        self.training_path = self.base_path / "backend/app/training"

        for p in [self.models_path, self.training_path,
                  self.training_path / "logs",
                  self.training_path / "checkpoints",
                  TRAINING_DIR]:
            p.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Device: {self.device}")

        self.rad_model = None
        self.noise_tracker = NoisePatternTracker()

        try:
            self.document_transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
            ])
        except Exception:
            self.document_transform = None

    # ── File helpers ──────────────────────────────────────────────────────────

    def _append_jsonl(self, path: Path, record: dict):
        TRAINING_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _load_jsonl(self, path: Path) -> list:
        if not path.exists():
            return []
        records = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def _find_scan(self, scan_id: str) -> Optional[dict]:
        for r in self._load_jsonl(RAW_SCANS_FILE):
            if r.get("scan_id") == scan_id:
                return r
        return None

    def _mark_scan_corrected(self, scan_id: str):
        records = self._load_jsonl(RAW_SCANS_FILE)
        for r in records:
            if r.get("scan_id") == scan_id:
                r["has_correction"] = True
        with open(RAW_SCANS_FILE, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ══════════════════════════════════════════════════════════════════════════
    # OCR CORRECTION PIPELINE  (from new pipeline)
    # ══════════════════════════════════════════════════════════════════════════

    def log_scan(
        self,
        ocr_text: str,
        extracted_fields: dict,
        document_type: str = "national_id",
        confidence_scores: Optional[dict] = None,
        image_path: Optional[str] = None,
        # NEW: accept visual model scores so they feed into confidence
        rad_mse: Optional[float] = None,
        fraud_risk: Optional[float] = None,
        biometric_score: Optional[float] = None,
    ) -> str:
        """
        Log a raw scan result. Returns scan_id.
        Also computes a composite confidence per-field using RAD/fraud/bio scores.
        """
        scan_id = str(uuid.uuid4())[:12]

        # Build composite confidence from visual models if available
        visual_quality = 1.0
        if rad_mse is not None:
            # Lower MSE = more authentic = higher confidence
            visual_quality *= max(0.0, 1.0 - (rad_mse / 0.1))
        if fraud_risk is not None:
            visual_quality *= (1.0 - min(fraud_risk, 1.0))

        conf = confidence_scores or {}
        for field in NATIONAL_ID_FIELDS:
            if field not in conf:
                val = extracted_fields.get(field, "")
                conf[field] = round(visual_quality * (0.9 if val else 0.1), 3)

        record = {
            "scan_id":           scan_id,
            "timestamp":         datetime.now().isoformat(),
            "document_type":     document_type,
            "ocr_text":          ocr_text,
            "extracted_fields":  extracted_fields,
            "confidence_scores": conf,
            "image_path":        image_path or "",
            "rad_mse":           rad_mse,
            "fraud_risk":        fraud_risk,
            "biometric_score":   biometric_score,
            "has_correction":    False,
        }
        self._append_jsonl(RAW_SCANS_FILE, record)
        logger.info(f"Scan logged: {scan_id}")
        return scan_id

    def log_correction(
        self,
        scan_id: str,
        corrected_fields: dict,
        notes: str = "",
        trigger_retrain: bool = False,
    ) -> dict:
        """
        Record a human correction. Auto-infers noise, optionally retrains models.
        """
        original = self._find_scan(scan_id)
        if not original:
            raise ValueError(f"Scan {scan_id!r} not found")

        merged = deepcopy(original.get("extracted_fields", {}))
        merged.update(corrected_fields)

        noise_tokens = self.noise_tracker.infer_noise(
            ocr_text=original["ocr_text"],
            correct_fields=merged,
            doc_type=original["document_type"],
        )
        self.noise_tracker.record_noise(noise_tokens, original["document_type"])

        correction = {
            "scan_id":          scan_id,
            "timestamp":        datetime.now().isoformat(),
            "document_type":    original["document_type"],
            "ocr_text":         original["ocr_text"],
            "original_fields":  original.get("extracted_fields", {}),
            "corrected_fields": corrected_fields,
            "merged_fields":    merged,
            "noise_inferred":   noise_tokens,
            "confidence_scores": original.get("confidence_scores", {}),
            "rad_mse":          original.get("rad_mse"),
            "fraud_risk":       original.get("fraud_risk"),
            "notes":            notes,
        }
        self._append_jsonl(CORRECTIONS_FILE, correction)
        self._mark_scan_corrected(scan_id)

        logger.info(f"Correction logged for {scan_id}. Noise: {noise_tokens}")

        # Optionally retrain OCR model when enough new corrections accumulate
        if trigger_retrain:
            corrections = self._load_jsonl(CORRECTIONS_FILE)
            if len(corrections) % 50 == 0:
                logger.info("Threshold reached — exporting fine-tune dataset for retraining")
                self.export_finetune_dataset()

        return correction

    def export_finetune_dataset(self, include_uncorrected: bool = False) -> list:
        """
        Build JSONL + CSV fine-tuning dataset from corrections.
        Injects noise hints learned from the noise tracker.
        """
        samples = []
        corrections = self._load_jsonl(CORRECTIONS_FILE)

        for c in corrections:
            samples.append(self._build_sample(
                ocr_text=c["ocr_text"],
                correct_fields=c["merged_fields"],
                doc_type=c["document_type"],
                scan_id=c["scan_id"],
                noise_tokens=c.get("noise_inferred", []),
                confidence_scores=c.get("confidence_scores", {}),
                source="correction",
            ))

        if include_uncorrected:
            corrected_ids = {c["scan_id"] for c in corrections}
            for s in self._load_jsonl(RAW_SCANS_FILE):
                if s["scan_id"] in corrected_ids:
                    continue
                scores = s.get("confidence_scores", {})
                avg = (sum(scores.values()) / len(scores)) if scores else 0
                if avg >= 0.85:
                    samples.append(self._build_sample(
                        ocr_text=s["ocr_text"],
                        correct_fields=s["extracted_fields"],
                        doc_type=s["document_type"],
                        scan_id=s["scan_id"],
                        noise_tokens=[],
                        confidence_scores=scores,
                        source="auto_high_confidence",
                    ))

        with open(FINETUNE_JSONL, "w") as f:
            for s in samples:
                f.write(json.dumps(s) + "\n")

        self._write_csv(samples)
        self._write_stats(samples, corrections)

        logger.info(f"Fine-tune dataset: {len(samples)} samples → {FINETUNE_JSONL}")
        return samples

    def _build_sample(self, ocr_text, correct_fields, doc_type, scan_id,
                      noise_tokens, confidence_scores, source) -> dict:
        top_noise = self.noise_tracker.get_top_noise(doc_type, min_count=2, top_n=20)
        noise_hint = (
            f"\n\n[Known OCR noise tokens to ignore for {doc_type}: "
            f"{', '.join(top_noise)}]"
        ) if top_noise else ""

        output_fields = (
            {f: correct_fields.get(f, "") for f in NATIONAL_ID_FIELDS}
            if doc_type == "national_id"
            else correct_fields
        )

        return {
            "messages": [
                {"role": "system",    "content": SYSTEM_PROMPT},
                {"role": "user",      "content": f"Extract fields from this scanned {doc_type} OCR text:\n\n{ocr_text}{noise_hint}"},
                {"role": "assistant", "content": json.dumps(output_fields, ensure_ascii=False)},
            ],
            "metadata": {
                "scan_id":           scan_id,
                "document_type":     doc_type,
                "source":            source,
                "noise_tokens":      noise_tokens,
                "confidence_scores": confidence_scores,
                "timestamp":         datetime.now().isoformat(),
            },
        }

    def _write_csv(self, samples: list):
        rows = []
        for s in samples:
            msg  = {m["role"]: m["content"] for m in s["messages"]}
            meta = s["metadata"]
            try:
                fields = json.loads(msg.get("assistant", "{}"))
            except Exception:
                fields = {}
            rows.append({
                "scan_id":       meta["scan_id"],
                "source":        meta["source"],
                "document_type": meta["document_type"],
                "ocr_text":      msg.get("user", "")[:300],
                **{f"field_{k}": v for k, v in fields.items()},
                "noise_tokens":  ", ".join(meta.get("noise_tokens", [])),
                "timestamp":     meta["timestamp"],
            })
        if rows:
            with open(FINETUNE_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def _write_stats(self, samples: list, corrections: list):
        field_counter: dict = {}
        for c in corrections:
            for field in c.get("corrected_fields", {}):
                field_counter[field] = field_counter.get(field, 0) + 1

        stats = {
            "generated_at":           datetime.now().isoformat(),
            "total_samples":          len(samples),
            "from_corrections":       sum(1 for s in samples if s["metadata"]["source"] == "correction"),
            "from_auto":              sum(1 for s in samples if s["metadata"]["source"] != "correction"),
            "total_raw_scans":        sum(1 for _ in self._load_jsonl(RAW_SCANS_FILE)),
            "total_corrections":      len(corrections),
            "most_corrected_fields":  field_counter,
            "noise_summary":          self.noise_tracker.summary(),
        }
        with open(STATS_FILE, "w") as f:
            json.dump(stats, f, indent=2)

    # ══════════════════════════════════════════════════════════════════════════
    # RAD AUTOENCODER  (from original pipeline, now returns per-image MSE)
    # ══════════════════════════════════════════════════════════════════════════

    def load_document_training_data(self):
        logger.info("Loading document training data…")
        authentic_docs, forged_docs = [], []

        authentic_path = self.data_path / "documents/authentic"
        for doc_type in ["kcse_certificates", "national_ids", "admission_letters", "helb_statements"]:
            folder = authentic_path / doc_type
            if folder.exists():
                if not list(folder.glob("*.jpg")):
                    self._create_placeholder_images(folder, 100)
                authentic_docs.extend(str(p) for p in folder.glob("*.jpg"))

        forged_path = self.data_path / "documents/forged"
        for doc_type in ["deepfake_kcse", "photoshopped_ids", "synthesized_letters", "fraudulent_helb"]:
            folder = forged_path / doc_type
            if folder.exists():
                if not list(folder.glob("*.jpg")):
                    self._create_placeholder_images(folder, 80)
                forged_docs.extend(str(p) for p in folder.glob("*.jpg"))

        logger.info(f"Documents: {len(authentic_docs)} authentic, {len(forged_docs)} forged")
        return authentic_docs, forged_docs

    def _create_placeholder_images(self, folder: Path, count: int):
        logger.info(f"Creating {count} placeholder images in {folder}")
        folder.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            img = Image.fromarray(
                np.random.randint(0, 256, (224, 224), dtype=np.uint8), mode="L"
            )
            img.save(folder / f"placeholder_{i:03d}.jpg")

    def train_rad_autoencoder(self, authentic_docs: list) -> dict:
        logger.info("Training RAD Autoencoder…")

        dataset    = DocumentDataset(authentic_docs, transform=self.document_transform)
        dataloader = DataLoader(dataset, batch_size=32, shuffle=True, num_workers=2)

        self.rad_model = RADAutoencoder().to(self.device)
        criterion  = nn.MSELoss()
        optimizer  = optim.Adam(self.rad_model.parameters(), lr=0.001)

        losses = []
        for epoch in range(50):
            epoch_loss = 0.0
            for data, _ in dataloader:
                data = data.to(self.device)
                optimizer.zero_grad()
                loss = criterion(self.rad_model(data), data)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            avg = epoch_loss / len(dataloader)
            losses.append(avg)
            if epoch % 10 == 0:
                logger.info(f"  Epoch {epoch}/50 — loss: {avg:.6f}")

        # Compute per-image MSE on authentic docs (threshold calibration)
        mse_scores = []
        self.rad_model.eval()
        with torch.no_grad():
            for data, _ in dataloader:
                data = data.to(self.device)
                recon = self.rad_model(data)
                per_img_mse = ((recon - data) ** 2).mean(dim=[1, 2, 3])
                mse_scores.extend(per_img_mse.cpu().tolist())

        threshold = float(np.percentile(mse_scores, 95))
        logger.info(f"  Calibrated threshold (95th pct): {threshold:.6f}")

        model_path = self.models_path / "rad_autoencoder_v2.pth"
        torch.save({
            "model_state_dict": self.rad_model.state_dict(),
            "losses":           losses,
            "mse_threshold":    threshold,
            "training_date":    datetime.now().isoformat(),
        }, model_path)
        logger.info(f"RAD Autoencoder saved → {model_path}")

        return {"final_loss": losses[-1], "epochs": len(losses), "mse_threshold": threshold}

    def score_document_rad(self, image_tensor) -> float:
        """
        Score a single document image. Returns MSE (lower = more authentic).
        Call this during live scans to populate rad_mse in log_scan().
        """
        if self.rad_model is None:
            pth = self.models_path / "rad_autoencoder_v2.pth"
            if pth.exists():
                self.rad_model = RADAutoencoder().to(self.device)
                ckpt = torch.load(pth, map_location=self.device)
                self.rad_model.load_state_dict(ckpt["model_state_dict"])
                self.rad_model.eval()
            else:
                return 0.0
        with torch.no_grad():
            x    = image_tensor.unsqueeze(0).to(self.device)
            recon = self.rad_model(x)
            return float(((recon - x) ** 2).mean().item())

    # ══════════════════════════════════════════════════════════════════════════
    # BIOMETRIC VERIFIER  (from original, unchanged)
    # ══════════════════════════════════════════════════════════════════════════

    def train_biometric_verifier(self) -> dict:
        logger.info("Training biometric verifier…")

        genuine  = [np.random.randn(128) for _ in range(2000)]
        attacks  = [np.random.randn(128) * 1.2 for _ in range(1200)]

        X = np.vstack([genuine, attacks])
        y = np.hstack([np.ones(len(genuine)), np.zeros(len(attacks))])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        scaler = StandardScaler()
        X_tr   = scaler.fit_transform(X_train)
        X_te   = scaler.transform(X_test)

        iso = IsolationForest(contamination=0.1, random_state=42)
        iso.fit(X_tr[y_train == 1])

        y_pred   = iso.predict(X_te)
        accuracy = float(np.mean(y_pred == (y_test == 1).astype(int)))
        logger.info(f"  Biometric accuracy: {accuracy:.4f}")

        joblib.dump(iso,    self.models_path / "biometric_verifier.pkl")
        joblib.dump(scaler, self.models_path / "biometric_scaler.pkl")

        return {"accuracy": accuracy}

    # ══════════════════════════════════════════════════════════════════════════
    # FRAUD DETECTOR  (from original + now augmented with real scan outcomes)
    # ══════════════════════════════════════════════════════════════════════════

    def _build_fraud_features_from_scans(self) -> tuple:
        """
        NEW: Extract fraud detector features from real scan log.
        Supplements synthetic data with real signal.
        Fields used:
          rad_mse → document_consistency proxy
          has_correction → label (1 = something was wrong)
          confidence_scores mean → behavioral_pattern_score proxy
        """
        real_X, real_y = [], []
        for r in self._load_jsonl(RAW_SCANS_FILE):
            mse  = r.get("rad_mse") or 0.025
            risk = r.get("fraud_risk") or 0.3
            conf = r.get("confidence_scores", {})
            avg_conf = (sum(conf.values()) / len(conf)) if conf else 0.7

            feature_vec = [
                1.0,                      # submission_frequency (unknown → neutral)
                max(0, 1 - risk),         # ip_reputation_score proxy
                max(0, 1 - mse * 10),     # document_consistency from RAD MSE
                0.85,                     # time_of_day_score (unknown → neutral)
                risk,                     # geographic_risk proxy
                avg_conf,                 # device_fingerprint_score proxy
                avg_conf,                 # behavioral_pattern_score proxy
            ]
            label = 1 if r.get("has_correction") else 0
            real_X.append(feature_vec)
            real_y.append(label)

        return np.array(real_X), np.array(real_y)

    def train_fraud_detector(self) -> dict:
        logger.info("Training fraud detector…")

        # Synthetic data (baseline)
        synth_X, synth_y = [], []
        for _ in range(5000):  # legit
            synth_X.append([
                np.random.poisson(1.2),
                np.random.normal(0.8, 0.15),
                np.random.normal(0.9, 0.1),
                np.random.normal(0.85, 0.2),
                np.random.normal(0.3, 0.2),
                np.random.normal(0.88, 0.12),
                np.random.normal(0.92, 0.08),
            ])
            synth_y.append(0)
        for _ in range(2000):  # fraud
            synth_X.append([
                np.random.poisson(5.5),
                np.random.normal(0.2, 0.25),
                np.random.normal(0.4, 0.3),
                np.random.normal(0.3, 0.25),
                np.random.normal(0.7, 0.2),
                np.random.normal(0.35, 0.3),
                np.random.normal(0.25, 0.2),
            ])
            synth_y.append(1)

        # Real scan-derived features
        real_X, real_y = self._build_fraud_features_from_scans()
        if len(real_X):
            logger.info(f"  Augmenting with {len(real_X)} real scan records")
            X = np.vstack([synth_X, real_X])
            y = np.hstack([synth_y, real_y])
        else:
            X, y = np.array(synth_X), np.array(synth_y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_tr   = scaler.fit_transform(X_train)
        X_te   = scaler.transform(X_test)

        rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        rf.fit(X_tr, y_train)

        accuracy = float(np.mean(rf.predict(X_te) == y_test))
        logger.info(f"  Fraud detector accuracy: {accuracy:.4f}")

        joblib.dump(rf,     self.models_path / "fraud_detector.pkl")
        joblib.dump(scaler, self.models_path / "fraud_scaler.pkl")

        return {"accuracy": accuracy, "real_samples_used": int(len(real_X))}

    # ══════════════════════════════════════════════════════════════════════════
    # MODEL INDEX  (from original, extended with OCR dataset metadata)
    # ══════════════════════════════════════════════════════════════════════════

    def create_model_index(self, results: dict) -> dict:
        corrections = self._load_jsonl(CORRECTIONS_FILE)
        index = {
            "training_date": datetime.now().isoformat(),
            "models": {
                "rad_autoencoder": {
                    "file":          "rad_autoencoder_v2.pth",
                    "type":          "pytorch",
                    "purpose":       "Document reconstruction anomaly detection",
                    "input_shape":   [1, 224, 224],
                    "mse_threshold": results.get("rad_autoencoder", {}).get("mse_threshold", 0.025),
                    "final_loss":    results.get("rad_autoencoder", {}).get("final_loss"),
                },
                "biometric_verifier": {
                    "file":          "biometric_verifier.pkl",
                    "type":          "sklearn",
                    "purpose":       "Facial biometric verification",
                    "input_features": 128,
                    "model_type":    "IsolationForest",
                    "accuracy":      results.get("biometric_verifier", {}).get("accuracy"),
                },
                "fraud_detector": {
                    "file":           "fraud_detector.pkl",
                    "type":           "sklearn",
                    "purpose":        "Fraud pattern detection",
                    "input_features": 7,
                    "model_type":     "RandomForest",
                    "accuracy":       results.get("fraud_detector", {}).get("accuracy"),
                    "real_samples":   results.get("fraud_detector", {}).get("real_samples_used", 0),
                },
            },
            "scalers": {
                "biometric_scaler": "biometric_scaler.pkl",
                "fraud_scaler":     "fraud_scaler.pkl",
            },
            "ocr_training": {
                "finetune_dataset":    str(FINETUNE_JSONL),
                "total_samples":       len(self._load_jsonl(FINETUNE_JSONL)) if FINETUNE_JSONL.exists() else 0,
                "total_corrections":   len(corrections),
                "noise_vocab_size":    sum(
                    len(v) for v in self.noise_tracker.data.values()
                ),
            },
        }
        path = self.models_path / "model_index.json"
        with open(path, "w") as f:
            json.dump(index, f, indent=2)
        logger.info(f"Model index saved → {path}")
        return index

    # ══════════════════════════════════════════════════════════════════════════
    # FULL PIPELINE
    # ══════════════════════════════════════════════════════════════════════════

    def run_full_training_pipeline(self) -> dict:
        """
        Run all training steps end-to-end.
        Safe to re-run — each step overwrites its own artefacts.
        """
        logger.info("═" * 60)
        logger.info("UhakikiAI Unified Training Pipeline — start")
        logger.info("═" * 60)

        results = {}

        # 1. Visual models
        authentic_docs, _ = self.load_document_training_data()
        results["rad_autoencoder"]     = self.train_rad_autoencoder(authentic_docs)
        results["biometric_verifier"]  = self.train_biometric_verifier()

        # 2. Fraud detector (augmented with any real scans already logged)
        results["fraud_detector"] = self.train_fraud_detector()

        # 3. OCR fine-tuning dataset
        samples = self.export_finetune_dataset(include_uncorrected=True)
        results["ocr_finetune"] = {"samples_exported": len(samples)}

        # 4. Model index
        results["model_index"] = self.create_model_index(results)

        # 5. Save summary
        summary_path = self.training_path / "training_results.json"
        with open(summary_path, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info("Training pipeline complete.")
        return results

    def print_stats(self):
        raw  = sum(1 for _ in self._load_jsonl(RAW_SCANS_FILE))
        corr = sum(1 for _ in self._load_jsonl(CORRECTIONS_FILE))
        print(f"\n📊 UhakikiAI Training Stats")
        print(f"   Raw scans   : {raw}")
        print(f"   Corrections : {corr}")
        print(f"   Coverage    : {corr/raw*100:.1f}%" if raw else "   Coverage: N/A")
        print(f"\n🔇 Noise patterns:")
        for dt, info in self.noise_tracker.summary().items():
            print(f"   [{dt}] {info['unique_noise_tokens']} tokens | top: {info['top_10']}")


# ═══════════════════════════════════════════════════════════════════════════════
# DROP-IN INTEGRATION HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def integrate_with_document_service(
    trainer: UnifiedTrainer,
    scan_result: dict,
    image_path: Optional[str] = None,
) -> str:
    """
    Call after DocumentScanningService.process_document().
    Automatically populates all score fields from the scan result.

    Example:
        result   = document_service.process_document(base64_image)
        scan_id  = integrate_with_document_service(trainer, result)
        # When user corrects a field in the UI:
        trainer.log_correction(scan_id, {"name": "Leo Chrisben Evans"})
    """
    fields  = scan_result.get("extracted_fields", {})
    quality = scan_result.get("quality_analysis", {})
    forgery = scan_result.get("forgery_analysis", {})

    rad_mse        = None
    fraud_risk     = forgery.get("risk_score")
    bio_score      = None

    # If quality_score present, derive a rough MSE proxy (inverse)
    qs = quality.get("quality_score", 0.5)
    if qs > 0:
        rad_mse = round((1 - qs) * 0.05, 6)

    return trainer.log_scan(
        ocr_text=scan_result.get("extracted_text", ""),
        extracted_fields=fields,
        document_type=scan_result.get("document_type", "unknown"),
        image_path=image_path or "",
        rad_mse=rad_mse,
        fraud_risk=fraud_risk,
        biometric_score=bio_score,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN  (mirrors original pipeline's CLI entry point)
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    trainer = UnifiedTrainer()
    results = trainer.run_full_training_pipeline()

    print("\n" + "=" * 60)
    print("TRAINING SUMMARY")
    print("=" * 60)
    rad = results.get("rad_autoencoder", {})
    bio = results.get("biometric_verifier", {})
    frd = results.get("fraud_detector", {})
    ocr = results.get("ocr_finetune", {})
    print(f"RAD Autoencoder   — final loss: {rad.get('final_loss', 'N/A'):.6f}  "
          f"threshold: {rad.get('mse_threshold', 'N/A'):.6f}")
    print(f"Biometric Verifier— accuracy:   {bio.get('accuracy', 'N/A'):.4f}")
    print(f"Fraud Detector    — accuracy:   {frd.get('accuracy', 'N/A'):.4f}  "
          f"real samples: {frd.get('real_samples_used', 0)}")
    print(f"OCR Fine-tune     — samples:    {ocr.get('samples_exported', 0)}")
    print(f"\nAll artefacts → {trainer.models_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()