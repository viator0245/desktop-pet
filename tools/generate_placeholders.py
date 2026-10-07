"""Regenerate original local PNGs only; performs no downloads."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PySide6.QtWidgets import QApplication
from src.assets import Assets
from src.config import Config, PROJECT_ROOT

app = QApplication([])
# Use an empty root to request the procedural fallback, even on later runs.
assets = Assets(Config(), PROJECT_ROOT / ".nonexistent-placeholder-source")
root = PROJECT_ROOT / "assets"
metadata = {"canvas": [256, 256], "default_foot_anchor": [128, 256], "default_hand_anchor": [177, 159], "frames": {}}
for state, frames in assets.frames.items():
    folder = root / "sakuragi" / state
    folder.mkdir(parents=True, exist_ok=True)
    for i, frame in enumerate(frames, 1):
        name = f"{i:02}.png"
        if not frame.pixmap.save(str(folder / name)):
            raise RuntimeError(f"Unable to save {name}")
        metadata["frames"][f"{state}/{name}"] = {"foot_anchor": list(frame.foot), "hand_anchor": list(frame.hand)}
(root / "sakuragi" / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
assets.ball.save(str(root / "basketball.png"))
(root / "hoop").mkdir(exist_ok=True)
assets.hoop.save(str(root / "hoop" / "hoop.png"))
(root / "hoop" / "metadata.json").write_text(json.dumps({"canvas": [150,230], "floor_anchor": [75,230], "rim_center": [48,73], "rim_radius": 20, "backboard_x": 95}, indent=2), encoding="utf-8")
print("Generated 84 original player frames, basketball and hoop.")
