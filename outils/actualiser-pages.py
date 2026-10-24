from pathlib import Path
from html import escape, unescape
import json,re,hashlib

ROOT=Path(__file__).resolve().parent.parent
D=json.loads((ROOT/'outils/methodologie.json').read_text(encoding='utf8'))
FORMULATIONS=json.loads((ROOT/'outils/formulations-recherche.json').read_text(encoding='utf8'))
def p(text,cls=''):
    return '<p'+(' class="'+cls+'"' if cls else '')+' data-say="'+escape(text,quote=True)+'">'+escape(text)+'</p>'

for lang in ['fr','en','es','zh','ar','atj','iu','innu']:
    partial=lang in ['atj','iu','innu'];d=D['fr' if partial else lang]
    path=ROOT/('index.html' if lang=='fr' else lang+'/index.html')
    s=path.read_text(encoding='utf8')
    officiel=FORMULATIONS['fr' if partial else lang]
    s=re.sub(r'<title>[\s\S]*?</title>',lambda m:'<title>'+escape(officiel['titre'])+'</title>',s,count=1)
    s=re.sub(r'<h1\b[^>]*>[\s\S]*?</h1>',lambda m:'<h1'+(' lang="fr"' if partial else '')+'>'+escape(officiel['titre'])+'</h1>',s,count=1)
    prefixes={'fr':"Mon projet s'intitule : ",'en':'My project is entitled: ','es':'Mi proyecto se titula: ','zh':'研究题目：','ar':'عنوان المشروع: '}
    def titre_intro(m):
        contenu=unescape(re.sub('<[^>]+>','',m[0]))
        if re.match(r"^(?:Mon projet s|My project is entitled|Mi proyecto se titula|我的课题题目|研究题目|يحمل مشروعي عنوان|عنوان المشروع|Noreritamowin|ᖃᐅᔨᓴᕐᓂᕐᒪ ᐊᑎᖓ|Nitaieshkuenitamun ishinikateu|Titre de référence en français)",contenu):
            texte=prefixes.get(lang,'Titre de référence en français : ')+officiel['titre']
            return '<p'+(' lang="fr"' if partial else '')+' data-say="'+escape(texte,quote=True)+'">'+escape(texte)+'</p>'
        return m[0]
    s=re.sub(r'<p\b[^>]*>[\s\S]*?</p>',titre_intro,s)
    entetes={'fr':'Question et objectifs spécifiques','en':'Research question and specific objectives','es':'Pregunta y objetivos específicos','zh':'研究问题与具体目标','ar':'سؤال البحث والأهداف المحددة'}
    def objectif(t,i):
        if lang=='zh':return '<li><strong>O'+str(i+1)+'.</strong> '+escape(t)+'</li>'
        mot,sep,suite=t.partition(' ')
        return '<li><strong>O'+str(i+1)+'. '+escape(mot)+'</strong>'+sep+escape(suite)+'</li>'
    formulation='<section class="text" id="objectifs-recherche"'+(' lang="fr"' if partial else '')+'><h2>'+entetes.get(lang,entetes['fr']+' · français de référence')+'</h2>'+p(officiel['question'])+'<ol>'+''.join(objectif(t,i) for i,t in enumerate(officiel['objectifs']))+'</ol></section>'
    s=re.sub(r'<section class="text" id="objectifs-recherche"[^>]*>[\s\S]*?</section>',lambda m:formulation,s,count=1)
    s=re.sub(r'\sdata-version-methodologie="[^"]*"|\sdata-traduction="partielle"','',s)
    s=re.sub(r'(<html\b[^>]*)(>)',r'\1 data-version-methodologie="2026-10-21"\2',s,count=1)
    if partial:
        s=s.replace('data-version-methodologie="2026-10-21"','data-version-methodologie="2026-10-21" data-traduction="partielle"')
    def replace_section(key,body):
        global s
        actual={'contexte':'context','methodes':'methods','resultats':'results'}.get(key,key) if lang=='en' else key
        pattern=r'<section class="text" id="'+actual+r'"[^>]*>[\s\S]*?</section>'
        m=re.search(pattern,s)
        if not m:raise ValueError((lang,key))
        heading=re.search(r'<h2\b[\s\S]*?</h2>',m[0])[0]
        if partial:heading={'contexte':'<h2 id="h-contexte">1. Contexte · français de référence</h2>','methodes':'<h2 id="h-methodes">2. Méthodes · français de référence</h2>','resultats':'<h2 id="h-resultats">3. Produits attendus · français de référence</h2>','impacts':'<h2 id="h-impacts">4. Retombées visées · français de référence</h2>'}[key]
        result='<section class="text" id="'+actual+'" aria-labelledby="h-'+actual+'"'+(' lang="fr"' if partial else '')+'>'+heading+body+'</section>'
        s=s[:m.start()]+result+s[m.end():]
    replace_section('contexte',p(d['population'])+p(d['caseText'])+p(d['question']))
    methodo_labels={'fr':'Objectif méthodologique','en':'Methodological objective','es':'Objetivo metodológico','zh':'方法目标','ar':'الهدف المنهجي'}
    cards='<div class="methodes-cartes">'+''.join('<article><h3>'+escape(methodo_labels.get(lang,methodo_labels['fr'])+' '+str(i+1))+'</h3>'+p(officiel['methodologiques'][i],'methodo-formulation-officielle')+p(c['metric'],'methode-repere')+'<details><summary>'+escape({'fr':'Précisions du protocole','en':'Protocol details','es':'Detalles del protocolo','zh':'方案详情','ar':'تفاصيل البروتوكول'}.get(lang,'Précisions du protocole'))+'</summary><ol>'+''.join('<li data-say="'+escape(step,quote=True)+'">'+escape(step)+'</li>' for step in c['steps'])+'</ol></details></article>' for i,c in enumerate(d['cards']))+'</div>'
    biblio='<details class="sources-ars"><summary>'+escape({'fr':'Références méthodologiques · APA','en':'Methodological references · APA','es':'Referencias metodológicas · APA','zh':'方法参考文献 · APA','ar':'المراجع المنهجية · APA'}.get(lang,'Références méthodologiques · APA'))+'</summary><p>Brewster, A. L., Tan, A. X., &amp; Yuan, C. T. (2019). Development and application of a survey instrument to measure collaboration among health care and social services organizations. <i>Health Services Research, 54</i>(6), 1246–1254. <a href="https://doi.org/10.1111/1475-6773.13206">https://doi.org/10.1111/1475-6773.13206</a></p><p>Agency for Healthcare Research and Quality. (2014). Chapter 4: Emerging trends in care coordination measurement. In <i>Care coordination measures atlas update</i>. <a href="https://www.ahrq.gov/ncepcr/care/coordination/atlas/chapter4.html">AHRQ</a></p></details>'
    body=(p(d['partial'],'prelim') if partial else '')+p(d['status'],'statut-protocole')+cards+p(d['integration'])+p(d['warning'],'prelim')+biblio
    replace_section('methodes',body)
    replace_section('resultats',p(d['results'])+'<ol>'+''.join('<li data-say="'+escape(c['product'],quote=True)+'">'+escape(c['product'])+'</li>' for c in d['cards'])+'</ol>'+p(d['warning']))
    replace_section('impacts',p(d['impactText'])+p(d['integration']))
    # Ne pas proposer un ancien enregistrement pour un texte révisé.
    m=re.search(r'<section class="listen"[\s\S]*?</section>',s)
    if m:
        text=m[0]
        text=re.sub(r'<ol>[\s\S]*?</ol>','',text)
        notices={'fr':'Écoutez le texte actualisé avec la voix de votre appareil. Les anciennes pistes ne sont pas utilisées pour cette révision.','en':'Listen to the updated text with your device voice. Earlier recordings are not used for this revision.','es':'Escuche el texto actualizado con la voz de su dispositivo. Esta revisión no utiliza las grabaciones anteriores.','zh':'使用设备语音收听更新后的文本。本次修订不使用旧录音。','ar':'استمع إلى النص المحدّث بصوت جهازك. لا تُستخدم التسجيلات السابقة في هذه المراجعة.'}
        text=re.sub(r'(<h2[^>]*>[\s\S]*?</h2>)<p>[\s\S]*?</p>',lambda x:x[1]+p(notices.get(lang,notices['fr'])),text,count=1)
        s=s[:m.start()]+text+s[m.end():]
    path.write_text(s,encoding='utf8')

