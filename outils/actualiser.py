"""Affiches PDF vectorielles et dérivés, à partir de la version publiée conservée dans Git.
Les régions non concernées (auteur, logos et contexte) sont préservées.
Usage : python outils/actualiser.py
"""
from pathlib import Path
from io import BytesIO
import json, subprocess, html, re
import pymupdf as fitz
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT/'outils/methodologie.json').read_text(encoding='utf8'))
FORMULATIONS = json.loads((ROOT/'outils/formulations-recherche.json').read_text(encoding='utf8'))
BASE = '78413578f3f33488be46114be596bc4ffb053236'
LANGS = ['fr','en','es','zh','ar','atj','iu','innu']
pdfmetrics.registerFont(TTFont('Arial','C:/Windows/Fonts/arial.ttf'))
pdfmetrics.registerFont(TTFont('ArialB','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('CJK','C:/Windows/Fonts/simsun.ttc', subfontIndex=0))

def clean(s):
    return s.replace('–','-').replace('‑','-').replace('\u00a0',' ')

def update_pdf(lang, cb):
    partial = lang in ['atj','iu','innu']
    d = DATA['fr' if partial else lang]
    name = 'affiche-'+lang+('-daltonien' if cb else '')
    raw = subprocess.check_output(['git','show',f'{BASE}:pdf/{name}.pdf'],cwd=ROOT)
    doc = fitz.open(stream=raw,filetype='pdf')
    page = doc[0]
    scale = page.rect.width/2400
    # Suppression réelle du texte/graphisme remplacé : pas de texte périmé caché sous un cache blanc.
    regions = [(60,155,2340,425),(1600,560,2399,1328),(0,1328,2400,2400)]
    for r in regions:
        page.add_redact_annot(fitz.Rect(*(v*scale for v in r)),fill=(1,1,1))
    page.apply_redactions(images=2,graphics=2,text=0)
    # Harmoniser la population, sans conserver les anciens critères sociaux seuls.
    for r in [(200,905,740,1030),(200,1048,740,1176)]:
        page.add_redact_annot(fitz.Rect(*(v*scale for v in r)),fill=(.955,.971,.98))
    page.apply_redactions(images=2,graphics=0,text=0)
    for link in page.get_links():
        if any(link['from'].intersects(fitz.Rect(*(v*scale for v in r))) for r in regions):
            page.delete_link(link)
    stream=BytesIO()
    c=canvas.Canvas(stream,pagesize=(page.rect.width,page.rect.height))
    c.scale(scale,scale)
    colors = ['#286C23','#006E72','#18559B'] if not cb else ['#075D94','#9A4C00','#65459A']
    ink='#123C4D';muted='#42616D';line='#D9E4E8'
    font='CJK' if lang=='zh' else 'Arial'
    bold='CJK' if lang=='zh' else 'ArialB'

    def rect(x,y,w,h,fill,stroke=None,radius=12):
        c.setFillColor(HexColor(fill));c.setStrokeColor(HexColor(stroke or fill))
        c.roundRect(x,2400-y-h,w,h,radius,fill=1,stroke=bool(stroke))

    def para(text,x,y,w,size=21,color=ink,strong=False,limit=None,verb=False):
        text=clean(text)
        f=bold if strong else font
        if lang=='ar' and not partial:
            lines=[];row=''
            for word in text.split():
                trial=(row+' '+word).strip()
                if pdfmetrics.stringWidth(get_display(arabic_reshaper.reshape(trial)),f,size)>w and row:
                    lines.append(row);row=word
                else:row=trial
            if row:lines.append(row)
            h=len(lines)*size*1.35
            if limit is not None and h>limit:raise ValueError((name,text[:40],h,limit))
            c.setFont(f,size);c.setFillColor(HexColor(color))
            for i,row in enumerate(lines):c.drawRightString(x+w,2400-y-size-i*size*1.35,get_display(arabic_reshaper.reshape(row)))
            return h
        style=ParagraphStyle('p',fontName=f,fontSize=size,leading=size*1.32,textColor=HexColor(color),wordWrap='CJK' if lang=='zh' else 'LTR',spaceAfter=0)
        markup=html.escape(text).replace(' ?', '&#160;?').replace(' :', '&#160;:')
        if verb and lang!='zh':markup=re.sub(r'^(\S+)',lambda m:'<font name="'+bold+'">'+m[0]+'</font>',markup,count=1)
        p=Paragraph(markup,style)
        _,h=p.wrap(w,3000)
        if limit is not None and h>limit:raise ValueError((name,text[:40],h,limit))
        p.drawOn(c,x,2400-y-h)
        return h

    # Titre et objectifs spécifiques approuvés ; les intitulés de méthode restent inchangés.
    officiel=FORMULATIONS['fr' if partial else lang]
    para(officiel['titre'],70,172,2260,52,ink,True,limit=248)
    contexte=d['contextNeeds']
    para(contexte[0],210,920,520,22,ink,True,limit=40)
    para(contexte[1],210,962,520,19,ink,limit=62)
    para(contexte[2],210,1060,520,21,ink,True,limit=55)
    para(d['contextPopulation'],210,1110,520,15.5,ink,limit=62)
    # Question et formulations complètes, dans la colonne existante.
    x=1615;w=715
    rect(x,577,w,192,ink)
    para(officiel['question'],x+20,595,w-40,25,'#FFFFFF',True,limit=162)
    for i in range(3):
        y=783+i*176
        rect(x,y,w,168,'#F1F6F8',line)
        para('O'+str(i+1),x+16,y+9,w-32,21,colors[i],True)
        para(officiel['objectifs'][i],x+16,y+40,w-32,17.5,ink,limit=122,verb=True)

    para(d['methods'],70,1350,2260,38,ink,True)
    para(d['status'],70,1400,2260,19,colors[1],True)
    para(d['partial'] if partial else d['population'],70,1432,2260,21,muted,limit=57)
    cw=730;xs=([1600,835,70] if lang=='ar' else [70,835,1600]);top=1505;bottom=2045
    titres_methodes={'fr':'Objectif méthodologique','en':'Methodological objective','es':'Objetivo metodológico','zh':'方法目标','ar':'الهدف المنهجي'}
    for i,card in enumerate(d['cards']):
        x=xs[i];col=colors[i]
        rect(x,top,cw,bottom-top,'#F4F8FA',line)
        rect(x,top,cw,7,col,radius=0)
        h=para(titres_methodes.get(lang,titres_methodes['fr'])+' O'+str(i+1),x+22,top+23,cw-44,25,col,True,limit=75)
        y=top+28+h
        h=para(officiel['methodologiques'][i],x+22,y,cw-44,20,ink,limit=235);y+=h+15
        h=para(card['metric'],x+22,y,cw-44,18,ink,True,limit=60);y+=h+15
        for step in card['steps']:
            rect(x+22,y+8,6,6,col,radius=2)
            h=para(step,x+40,y,cw-66,17.5,ink)
            y+=h+10
        if y>bottom-14:raise ValueError((name,'card overflow',i,y,bottom))
    rect(70,2060,2260,84,'#EAF3F5')
    para(d['integration'],88,2076,2224,22,ink,limit=61)
    para(d['results'],70,2160,2260,30,ink,True,limit=42)
    for i,card in enumerate(d['cards']):
        rect(xs[i],2206,cw,72,'#FFFFFF',colors[i])
        para(card['product'],xs[i]+17,2221,cw-34,24,colors[i],True,limit=54)
    para(d['impact'],70,2294,600,24,ink,True)
    para(d['impactText'],690,2293,1500,20,ink,limit=55)
    para(d['warning'],70,2352,2140,17,muted,limit=25)
    para(d['source'],70,2380,2130,14,muted,limit=24)
    # Code QR et lien cliquable vers le protocole qui fait foi.
    q=qr.QrCodeWidget(DATA['reference']);bounds=q.getBounds();sz=94
    drawing=Drawing(sz,sz,transform=[sz/(bounds[2]-bounds[0]),0,0,sz/(bounds[3]-bounds[1]),0,0]);drawing.add(q)
    renderPDF.draw(drawing,c,2240,2)
    c.linkURL(DATA['reference'],(70,0,2325,62),relative=0,thickness=0)
    c.showPage();c.save()
    overlay=fitz.open(stream=stream.getvalue(),filetype='pdf')
    page.show_pdf_page(page.rect,overlay,0)
    doc.set_metadata({'title':officiel['titre'],'author':'Éric Bernier','subject':officiel['question'],'keywords':'Objectifs spécifiques O1 O2 O3 · formulations approuvées le 21 octobre 2026'})
    dest=ROOT/'pdf'/f'{name}.pdf'
    doc.save(dest,garbage=4,deflate=True)
    # Images publiées et vues basse vision sont toutes dérivées du même PDF actualisé.
    page.get_pixmap(matrix=fitz.Matrix(2400/page.rect.width,2400/page.rect.height),alpha=False).save(ROOT/'img'/f'{name}.png')
    tiles=[(0,0,2400,550),(0,550,800,1328),(800,550,1600,1328),(1600,550,2400,1328),(0,1328,1600,2060),(1600,1328,2400,2060),(0,2060,2400,2285),(0,2285,2400,2400)]
    for n,r in enumerate(tiles,1):
        page.get_pixmap(matrix=fitz.Matrix(1/scale,1/scale),clip=fitz.Rect(*(v*scale for v in r)),alpha=False).save(ROOT/'img/zoom'/(lang+('-daltonien' if cb else '')+f'-{n}.png'))
    doc.close()
    print(name, 'PDF + PNG + 8 vues')

if __name__=='__main__':
    for lang in (__import__('sys').argv[1:] or LANGS):
        for cb in [False,True]:update_pdf(lang,cb)
