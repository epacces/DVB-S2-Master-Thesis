"""dvbs2: Galois fields, FEC codes and a DVB-S2 physical-layer simulator.

Python companion of the thesis "BCH-LDPC Concatenated Coding and High Order
Modulations for Satellite Transmitters" (E. Pacces, Politecnico di Torino, 2008).
"""
from .gf import GF2m, GFp

__version__ = "1.0.0"
__all__ = ["GF2m", "GFp", "__version__"]
