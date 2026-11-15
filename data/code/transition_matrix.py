"""Read station-to-station transition matrices for the YouBike Markov-chain simulation.

Produced by data/code/youbike_transition_probs.ipynb; reads
data/processed/youbike_transition/transition_probs.parquet.

Rows = origin stations (109 in-field stations), columns = destinations
(the same 109 stations + "區外"). Each valid row sums to 1.
"""

from pathlib import Path

import numpy as np
import pandas as pd

OUTSIDE_ID = "區外"
PERIODS = ("學期", "假期")
DEFAULT_RELATIVE_PATH = Path("data/processed/youbike_transition/transition_probs.parquet")

_cache = {}


def _find_project_root(start=None):
    start = Path.cwd() if start is None else Path(start)
    for candidate in (start.resolve(), *start.resolve().parents):
        if (candidate / "AGENTS.md").is_file() and (candidate / "templates").is_dir():
            return candidate
    raise FileNotFoundError("Run inside the project containing AGENTS.md and templates/.")


def _load(path):
    path = Path(path).resolve()
    if path not in _cache:
        _cache[path] = pd.read_parquet(path, engine="pyarrow")
    return _cache[path]


def get_matrix(period, day_of_week, hour, fallback=True, path=None):
    """Return the transition matrix for one (period, day_of_week, hour).

    Parameters
    ----------
    period : "學期" or "假期"
    day_of_week : int, 1 = Monday ... 7 = Sunday
    hour : int, rent hour 0-23
    fallback : if True, an origin row whose own probability is NA (fewer than 30
        rentals) is replaced by its fallback row, estimated from the same period,
        hour and day type (weekday Mon-Fri or weekend Sat-Sun). Rows are replaced
        whole, never cell by cell, so they still sum to 1.
    path : optional path to transition_probs.parquet.

    Returns
    -------
    pandas.DataFrame, index = origin_id (109 stations), columns = dest_id
    (109 stations + "區外"). Rows that remain NA (also below threshold in the
    fallback, or no rentals at all) are all NaN.
    """
    if period not in PERIODS:
        raise ValueError(f"period must be one of {PERIODS}")
    if not 1 <= int(day_of_week) <= 7 or not 0 <= int(hour) <= 23:
        raise ValueError("day_of_week must be 1-7 and hour 0-23")

    if path is None:
        path = _find_project_root() / DEFAULT_RELATIVE_PATH
    probs = _load(path)

    stations = sorted(probs["origin_id"].unique())
    destinations = stations + [OUTSIDE_ID]

    cell = probs[
        (probs["period"] == period)
        & (probs["day_of_week"] == int(day_of_week))
        & (probs["hour"] == int(hour))
    ]

    matrix = cell.pivot(index="origin_id", columns="dest_id", values="prob")
    matrix = matrix.reindex(index=stations, columns=destinations)
    # Probabilities exist only for rows above the threshold; inside those rows,
    # destinations without trips are true zeros.
    valid_rows = cell.loc[~cell["below_threshold"], "origin_id"].unique()
    matrix.loc[matrix.index.isin(valid_rows)] = matrix.loc[matrix.index.isin(valid_rows)].fillna(0.0)

    if fallback:
        fb = cell.pivot(index="origin_id", columns="dest_id", values="prob_fallback")
        fb = fb.reindex(index=stations, columns=destinations)
        fb_valid = cell.loc[cell["prob_fallback"].notna(), "origin_id"].unique()
        fb.loc[fb.index.isin(fb_valid)] = fb.loc[fb.index.isin(fb_valid)].fillna(0.0)
        replace = ~matrix.index.isin(valid_rows)
        matrix.loc[replace] = fb.loc[replace]

    matrix.index.name = "origin_id"
    matrix.columns.name = "dest_id"
    return matrix.astype(np.float64)
