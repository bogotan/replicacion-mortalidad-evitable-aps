"""Arranque común de los scripts del artículo A5: entorno determinista (semilla de hash fija, un solo hilo en polars y
BLAS) y src/ en el camino de importación. Sin rutas absolutas."""
from __future__ import annotations

import os
import sys
from pathlib import Path

for _v in ("POLARS_MAX_THREADS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS"):
    os.environ[_v] = "1"
if os.environ.get("PYTHONHASHSEED") != "0":
    os.environ["PYTHONHASHSEED"] = "0"
    os.execv(sys.executable, [sys.executable] + sys.argv)

_SRC = next(p / "src" for p in Path(__file__).resolve().parents if (p / "src" / "aps_evitable").is_dir())
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
