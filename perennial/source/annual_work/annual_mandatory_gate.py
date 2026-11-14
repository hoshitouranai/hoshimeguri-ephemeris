"""Annual v53 invariant contract. Report failing conditions; never call partial success PASS.

Development outputs may be rendered with FAIL to enable comparison, but cannot be
LOCKED or labelled original-equivalent until every required check passes.
"""

def inspect(qa):
    year=qa['year']; bodies=qa['body_count']; src=qa['source_note']
    center=qa['annual_display_rules']; labels=qa['outer_start_markers']
    chiron=qa.get('chiron',{})
    expected=11
    checks={
      'all_12_zodiac_labels_and_color_rule':center['status']=='PASS' and len(center['sign_text_colors'])==12,
      'time_direction_and_center_period':center['center_lines']==[f'{year}年','1月 → 12月','外 → 内'],
      'all_11_tracks_including_chiron': bodies==expected and bool(qa.get('glyph_master_policy',{}).get('chiron_included')) and chiron.get('status')=='DRAWN',
      'end_arrow_per_orbit':qa['end_arrows']['status']=='PASS' and qa['end_arrows']['count']==expected,
      'outer_glyph_and_start_dotted_guide':labels.get('marker_count')==expected and labels.get('dotted_leader_count')==expected and labels.get('status')=='PASS' and all(m.get('leader_end_matches_calculated_start') for m in labels.get('markers',[])),
      'date_range_in_footer':f'{year}/1/1' in src['start_end_label'] and f'{year}/12/31' in src['start_end_label'],
      'coordinate_system_and_time_zone_in_chart':all(t in qa.get('header_subtitle','') for t in ('地心','トロピカル','JST')),
      'actual_ephemeris_in_footer':'Swiss Ephemeris' in src['calculation_verification_note'] and 'Moshier' in src['calculation_verification_note'],
      'verification_status_in_footer':'未完了' in src['calculation_verification_note'],
      'event_panel_present':qa['event_panel'] is not None,
    }
    failed=[k for k,v in checks.items() if not v]
    return {'status':'FAIL' if failed else 'PASS','checks':checks,'failed':failed,'year':year,
            'scope':'required presence only; reference image equality and independent numeric verification are separate gates',
            'safe_to_lock':False}
