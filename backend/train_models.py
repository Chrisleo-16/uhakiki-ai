#!/usr/bin/env python3
"""
Document Verification Model Training Script
Trains:
  1. RADAutoencoder  (PyTorch)  → rad_autoencoder_kenyan.pth  ← what the pipeline uses
  2. DocumentClassifier (RF)   → document_classifier.pkl
  3. BiometricVerifier  (SVM)  → biometric_verifier.pkl
  4. FraudDetector (Keras)     → fraud_detector.h5

Run from project root:
    python backend/train_models.py
    python backend/train_models.py --real-images   # use actual scanned IDs
    python backend/train_models.py --epochs 30     # more RAD training epochs
"""

import os
import sys
import json
import argparse
import warnings
import numpy as np
from pathlib import Path

warnings.filterwarnings('ignore')

# ── paths ─────────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent   # project root
DATA_PATH   = ROOT / "backend" / "data" / "training"
MODELS_PATH = ROOT / "backend" / "models"
FORENSICS   = ROOT / "backend" / "data" / "forensics" / "original"

MODELS_PATH.mkdir(parents=True, exist_ok=True)

# ── colour helpers ─────────────────────────────────────────────────────────────
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"; X = "\033[0m"
def ok(m):   print(f"{G}  ✅ {m}{X}")
def bad(m):  print(f"{R}  ❌ {m}{X}")
def warn(m): print(f"{Y}  ⚠️  {m}{X}")
def info(m): print(f"{C}  ℹ️  {m}{X}")
def hdr(m):  print(f"\n{C}{'─'*60}\n  {m}\n{'─'*60}{X}")


# ══════════════════════════════════════════════════════════════════════════════
# PART 1 — RAD AUTOENCODER  (the model your pipeline actually uses)
# ══════════════════════════════════════════════════════════════════════════════
def train_rad_autoencoder(image_dir: Path, epochs: int = 20, use_real: bool = False):
    """
    Train the Reconstruction Anomaly Detector (RAD) autoencoder.
    
    Strategy
    --------
    • Authentic images  → model learns to reconstruct them with low MSE
    • Forged / tampered → high reconstruction error flags them
    
    If real scanned ID images exist in `image_dir`, they are used.
    Otherwise a small synthetic dataset is generated so the weights
    file always gets created and the pipeline doesn't break.
    """
    hdr("1. RAD Autoencoder (PyTorch) — the core forgery detector")

    try:
        import torch
        import torch.nn as nn
        from torch.utils.data import DataLoader, TensorDataset
        from torchvision import transforms
        from PIL import Image
        sys.path.insert(0, str(ROOT / "backend"))
        from app.logic.rad_model import RADAutoencoder
    except ImportError as e:
        bad(f"Missing dependency: {e}")
        info("pip install torch torchvision Pillow")
        return None

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    info(f"Device: {device}")

    # ── load images ───────────────────────────────────────────────────────────
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),          # → [3, 224, 224]  float32 in [0,1]
    ])

    tensors = []

    if use_real and image_dir.exists():
        exts = {".jpg", ".jpeg", ".png", ".bmp"}
        paths = [p for p in image_dir.rglob("*") if p.suffix.lower() in exts]
        info(f"Found {len(paths)} real images in {image_dir}")
        for p in paths:
            try:
                img = Image.open(p).convert("RGB")
                tensors.append(preprocess(img))
            except Exception as ex:
                warn(f"Skipping {p.name}: {ex}")
    
    if len(tensors) < 10:
        warn(
            f"Only {len(tensors)} real images found — padding with synthetic data.\n"
            "  To use real images: place authentic Kenyan ID scans in\n"
            f"  {image_dir}\n"
            "  then re-run with --real-images"
        )
        # Synthetic: random noise images that look like real photos
        n_synth = max(200, 200 - len(tensors))
        for _ in range(n_synth):
            # Simulate a 'normal' document: mostly uniform with some texture
            base   = torch.rand(3, 224, 224) * 0.4 + 0.3   # mid-range values
            noise  = torch.randn(3, 224, 224) * 0.05
            tensors.append((base + noise).clamp(0, 1))
        info(f"Using {len(tensors)} total training samples ({n_synth} synthetic)")

    X = torch.stack(tensors)                        # [N, 3, 224, 224]
    dataset    = TensorDataset(X)
    loader     = DataLoader(dataset, batch_size=16, shuffle=True)

    # ── model + optimiser ─────────────────────────────────────────────────────
    model     = RADAutoencoder().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()

    # ── determine input channels the model actually expects ───────────────────
    # Probe once so we handle both 1-ch and 3-ch architectures
    with torch.no_grad():
        try:
            model(torch.zeros(1, 3, 224, 224).to(device))
            in_channels = 3
        except Exception:
            try:
                model(torch.zeros(1, 1, 224, 224).to(device))
                in_channels = 1
            except Exception as e:
                bad(f"Cannot determine model input channels: {e}")
                return None
    info(f"Model expects {in_channels}-channel input")

    # ── training loop ─────────────────────────────────────────────────────────
    print()
    best_loss = float('inf')
    for epoch in range(1, epochs + 1):
        model.train()
        epoch_loss = 0.0
        for (batch,) in loader:
            batch = batch.to(device)
            if in_channels == 1:
                import torchvision.transforms.functional as TF
                batch = TF.rgb_to_grayscale(batch)   # [N,1,224,224]

            optimizer.zero_grad()
            recon = model(batch)
            loss  = criterion(recon, batch)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg = epoch_loss / len(loader)
        bar = "█" * int(avg * 200)
        print(f"  Epoch {epoch:3d}/{epochs}  loss={avg:.6f}  {bar}")

        if avg < best_loss:
            best_loss = avg
            # save best checkpoint
            torch.save(
                {
                    "epoch":            epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "loss":             avg,
                    "in_channels":      in_channels,
                },
                MODELS_PATH / "rad_autoencoder_kenyan.pth",
            )

    ok(f"RAD Autoencoder trained  →  best loss={best_loss:.6f}")
    ok(f"Saved → {MODELS_PATH / 'rad_autoencoder_kenyan.pth'}")

    # ── derive & save threshold ───────────────────────────────────────────────
    # Run the trained model on the training set to find a good MSE threshold
    model.eval()
    mse_scores = []
    with torch.no_grad():
        for (batch,) in loader:
            batch = batch.to(device)
            if in_channels == 1:
                import torchvision.transforms.functional as TF
                batch = TF.rgb_to_grayscale(batch)
            recon = model(batch)
            mse   = nn.MSELoss(reduction='none')(recon, batch)
            mse   = mse.mean(dim=[1, 2, 3])          # per-image MSE
            mse_scores.extend(mse.cpu().numpy().tolist())

    mse_arr   = np.array(mse_scores)
    # threshold = mean + 2*std  (captures ~95 % of authentic docs as authentic)
    threshold = float(np.mean(mse_arr) + 2 * np.std(mse_arr))
    info(f"MSE  mean={np.mean(mse_arr):.6f}  std={np.std(mse_arr):.6f}")
    info(f"Threshold set to {threshold:.6f}")

    config = {
        "threshold":   threshold,
        "in_channels": in_channels,
        "train_samples": len(tensors),
        "epochs":      epochs,
        "best_loss":   best_loss,
    }
    cfg_path = MODELS_PATH / "kenyan_threshold_config.json"
    with open(cfg_path, "w") as f:
        json.dump(config, f, indent=2)
    ok(f"Threshold config saved → {cfg_path}")

    return model, threshold


