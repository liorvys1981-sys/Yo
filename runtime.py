"""FACADE retrocompatible — la logica vive en rtpkg/. Baseline original en .reorg_2026-10-08/."""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "rtpkg"))
from rtpkg import *  # noqa
