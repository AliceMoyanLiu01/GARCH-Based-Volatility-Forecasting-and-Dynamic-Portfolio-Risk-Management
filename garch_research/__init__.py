"""Causal volatility forecasting and portfolio research."""
import os
from pathlib import Path

# arch imports matplotlib, so set the writable cache before any model import.
os.environ.setdefault('MPLCONFIGDIR', str(Path('.cache/matplotlib').resolve()))
