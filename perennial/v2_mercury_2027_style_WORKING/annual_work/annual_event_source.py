"""Unified year-specific astronomical event calculation, all years same policy."""
from yearly_auto import panel_rows

def rows_for_year(year, zip_path=None):
    if not 1600 <= year <= 2399:
        raise ValueError("year outside supported range")
    rows = panel_rows(year)
    if not rows:
        raise ValueError(f"No events computed for {year}")
    if any(int(r['計算日時_JST'][:4]) != year for r in rows):
        raise ValueError("Cross-year event contamination")
    return rows, "year-specific Swiss Ephemeris Moshier derived events (provisional)"