# ══════════════════════════════════════════════════════════════════════════════
# PART 2 — SKLEARN / KERAS MODELS  (document classifier, biometric, fraud)
# ══════════════════════════════════════════════════════════════════════════════

class ClassicModelTrainer:
    """
    Trains the sklearn / Keras models.

    NOTE: Training data here is synthetic because we don't have labelled
    CSV files.  Replace `load_*_data()` methods with real data loaders
    once you have labelled datasets.  The models ARE saved and CAN be
    swapped into your pipeline, but they are not currently called by
    the main FastAPI routes — the RAD autoencoder handles live forgery.
    """

    def __init__(self):
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.svm import SVC
        from sklearn.preprocessing import StandardScaler
        self.rf      = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
        self.svm     = SVC(kernel='rbf', probability=True, random_state=42)
        self.scalers = {}

    # ── data generators ───────────────────────────────────────────────────────

    def load_document_data(self):
        hdr("2. Document Authenticity Classifier (RandomForest)")
        rng = np.random.default_rng(42)
        # 8 hand-crafted features
        auth = rng.normal([0.9, 0.95, 0.92, 0.88, 0.94, 0.85, 0.9, 0.91],
                          [0.1, 0.05, 0.08, 0.12, 0.06, 0.15, 0.05, 0.09],
                          size=(1000, 8)).clip(0, 1)
        forg = rng.normal([0.3, 0.4,  0.2,  0.35, 0.5,  0.3,  0.3, 0.4],
                          [0.2, 0.3,  0.25, 0.2,  0.3,  0.25, 0.2, 0.25],
                          size=(800, 8)).clip(0, 1)
        X = np.vstack([auth, forg])
        y = np.hstack([np.ones(1000), np.zeros(800)])
        return X, y

    def load_biometric_data(self):
        hdr("3. Biometric Verifier (SVM)")
        rng = np.random.default_rng(42)
        genuine = rng.standard_normal((2000, 128))
        attacks = rng.standard_normal((1200, 128)) * 1.5
        X = np.vstack([genuine, attacks])
        y = np.hstack([np.ones(2000), np.zeros(1200)])
        return X, y

    def load_fraud_data(self):
        hdr("4. Fraud Pattern Detector (Keras NN)")
        rng = np.random.default_rng(42)
        legit = rng.normal([1.2, 0.8, 0.9, 0.85, 0.3, 0.88, 0.92],
                           [0.5, 0.15, 0.1, 0.2, 0.2, 0.12, 0.08],
                           size=(5000, 7))
        fraud = rng.normal([5.5, 0.2, 0.4, 0.3, 0.7, 0.35, 0.25],
                           [1.5, 0.25, 0.3, 0.25, 0.2, 0.3, 0.2],
                           size=(2000, 7))
        X = np.vstack([legit, fraud])
        y = np.hstack([np.zeros(5000), np.ones(2000)])
        return X, y

    # ── trainers ──────────────────────────────────────────────────────────────

    def train_document_classifier(self):
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score, classification_report

        X, y = self.load_document_data()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        sc = StandardScaler()
        self.scalers['document'] = sc
        self.rf.fit(sc.fit_transform(Xtr), ytr)

        acc = accuracy_score(yte, self.rf.predict(sc.transform(Xte)))
        ok(f"Document Classifier  accuracy={acc:.4f}")
        print(classification_report(yte, self.rf.predict(sc.transform(Xte)),
                                    target_names=['Forged', 'Authentic']))
        return acc

    def train_biometric_verifier(self):
        from sklearn.model_selection import train_test_split
        from sklearn.preprocessing import StandardScaler
        from sklearn.metrics import accuracy_score, classification_report

        X, y = self.load_biometric_data()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        sc = StandardScaler()
        self.scalers['biometric'] = sc
        self.svm.fit(sc.fit_transform(Xtr), ytr)

        acc = accuracy_score(yte, self.svm.predict(sc.transform(Xte)))
        ok(f"Biometric Verifier   accuracy={acc:.4f}")
        print(classification_report(yte, self.svm.predict(sc.transform(Xte)),
                                    target_names=['Attack', 'Genuine']))
        return acc

    def train_fraud_detector(self):
        try:
            import tensorflow as tf
            from tensorflow.keras import layers, models as km
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score, classification_report
        except ImportError:
            warn("TensorFlow not installed — skipping fraud detector.")
            info("pip install tensorflow")
            return None

        X, y = self.load_fraud_data()
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

        sc = StandardScaler()
        self.scalers['fraud'] = sc
        Xtr_s = sc.fit_transform(Xtr)
        Xte_s = sc.transform(Xte)

        nn = km.Sequential([
            layers.Dense(64, activation='relu', input_shape=(Xtr.shape[1],)),
            layers.Dropout(0.3),
            layers.Dense(32, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(16, activation='relu'),
            layers.Dense(1,  activation='sigmoid'),
        ])
        nn.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        nn.fit(Xtr_s, ytr, epochs=30, batch_size=32, validation_split=0.2, verbose=1)

        ypred = (nn.predict(Xte_s) > 0.5).astype(int).flatten()
        acc   = accuracy_score(yte, ypred)
        ok(f"Fraud Detector       accuracy={acc:.4f}")
        print(classification_report(yte, ypred, target_names=['Legitimate', 'Fraudulent']))
        self.fraud_nn = nn
        return acc

    def save(self):
        import joblib
        joblib.dump(self.rf,               MODELS_PATH / 'document_classifier.pkl')
        joblib.dump(self.scalers['document'], MODELS_PATH / 'document_scaler.pkl')
        ok(f"Saved document_classifier.pkl")

        joblib.dump(self.svm,              MODELS_PATH / 'biometric_verifier.pkl')
        joblib.dump(self.scalers['biometric'], MODELS_PATH / 'biometric_scaler.pkl')
        ok(f"Saved biometric_verifier.pkl")

        if hasattr(self, 'fraud_nn'):
            self.fraud_nn.save(MODELS_PATH / 'fraud_detector.h5')
            joblib.dump(self.scalers['fraud'], MODELS_PATH / 'fraud_scaler.pkl')
            ok(f"Saved fraud_detector.h5")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Train Uhakiki-AI models")
    parser.add_argument("--real-images", action="store_true",
                        help="Use real scanned ID images from forensics/original/")
    parser.add_argument("--epochs", type=int, default=20,
                        help="RAD autoencoder training epochs (default 20)")
    parser.add_argument("--rad-only", action="store_true",
                        help="Only train the RAD autoencoder (faster)")
    args = parser.parse_args()

    print(f"\n{C}{'═'*60}")
    print("  UHAKIKI-AI  —  Model Training Pipeline")
    print(f"{'═'*60}{X}\n")
    info(f"Models will be saved to: {MODELS_PATH}")
    info(f"Image dir:               {FORENSICS}")

    # 1. RAD autoencoder — MUST train this; the whole API depends on it
    rad_result = train_rad_autoencoder(
        image_dir  = FORENSICS,
        epochs     = args.epochs,
        use_real   = args.real_images,
    )

    # 2. Classic models (optional but useful)
    if not args.rad_only:
        try:
            trainer = ClassicModelTrainer()
            doc_acc  = trainer.train_document_classifier()
            bio_acc  = trainer.train_biometric_verifier()
            fraud_acc = trainer.train_fraud_detector()
            trainer.save()
        except Exception as e:
            warn(f"Classic model training failed: {e}")
            info("The RAD autoencoder (above) is what matters for the live API.")

    # ── final summary ─────────────────────────────────────────────────────────
    print(f"\n{C}{'═'*60}")
    print("  Training complete — file inventory")
    print(f"{'═'*60}{X}")
    expected = [
        "rad_autoencoder_kenyan.pth",
        "kenyan_threshold_config.json",
        "document_classifier.pkl",
        "biometric_verifier.pkl",
        "fraud_detector.h5",
    ]
    for fname in expected:
        p = MODELS_PATH / fname
        if p.exists():
            ok(f"{fname}  ({p.stat().st_size // 1024} KB)")
        else:
            warn(f"{fname}  — not found")

    print()
    info("Next steps:")
    print("  1. Start the server:  uvicorn backend.main:app --reload")
    print("  2. Test the pipeline: python test_pipeline.py --image path/to/id.jpg --api")
    print()


if __name__ == "__main__":
    main()