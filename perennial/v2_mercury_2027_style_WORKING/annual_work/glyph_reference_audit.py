"""Reference vs rendered glyph audit. Provisional diagnostic, NOT auto-approval."""
from pathlib import Path
import csv, json
import numpy as np
from PIL import Image,ImageDraw,ImageFont

def audit(reference_path,render_path,ledger_path,palette,output_dir):
    ref=np.asarray(Image.open(reference_path).convert('RGB')).astype(np.int16)
    rendered=np.asarray(Image.open(render_path).convert('RGB')).astype(np.int16)
    assert ref.shape==rendered.shape==(1818,3060,3)
    with open(ledger_path,encoding='utf-8-sig',newline='') as f: ledger=list(csv.DictReader(f))
    rows=[]; cards=[]
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',21)
    for entry in ledger:
        name=entry['天体'];cx=int(round(float(entry['表示中心X_px_概算'])));cy=int(round(float(entry['表示中心Y_px_概算'])))
        color=palette.get(name)
        radius=15 # ignore surrounding white-circle border, tails outside circle analyzed separately
        bounds=(cx-26,cy-26,cx+27,cy+27)
        a=ref[bounds[1]:bounds[3],bounds[0]:bounds[2]]
        b=rendered[bounds[1]:bounds[3],bounds[0]:bounds[2]]
        rgb=np.array([int(color[i:i+2],16) for i in (1,3,5)],dtype=np.float32) if color else None
        yy,xx=np.ogrid[bounds[1]:bounds[3],bounds[0]:bounds[2]]
        mask=(xx-cx)**2+(yy-cy)**2 <=radius**2
        # A candidate mask requires close color AND separation from white canvas.
        # Anti-aliasing and overlapping trajectories make this inherently uncertain.
        def chroma(img):
            dif=np.sqrt(((img.astype(np.float32)-rgb)**2).sum(axis=2)) if rgb is not None else np.full(img.shape[:2],1e6)
            return (dif<=50)&(img.max(axis=2)-img.min(axis=2)>=15)&mask
        ma=chroma(a);mb=chroma(b)
        inter=int((ma&mb).sum());union=int((ma|mb).sum())
        j=round(inter/union,4) if union else None
        row={'天体':name,'中心X_暫定':cx,'中心Y_暫定':cy,'基準色':color,'原本の候補画素':int(ma.sum()),'試作の候補画素':int(mb.sum()),'共有候補画素':inter,'IoU_参考値':j,'判定':'候補比較のみ・背景軌跡混入の可能性あり','座標確度':entry['確度']}
        rows.append(row)
        left=Image.fromarray(np.uint8(a)).resize((159,159),Image.Resampling.NEAREST)
        right=Image.fromarray(np.uint8(b)).resize((159,159),Image.Resampling.NEAREST)
        cards.append((name,color,j,left,right))
    output_dir=Path(output_dir);output_dir.mkdir(exist_ok=True,parents=True)
    outcsv=output_dir/'第二十八回_11対象_色形状候補比較.csv'
    with open(outcsv,'w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    cw,ch=420,210;w=cw*2;h=ch*6+55
    panel=Image.new('RGB',(w,h),'#f7f8fb');draw=ImageDraw.Draw(panel)
    draw.text((20,12),'v53 reference / Python trial | candidate-color pixel audit',font=font,fill='#253548')
    for i,(name,color,j,left,right) in enumerate(cards):
        row=i//2;col=i%2;x=col*cw;y=row*ch+55
        draw.text((x+8,y+2),f'{name}  IoU={j if j is not None else "N/A"}',font=font,fill='#202d3b')
        panel.paste(left,(x+14,y+36));panel.paste(right,(x+191,y+36))
        draw.text((x+40,y+191),'v53',font=font,fill='#526574');draw.text((x+229,y+191),'Python',font=font,fill='#526574')
    outpng=output_dir/'第二十八回_11対象_原本試作_共通比較.png';panel.save(outpng)
    return rows,outcsv,outpng
