(function(){
  var root = document.documentElement, ttsLang = root.getAttribute("data-tts") || "";
  function load(k, d){ try { var v = localStorage.getItem(k); return v === null ? d : v; } catch(e){ return d; } }
  function save(k, v){ try { localStorage.setItem(k, v); } catch(e){} }
  function $(id){ return document.getElementById(id); }

  // taille du texte et contraste
  var size = parseInt(load("affiche-taille", "0"), 10) || 0;
  function applySize(){ root.classList.remove("t1","t2","t3"); if(size>0) root.classList.add("t"+size); }
  applySize();
  if ($("plus")) $("plus").onclick = function(){ size = Math.min(3, size+1); applySize(); save("affiche-taille", size); };
  if ($("moins")) $("moins").onclick = function(){ size = Math.max(0, size-1); applySize(); save("affiche-taille", size); };
  function toggle(id, cls, key, on){
    var b = $(id); if(!b) return;
    function apply(v){ root.classList.toggle(cls, v); b.setAttribute("aria-pressed", v ? "true" : "false"); if(id==="daltonisme") swap(v); }
    apply(on);
    b.onclick = function(){ var v = !root.classList.contains(cls); apply(v); save(key, v ? "1" : "0"); };
  }
  // version adaptée au daltonisme : images et PDF
  function swap(cb){
    var els = document.querySelectorAll("[data-std]");
    for (var i=0;i<els.length;i++){
      var el = els[i], v = el.getAttribute(cb ? "data-cb" : "data-std");
      if (el.tagName === "IMG") el.src = v; else el.href = v;
      if (el.hasAttribute("data-alt-cb")) el.alt = el.getAttribute(cb ? "data-alt-cb" : "data-alt-std");
    }
  }
  var h = location.hash;
  toggle("contraste", "contrast", "affiche-contraste", load("affiche-contraste", "0") === "1");
  toggle("daltonisme", "cb", "affiche-daltonisme", h === "#daltonien" || h === "#colour-blind" || load("affiche-daltonisme", "0") === "1");
  toggle("bassevision", "lv", "affiche-bassevision", h === "#basse-vision" || h === "#low-vision" || load("affiche-bassevision", "0") === "1");

  // pistes audio enregistrées par l'auteur (mp3 ou m4a)
  var tracks = document.querySelectorAll("[data-track]"), found = 0, pending = tracks.length;
  function done(){ pending--; if(pending===0 && found===0 && $("tts-note")){ $("tts-note").classList.remove("hidden"); } }
  function probe(el, exts){
    if(!exts.length){ done(); return; }
    var src = el.getAttribute("data-track") + exts[0];
    fetch(src, {method:"HEAD"}).then(function(r){
      if(r.ok){ var a=document.createElement("audio"); a.controls=true; a.preload="none"; a.src=src; el.appendChild(a); found++; el.classList.remove("hidden"); done(); }
      else probe(el, exts.slice(1));
    }).catch(function(){ probe(el, exts.slice(1)); });
  }
  for (var t=0;t<tracks.length;t++){ probe(tracks[t], [".mp3", ".m4a", ".webm"]); }

  // lecture par la voix de l'appareil
  var synth = window.speechSynthesis, stopBtn = $("stop");
  var base = ttsLang.slice(0,2).toLowerCase();
  function voices(){ return synth ? synth.getVoices().filter(function(v){ return v.lang && v.lang.toLowerCase().replace("_","-").indexOf(base)===0; }) : []; }
  function hideTts(){ var tb=document.querySelectorAll(".tts"); for(var k=0;k<tb.length;k++) tb[k].classList.add("hidden"); if($("no-voice")) $("no-voice").classList.remove("hidden"); }
  if(!synth || !ttsLang){ hideTts(); return; }
  function bestVoice(){
    var vs = voices();
    function score(v){ var n=v.name; return (/natural|neural|online/i.test(n)?4:0)+(/premium|enhanced|siri/i.test(n)?3:0)+(/google/i.test(n)?2:0)+(v.lang.toLowerCase().indexOf(ttsLang.toLowerCase())===0?1:0); }
    vs.sort(function(a,b){ return score(b)-score(a); });
    return vs[0] || null;
  }
  // langue sans voix installée sur l'appareil : on le dit au lieu de lire avec une autre langue
  setTimeout(function(){ if(base!=="fr" && base!=="en" && synth.getVoices().length && !voices().length) hideTts(); }, 1500);
  function speak(texts){
    synth.cancel();
    var v = bestVoice();
    texts.forEach(function(tx){ var u=new SpeechSynthesisUtterance(tx); u.lang = ttsLang; if(v){ u.voice=v; u.lang=v.lang; } u.rate=0.95; synth.speak(u); });
    if(stopBtn) stopBtn.classList.remove("hidden");
  }
  if(stopBtn) stopBtn.onclick = function(){ synth.cancel(); stopBtn.classList.add("hidden"); };
  function paras(sec){ var ps=sec.querySelectorAll("[data-say]"), out=[]; for(var i=0;i<ps.length;i++) out.push(ps[i].getAttribute("data-say")); return out; }
  var sb = document.querySelectorAll("[data-speak]");
  for (var s=0;s<sb.length;s++){
    sb[s].onclick = function(){
      var id=this.getAttribute("data-speak");
      if(id==="all"){ var all=[], secs=document.querySelectorAll(".text"); for(var j=0;j<secs.length;j++) all=all.concat(paras(secs[j])); speak(all); }
      else speak(paras($(id)));
    };
  }
  if (synth.onvoiceschanged !== undefined) synth.onvoiceschanged = function(){};
})();
