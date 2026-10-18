"""Refreshes the static site copy of the case viewer: python -m factory_to_field.video.build_site (run ui.build_ui first)."""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parents[2]
shutil.copy(root / "factory_to_field/ui/case_viewer.html", root / "factory-to-field/case-viewer.html")
print("copied case viewer to factory-to-field/")
