import sys
from pathlib import Path

# Add the repository root directory to Python's module search path
sys.path.append(str(Path(__file__).parent))

from modules import ac_single_phase, ac_three_phase, circuit_builder, peem_engine, weird_circuits
