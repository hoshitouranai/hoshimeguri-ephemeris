"""Independently pluggable Chiron data provider for annual v53.

Chiron is asteroid 2060, not a Moshier-major-planet target.  Requires Swiss
Ephemeris asteroid file seas_18.se1. Never invent missing positions.
"""
from __future__ import annotations
from datetime import timezone
from pathlib import Path
import hashlib, os
import numpy as np
import swisseph as swe


def discover_path(explicit=None):
    candidates = []
    if explicit: candidates.append(Path(explicit))
    if os.environ.get('V53_EPHE_DIR'): candidates.append(Path(os.environ['V53_EPHE_DIR']))
    try:
        import importlib.util
        spec=importlib.util.find_spec('kerykeion')
        if spec and spec.submodule_search_locations:
            candidates.extend(Path(p)/'sweph' for p in spec.submodule_search_locations)
    except (ImportError, ValueError): pass
    candidates.extend([Path('/usr/share/swisseph'),Path('/usr/local/share/swisseph')])
    for p in candidates:
        if (p/'seas_18.se1').is_file(): return p
    raise FileNotFoundError('Chiron requires seas_18.se1; specify --chiron-ephe-dir or V53_EPHE_DIR; cannot publish Chiron until supplied.')


def calculate_chiron(times, ephe_dir=None):
    p=discover_path(ephe_dir)
    swe.set_ephe_path(str(p))
    coords=[]; speeds=[]; flags_returned=set()
    for t in times:
        u=t.astimezone(timezone.utc)
        jd=swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600)
        vals,ret=swe.calc_ut(jd,swe.CHIRON,swe.FLG_SWIEPH|swe.FLG_SPEED)
        # Swiss Ephemeris can report MOSEPH when underlying planetary ephemeris
        # falls back; asteroid file remains required and is checked above.
        coords.append(vals[0]);speeds.append(vals[3]);flags_returned.add(ret)
    longitude=np.asarray(coords,dtype=np.float64)
    speed=np.asarray(speeds,dtype=np.float64)
    if not(np.all(np.isfinite(longitude)) and np.all((longitude>=0)&(longitude<360)) and np.all(np.isfinite(speed))):
        raise ValueError('Invalid Chiron values')
    return longitude,speed,{'engine':'Swiss Ephemeris','file':str(p/'seas_18.se1'),'file_sha256':hashlib.sha256((p/'seas_18.se1').read_bytes()).hexdigest(),'returned_flags':sorted(flags_returned),'planetary_base_note':'Swiss Ephemeris reports MOSEPH fallback for base-planet calculations; asteroid file seas_18.se1 present','status':'computed; independently verified against external reference: NO','approved_glyph_color':False,'approved_plot_geometry':False}
