from pathlib import Path
p=Path(__file__).with_name('annual_engine.py')
s=p.read_text()
old="ax.text(tx,ty,name.replace('座',''),fontsize=11,ha='center',va='center',color=sign_text_palette[name],zorder=2)"
new="ax.text(tx,ty,name.replace('座',''),fontsize=11,ha='center',va='center',color='#20313C',zorder=2)"
assert old in s
p.write_text(s.replace(old,new,1))
print('updated zodiac sign glyph lettering to original reference dark ink; wedge fills unchanged')
