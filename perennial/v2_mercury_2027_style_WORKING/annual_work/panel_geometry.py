"""Year-independent v53 panel geometry. Only content is year-dependent."""
LEFT=1779
WIDTH=1205
# One fixed design for all years, derived from approved 2027 layout.
COMMON={'top':272,'heights':[283,232,169,169,169,169,169],
        'gap':4,'y_starts':[272,559,795,968,1141,1314,1487],
        'heading_y':55,'event_y':108,'line_step':55}
def layout(year):
    return {**COMMON, 'heights':list(COMMON['heights']), 'y_starts':list(COMMON['y_starts'])}
def cards(year):
    cfg=layout(year)
    return [(LEFT,y,LEFT+WIDTH,y+h) for y,h in zip(cfg['y_starts'],cfg['heights'])]
