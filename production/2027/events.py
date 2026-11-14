import argparse
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from scipy.optimize import brentq
import swisseph as swe

JST = timezone(timedelta(hours=9))
IDS = {'月': swe.MOON, 'ドラゴンヘッド': swe.TRUE_NODE, 'キロン': swe.CHIRON}
SIGNS = '牡羊座 牡牛座 双子座 蟹座 獅子座 乙女座 天秤座 蠍座 射手座 山羊座 水瓶座 魚座'.split()


def _jd(t):
    u=t.astimezone(timezone.utc)
    return swe.julday(u.year,u.month,u.day,u.hour+u.minute/60+u.second/3600+u.microsecond/3.6e9)

def _lon_speed(jd,ident):
    return swe.calc_ut(jd,ident,(swe.FLG_SWIEPH if ident == swe.CHIRON else swe.FLG_MOSEPH) | swe.FLG_SPEED)[0]

def year_events(year, samples=4):
    """Find sign crossings and stations from sampled ephemeris, then root-solve event times.
    All events are recomputed for the supplied year; no 2027 event table reuse.
    """
    t0=datetime(year,1,1,tzinfo=JST);t1=datetime(year+1,1,1,tzinfo=JST)
    start=_jd(t0);end=_jd(t1)
    grid=np.linspace(start,end,int(round((end-start)*samples))+1)
    records=[]
    for name,ident in IDS.items():
        vals=np.array([_lon_speed(float(jd),ident)[0] for jd in grid])
        vel=np.array([_lon_speed(float(jd),ident)[3] for jd in grid])
        unwrapped=np.rad2deg(np.unwrap(np.deg2rad(vals)))
        for i in range(len(grid)-1):
            a,b=float(grid[i]),float(grid[i+1]);lo,hi=float(unwrapped[i]),float(unwrapped[i+1])
            k0=int(np.floor(min(lo,hi)/30));k1=int(np.ceil(max(lo,hi)/30))
            for k in range(k0,k1+1):
                target=k*30
                if min(lo,hi)<target<=max(lo,hi):
                    def fn(jd):
                        value=_lon_speed(jd,ident)[0]
                        return lo+((value-vals[i]+180)%360-180)-target
                    root=brentq(fn,a,b,xtol=1e-10)
                    t=datetime.fromtimestamp((root-2440587.5)*86400,timezone.utc).astimezone(JST)
                    sign=SIGNS[k%12] if hi>lo else SIGNS[(k-1)%12]
                    records.append(dict(name=name,time=t,kind='ingress',sign=sign,retro=(hi<lo),lon=float(_lon_speed(root,ident)[0])))
            if vel[i]*vel[i+1]<0:
                root=brentq(lambda jd:_lon_speed(jd,ident)[3],a,b,xtol=1e-10)
                t=datetime.fromtimestamp((root-2440587.5)*86400,timezone.utc).astimezone(JST)
                lon=float(_lon_speed(root,ident)[0])
                records.append(dict(name=name,time=t,kind='station',sign=SIGNS[int(lon//30)],retro=bool(vel[i+1]<0),lon=lon))
    records.sort(key=lambda r:(r['time'],r['name'],r['kind']))
    assert all(r['time'].year==year for r in records)
    return records


def degree_text(longitude, ingress, retrograde):
    minutes = (1800 if retrograde else 0) if ingress else min(1799, round((longitude % 30) * 60))
    return f'{minutes // 60:02d}°{minutes % 60:02d}′'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('master', type=Path)
    parser.add_argument('ephemeris', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if not (args.ephemeris / 'seas_18.se1').is_file():
        parser.error('seas_18.se1 is required for Chiron')
    swe.set_ephe_path(str(args.ephemeris))
    with args.master.open(encoding='utf-8-sig', newline='') as stream:
        original = list(csv.DictReader(stream))
    year, = {int(row['計算日時_JST'][:4]) for row in original}
    rows = []
    for row in original:
        ingress = row['分類'] == 'サイン移動'
        retrograde = row['種類'] in ('逆行方向', '逆行開始')
        sign = row['詳細'].split('→')[-1] if ingress else SIGNS[int(float(row['黄経_度']) % 360 // 30)]
        rows.append((datetime.fromisoformat(row['計算日時_JST']), row['対象'], ingress, retrograde, sign, float(row['黄経_度'])))
    for event in year_events(year, samples=48):
        rows.append((event['time'], event['name'], event['kind'] == 'ingress', event['retro'], event['sign'], event['lon']))
    rows.sort()
    args.output.mkdir(parents=True, exist_ok=True)
    for month in [None, *range(1, 13)]:
        name = f'{year}-annual' if month is None else f'{year}-{month:02d}'
        with (args.output / f'{name}.csv').open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(['計算日時（JST）', '天体', 'イベント', 'サイン', '度数'])
            for time, body, ingress, retrograde, sign, longitude in rows:
                if month is None or month == time.month:
                    kind = ('サイン移動（逆行）' if retrograde else 'サイン移動') if ingress else ('逆行開始' if retrograde else '順行再開')
                    writer.writerow([time.isoformat(timespec='seconds'), body, kind, sign, degree_text(longitude, ingress, retrograde)])


if __name__ == '__main__':
    main()
