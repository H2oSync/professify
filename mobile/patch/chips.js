  /* THE MAP'S CHIPS (pass 2, 09-24): GEs · My major · Saved. "My major" is the list the default
     view already is — recommended for your major — so it is lit whenever nothing else is; with no
     major on file it says "All classes", which is what that list then is. Saved is a view of what
     you kept (window.exSaved). On the Professors side GEs has no meaning, so it is My major · Saved.
     Every chip reports its state in aria-pressed; the Classes | Professors switch does too. */
  var _maj=false; try{ _maj=!!(student&&student.major); }catch(e){}
  var _sv=!!window.exSaved;
  var _chip=function(on,label,act){ return '<button class="'+(on?'on':'')+'" aria-pressed="'+on+'" onclick="'+act+'">'+label+'</button>'; };
  if(exMode==='classes'||exMode==='ge'){
    el.innerHTML='<div class="ex-gesw" role="group" aria-label="Which classes">'
      +_chip(exMode==='ge'&&!_sv,'GEs',"setExMode('ge')")
      +_chip(exMode==='classes'&&!_sv,_maj?'My major':'All classes',"setExMode('classes')")
      +_chip(_sv,'Saved','exSetSaved(true)')
      +'</div>';
    return;
  }
  if(exMode==='professors'){
    el.innerHTML='<div class="ex-gesw" role="group" aria-label="Which professors">'
      +_chip(!_sv,_maj?'My major':'All professors',"setExMode('professors')")
      +_chip(_sv,'Saved','exSetSaved(true)')
      +'</div>';
    return;
  }
  el.innerHTML='';
