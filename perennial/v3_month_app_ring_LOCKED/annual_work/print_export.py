"""A4 landscape print export for annual_engine output; preserves approved pixel drawing.
Raster content is placed proportionally, never cropped, stretched or recolored.
"""
from pathlib import Path
import hashlib,json
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
import fitz

PAGE_W, PAGE_H=landscape(A4)
MARGIN_MM=6.0

def export_one(png,pdf,margin_mm=MARGIN_MM):
    png=Path(png);pdf=Path(pdf)
    with Image.open(png) as im:
        w,h=im.size
        assert im.mode in ('RGB','RGBA','P'),'PNG unexpected color mode'
    margin=margin_mm*72/25.4
    slot_w=PAGE_W-2*margin;slot_h=PAGE_H-2*margin
    scale=min(slot_w/w,slot_h/h)
    draw_w=w*scale;draw_h=h*scale
    x=(PAGE_W-draw_w)/2;y=(PAGE_H-draw_h)/2
    c=canvas.Canvas(str(pdf),pagesize=(PAGE_W,PAGE_H),pageCompression=1)
    c.drawImage(str(png),x,y,width=draw_w,height=draw_h,mask='auto')
    c.showPage();c.save()
    doc=fitz.open(pdf)
    assert len(doc)==1
    p=doc[0]; assert abs(p.rect.width-PAGE_W)<.1 and abs(p.rect.height-PAGE_H)<.1
    imgs=p.get_images(full=True)
    assert len(imgs)==1
    d={"pdf":pdf.name,"source_png":png.name,"png_sha256":hashlib.sha256(png.read_bytes()).hexdigest(),"page_mm":[round(PAGE_W*25.4/72,2),round(PAGE_H*25.4/72,2)],"image_pixel_dimensions":[w,h],"embedded_images":len(imgs),"image_placement_mm":{"left":round(x*25.4/72,2),"bottom":round(y*25.4/72,2),"width":round(draw_w*25.4/72,2),"height":round(draw_h*25.4/72,2)},"effective_dpi":round(w/(draw_w/72)),"preserve_aspect":True,"cropped":False,"pdf_sha256":hashlib.sha256(pdf.read_bytes()).hexdigest()}
    # Inspect a 150-dpi raster from PDF (can compare center cropped source after scaling)
    pix=p.get_pixmap(matrix=fitz.Matrix(150/72,150/72),alpha=False)
    render=pdf.with_name(pdf.stem+'_PDF確認.png');pix.save(render)
    d['pdf_render']=render.name
    doc.close()
    return d

def export_pair(folder):
    folder=Path(folder)
    results=[export_one(folder/f'stage39_{year}.png',folder/f'星めぐり年間図_{year}_A4横_試作.pdf') for year in (2027,2028)]
    out=folder/'stage39_print_qa.json';out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return results

if __name__=='__main__':
    print(json.dumps(export_pair(Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