# Version simple : quatre gestes, même protocole, sans annoncer un bénéfice acquis.
path=ROOT/'falc/index.html';s=path.read_text(encoding='utf8')
steps=[
 'Je lis les recherches pour repérer les besoins qui existent ensemble chez les mêmes personnes. Je construis des exemples seulement si les études les permettent. Les appels au 211 ne prouvent pas les besoins d’une même personne.',
 'Je fais des cartes des services et de leur accès. Les huit quartiers montrés sont un exemple. Les lieux de l’étude ne sont pas encore choisis.',
 'Avec les équipes de soutien à domicile, j’étudie des situations réelles des douze derniers mois. Je garde aussi les situations sans contact avec un autre groupe. Je distingue un contact, un travail ensemble et une aide reçue.',
 'Je parle avec les intervenants pour comprendre les cartes de relations. Je demande aussi ce qui manque et ce que l’on ne sait pas. Les autorisations sont nécessaires avant de commencer.'
]
m=re.search(r'<ol class="etapes">[\s\S]*?</ol>',s)
if not m:raise ValueError('FALC')
it=iter(steps)
body=re.sub(r'<p\b[^>]*>[\s\S]*?</p>',lambda m:p(next(it)),m[0])
s=s[:m.start()]+body+s[m.end():]
s=s.replace('Les personnes âgées vont recevoir une aide qui répond à tous leurs besoins, près de chez elles.','Cette recherche pourra aider à réfléchir à des services mieux adaptés. Elle ne garantit pas que tous les besoins seront résolus.')
s=s.replace('Le chemin de l&#x27;aide : qui aide en premier, qui aide ensuite, qui manque.','Des cartes des relations entre les groupes, et des explications sur la façon de travailler ensemble.')
path.write_text(s,encoding='utf8')

