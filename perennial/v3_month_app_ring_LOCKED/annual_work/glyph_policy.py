"""v53 glyph policy: white badge is a contrast plate, not a clipping bound.
No auto-shrink/auto-move based solely on badge overflow; astronomical track unchanged.
"""
def audit_policy(audit):
    return {
        'badge_role':'contrast background; original glyph ink may intentionally extend beyond it',
        'badge_overflow_is_error':False,
        'badge_overlap_is_error':True,
        'unverified_font_is_warning':True,
        'pluto_requires_custom_vector':'Original v53 uses circle+arc+cross; font glyph ♇/P is not acceptable',
        'node_shape_warning':'Original node glyph has large paired lower circles; font rendering does not match',
        'glyphs_unapproved':True,
        'observed_overflow_count':len(audit.get('glyph_badge_overflow',[])),
        'manual_review_required':True,
    }
