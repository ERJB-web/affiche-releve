(function(){
  var root = document.documentElement, lang = root.lang;
  function load(k, d){ try { var v = localStorage.getItem(k); return v === null ? d : v; } catch(e){ return d; } }
  function save(k, v){ try { localStorage.setItem(k, v); } catch(e){} }

  // taille du texte et contraste
  var size = parseInt(load("affiche-taille", "0"), 10) || 0;
  function applySize(){ root.classList.remove("t1","t2","t3"); if(size>0) root.classList.add("t"+size); }
  applySize();
  document.getElementById("plus").onclick = function(){ size = Math.min(3, size+1); applySize(); save("affiche-taille", size); };
  document.getElementById("moins").onclick = function(){ size = Math.max(0, size-1); applySize(); save("affiche-taille", size); };
  var cbtn = document.getElementById("contraste");
  function applyContrast(on){ root.classList.toggle("contrast", on); cbtn.setAttribute("aria-pressed", on ? "true" : "false"); }
  applyContrast(load("affiche-contraste", "0") === "1");
  cbtn.onclick = function(){ var on = !root.classList.contains("contrast"); applyContrast(on); save("affiche-contraste", on ? "1" : "0"); };

  // version de l'affiche
  var img = document.getElementById("affiche"), big = document.getElementById("grand"), pdf = document.getElementById("pdf");
  var vb = document.querySelectorAll("[data-version]");
  function applyVersion(v){
    for (var i=0;i<vb.length;i++){ vb[i].setAttribute("aria-pressed", vb[i].getAttribute("data-version")===v ? "true":"false"); }
    var b = vb[0].parentNode.querySelector('[data-version="'+v+'"]') || vb[0];
    img.src = b.getAttribute("data-img"); img.alt = b.getAttribute("data-alt");
    big.href = b.getAttribute("data-img"); pdf.href = b.getAttribute("data-pdf");
  }
  var start = load("affiche-version", "standard");
  if (location.hash === "#daltonien" || location.hash === "#colour-blind") start = "cb";
  applyVersion(start);
  for (var i=0;i<vb.length;i++){ vb[i].onclick = function(){ var v=this.getAttribute("data-version"); applyVersion(v); save("affiche-version", v); }; }

  // pistes audio enregistrées par l'auteur (mp3 ou m4a)
  var tracks = document.querySelectorAll("[data-track]"), found = 0, pending = tracks.length;
  function done(){ pending--; if(pending===0 && found===0){ document.getElementById("tts-note").classList.remove("hidden"); } }
  function probe(el, exts){
    if(!exts.length){ done(); return; }
    var src = el.getAttribute("data-track") + exts[0];
    fetch(src, {method:"HEAD"}).then(function(r){
      if(r.ok){ var a=document.createElement("audio"); a.controls=true; a.preload="none"; a.src=src; el.appendChild(a); found++; el.classList.remove("hidden"); done(); }
      else probe(el, exts.slice(1));
    }).catch(function(){ probe(el, exts.slice(1)); });
  }
  for (var t=0;t<tracks.length;t++){ probe(tracks[t], [".mp3", ".m4a"]); }

  // lecture par la voix de l'appareil (secours)
  var synth = window.speechSynthesis, stopBtn = document.getElementById("stop");
  if(!synth){ var tb=document.querySelectorAll(".tts"); for(var k=0;k<tb.length;k++) tb[k].classList.add("hidden"); return; }
  function bestVoice(){
    var vs = synth.getVoices().filter(function(v){ return v.lang && v.lang.toLowerCase().indexOf(lang)===0; });
    function score(v){ var n=v.name; return (/natural|neural|online/i.test(n)?4:0)+(/premium|enhanced|siri/i.test(n)?3:0)+(/google/i.test(n)?2:0)+(/ca/i.test(v.lang)&&lang==="fr"?1:0); }
    vs.sort(function(a,b){ return score(b)-score(a); });
    return vs[0] || null;
  }
  function speak(texts){
    synth.cancel();
    var v = bestVoice();
    texts.forEach(function(tx){ var u=new SpeechSynthesisUtterance(tx); u.lang = lang==="fr" ? "fr-CA" : "en-CA"; if(v){ u.voice=v; u.lang=v.lang; } u.rate=0.95; synth.speak(u); });
    stopBtn.classList.remove("hidden");
  }
  stopBtn.onclick = function(){ synth.cancel(); stopBtn.classList.add("hidden"); };
  function paras(sec){ var ps=sec.querySelectorAll("p[data-say]"), out=[]; for(var i=0;i<ps.length;i++) out.push(ps[i].getAttribute("data-say")); return out; }
  var sb = document.querySelectorAll("[data-speak]");
  for (var s=0;s<sb.length;s++){
    sb[s].onclick = function(){
      var id=this.getAttribute("data-speak");
      if(id==="all"){ var all=[], secs=document.querySelectorAll("section.text"); for(var j=0;j<secs.length;j++) all=all.concat(paras(secs[j])); speak(all); }
      else speak(paras(document.getElementById(id)));
    };
  }
  if (synth.onvoiceschanged !== undefined) synth.onvoiceschanged = function(){};
})();