# Versions de cache calculées pour toutes les représentations : image, PDF, zoom et ressources.
v=FORMULATIONS['fr'];path=ROOT/'falc/index.html';s=path.read_text(encoding='utf8')
annexe='<details id="cadrage-scientifique-exact"><summary>Formulations scientifiques exactes</summary><h2>Titre provisoire</h2>'+p(v['titre'])+'<h3>Question de recherche</h3>'+p(v['question'])+'<h3>Objectifs spécifiques</h3><ol>'+''.join('<li>'+escape(t)+'</li>' for t in v['objectifs'])+'</ol><h3>Objectifs méthodologiques</h3><ol>'+''.join('<li>'+escape(t)+'</li>' for t in v['methodologiques'])+'</ol></details>'
s=re.sub(r'<details id="cadrage-scientifique-exact">[\s\S]*?</details>',lambda m:annexe,s) if 'id="cadrage-scientifique-exact"' in s else s.replace('</main>',annexe+'</main>')
path.write_text(s,encoding='utf8')
for path in ROOT.rglob('*.html'):
    s=path.read_text(encoding='utf8')
    def version(m):
        value=unescape(m[2]);base=value.split('?')[0]
        if re.match(r'^(?:https?:|mailto:|#)',base):return m[0]
        target=(path.parent/base).resolve()
        if target.suffix.lower() not in ['.png','.pdf','.js','.css'] or not target.is_file():return m[0]
        digest=hashlib.sha256(target.read_bytes()).hexdigest()[:10]
        return m[1]+'="'+escape(base+'?v='+digest,quote=True)+'"'
    s=re.sub(r'\b(src|href|data-std|data-cb)="([^"]+)"',version,s)
    path.write_text(s,encoding='utf8')
