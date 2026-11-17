"""Locations for the frozen five-creator snapshot and its shared operations."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CREATORS = ROOT.parents[1] / "creators"
PEER_SLUGS = ("alex-hormozi", "codie-sanchez", "dan-martell", "nick-huber", "sahil-bloom")


def peer_glob(pattern):
    """Select only the five creators maintained by this snapshot pipeline."""
    return [path for path in CREATORS.glob(pattern)
            if path.relative_to(CREATORS).parts[0] in PEER_SLUGS]
