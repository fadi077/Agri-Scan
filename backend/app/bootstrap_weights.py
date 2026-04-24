"""
Create minimal `best.pt` + `class_names.json` so the API can run before you train on real plants.

This trains a tiny CNN on random tensors — outputs are NOT agricultural diagnoses.
Set AGRI_SCAN_AUTO_BOOTSTRAP=0 to skip automatic creation on startup.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from app.tiny_cnn import SmallCNN

logger = logging.getLogger(__name__)

# PlantVillage-style names so crop filtering works; text makes clear these are not trained diagnoses.
PLACEHOLDER_CLASS_NAMES = [
    "Tomato___Not_trained_replace_with_real_data",
    "Potato___Not_trained_replace_with_real_data",
    "Pepper___Not_trained_replace_with_real_data",
]


def run_bootstrap(weights_path: Path, class_names_path: Path) -> None:
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    class_names_path.parent.mkdir(parents=True, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    num_classes = len(PLACEHOLDER_CLASS_NAMES)
    torch.manual_seed(42)

    n = 384
    x = torch.rand(n, 3, 64, 64, device=device)
    y = torch.randint(0, num_classes, (n,), device=device)
    ds = TensorDataset(x.cpu(), y.cpu())
    loader = DataLoader(ds, batch_size=64, shuffle=True)

    model = SmallCNN(num_classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    crit = nn.CrossEntropyLoss()

    model.train()
    for _ in range(18):
        for xb, yb in loader:
            xb = xb.to(device)
            yb = yb.to(device)
            opt.zero_grad()
            logits = model(xb)
            loss = crit(logits, yb)
            loss.backward()
            opt.step()

    model.eval()
    payload = {
        "version": 2,
        "arch": "tiny_cnn",
        "input_size": 64,
        "diagnostic_ready": False,
        "state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
    }

    tmp_w = weights_path.with_suffix(".pt.tmp")
    tmp_c = class_names_path.with_suffix(".json.tmp")
    torch.save(payload, tmp_w)
    with open(tmp_c, "w", encoding="utf-8") as f:
        json.dump(PLACEHOLDER_CLASS_NAMES, f, indent=2)
    tmp_w.replace(weights_path)
    tmp_c.replace(class_names_path)
    logger.warning(
        "Wrote placeholder weights to %s - train on real leaf data and overwrite these files for real diagnostics.",
        weights_path,
    )
