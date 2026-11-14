from shared_page_typography import FOOTER_MAIN_PT, FOOTER_SOURCE_PT, FOOTER_MAIN_Y_FRAC, FOOTER_SOURCE_Y_FRAC, FOOTER_LEFT_X_FRAC
from annual_fixed_style import WIDTH, HEIGHT
"""Annual chart source footer. Fixed v53 2027 original wording; never invent verification for another year."""
def draw_source_note(ax, year, start_label, end_label):
    first=f'● 始点：{start_label}  → 矢印先端：{end_label}'
    if year == 2027:
        second='出典・検証：Swiss Ephemeris（Moshier方式）／Astrodienst 2027年日別表と照合。'
        evidence='2027 approved original wording retained; independent source check remains separate'
    else:
        second='出典・検証：Swiss Ephemeris（Moshier方式）。独立照合は未完了。'
        evidence='No claim that other years were compared to Astrodienst'
    t1=ax.text(WIDTH*FOOTER_LEFT_X_FRAC,HEIGHT*(1-FOOTER_MAIN_Y_FRAC),first,fontsize=FOOTER_MAIN_PT,color='#263E56',va='center',ha='left',zorder=20)
    t2=ax.text(WIDTH*FOOTER_LEFT_X_FRAC,HEIGHT*(1-FOOTER_SOURCE_Y_FRAC),second,fontsize=FOOTER_SOURCE_PT,color='#536A7F',va='center',ha='left',zorder=20)
    return {'status':'implemented','line_count':2,'start_end_label':first,'calculation_verification_note':second,'evidence_policy':evidence,'artists':[t1,t2]}
