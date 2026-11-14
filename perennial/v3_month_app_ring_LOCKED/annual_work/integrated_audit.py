"""Non-destructive integrated image and risk audit for annual v53 (draft)."""
from pathlib import Path
import hashlib
import numpy as np
from PIL import Image

ROIS = {
    'header':(0,0,3060,220),
    'circular_chart':(130,220,1550,1690),
    'event_panel':(1760,220,3010,1680),
    'bottom_footer':(0,1690,3060,1818),
}

def compare(reference, candidate, metadata):
    with Image.open(reference) as a, Image.open(candidate) as b:
        a=np.asarray(a.convert('RGB'),dtype=np.int16)
        b=np.asarray(b.convert('RGB'),dtype=np.int16)
    if a.shape!=b.shape:raise ValueError(f'image dimensions disagree: {a.shape} vs {b.shape}')
    change=np.any(a!=b,axis=2)
    maximum=np.max(np.abs(a-b),axis=2)
    out={}
    for name,(x0,y0,x1,y1) in ROIS.items():
        area=change[y0:y1,x0:x1]
        out[name]={
            'bounds_px':[x0,y0,x1,y1],
            'pixels_compared':int(area.size),
            'different_pixels':int(area.sum()),
            'difference_fraction':round(float(area.mean()),6),
            'mean_absolute_channel_error':round(float(np.abs(a[y0:y1,x0:x1]-b[y0:y1,x0:x1]).mean()),3),
            'maximum_channel_difference':int(maximum[y0:y1,x0:x1].max()),
        }
    findings=[]
    if not metadata.get('glyph_master_policy',{}).get('chiron_included',False):
        findings.append({'severity':'BLOCKER','id':'CHIRON_NOT_DRAWN','message':'Chiron longitude calculated but its approved rendering specification and drawn track are missing.'})
    if metadata.get('event_panel',{}).get('year')==2027 and not metadata.get('event_master_recalculation'):
        findings.append({'severity':'BLOCKER','id':'EVENT_MASTER_UNVERIFIED','message':'Event master verification missing'})
    findings.append({'severity':'BLOCKER','id':'INDEPENDENT_EPHEMERIS','message':'69 Moshier recalculations do not constitute independent ephemeris verification.'})
    findings.append({'severity':'BLOCKER','id':'2028_AUTO_LABELS','message':'2028 rule-based glyph/badge placement has not yet been implemented.'})
    findings.append({'severity':'BLOCKER','id':'DESIGN_APPROVAL','message':'Original v53 page and current trial differ significantly, with typography, tracks, and header not approved.'})
    layout=metadata.get('panel_layout_audit',{})
    if layout.get('outside_card') or layout.get('text_bbox_overlap'):
        findings.append({'severity':'REVIEW','id':'PANEL_TEXT','message':'Panel bbox warnings detected.'})
    return {
      'status':'NOT_LOCKED',
      'method':'RGB exact pixel comparison by fixed regions; no registration, resizing or manipulation',
      'source_sha256':hashlib.sha256(Path(reference).read_bytes()).hexdigest(),
      'candidate_sha256':hashlib.sha256(Path(candidate).read_bytes()).hexdigest(),
      'image_size':[b.shape[1],b.shape[0]],
      'regions':out,
      'uncovered_regions_note':'Regions intentionally non-overlapping in x except header/footer; remaining margins not covered by regional summary.',
      'reference_image_role':'Design reference, NOT numerical ephemeris authority',
      'blocking_findings':findings,
      'ready_for_lock':False,
    }
