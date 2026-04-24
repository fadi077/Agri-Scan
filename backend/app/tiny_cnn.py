"""Lightweight CNN for first-run bootstrap weights (not a plant pathology model)."""

from __future__ import annotations

import torch.nn as nn
from torch import Tensor


class SmallCNN(nn.Module):
    """64×64 RGB input → class logits. Used only until real ResNet weights replace `best.pt`."""

    def __init__(self, num_classes: int) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )
        self.head = nn.Linear(128 * 8 * 8, num_classes)

    def forward(self, x: Tensor) -> Tensor:
        z = self.features(x)
        z = z.flatten(1)
        return self.head(z)
