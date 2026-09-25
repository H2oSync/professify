(function(){
  if(!('ontouchstart' in window))return;

  /* Rate is not a stop. mtab-rate calls openRate(), a modal — swiping into it would leave you in
     a dialog you did not ask for, with no obvious way back out. Four views, in bar order. */
  var ORDER=['home','explore','sched','friends'];
  /* SCHEDULE'S THREE SUB-TABS ARE STOPS TOO — 2026-09-24.
     Tate (09-23): the header "where it says my classes, my watchlist, my planner … is a little bit
     hard to follow", and he asked for a slider. The four top tabs already swiped; the row that
     actually confused people did not. So the sequence is flattened rather than nested:

         Home · Explore · My classes · My watchlist · My planner · Friends

     One gesture, one rule, no mode to learn: a swipe always goes to the next thing to the side.
     A nested pager (sub-tabs swallow the swipe, top tabs only from the edge) was the other shape
     and it was rejected — it makes the same finger movement do two different things depending on
     how far along a row you are, which is the "swipe is arguing with you" feeling this engine was
     written to avoid. The tappable tabs stay the primary control; this rides on top of them. */
  var SCHED_SUB=['mine','watch','plan'];
  var AXIS_BIAS=1.4;        /* favour vertical: scrolling is by far the commoner gesture.
                               Sean's call: ship 1.4. Drop toward 1.15 if swipes feel ignored,
                               raise toward 1.6 if scrolling starts changing tabs. */
  var COMMIT=0.30;          /* fraction of the screen that counts as a decision */
  var FLICK=0.45;           /* ...or px/ms, so a fast short flick still commits */
  var DAMP=0.55;            /* finger-follow damping */
  var EDGE=28;              /* px from the left edge that means "back", not "next tab" */

  var x0=0,y0=0,t0=0,cur=null,axis=null,dragging=false,fromEdge=false,w=1,tgt=null;

  function activeView(){ return document.querySelector('.view.active'); }
  function curName(){ var v=activeView(); return v?String(v.id||'').replace(/^view-/,''):''; }
  function stops(){
    var out=[];
    ORDER.forEach(function(v){
      if(v==='sched')SCHED_SUB.forEach(function(t){ out.push({v:v,t:t}); });
      else out.push({v:v});
    });
    return out;
  }
  function subNow(){ var t=window.schedTab||'mine'; return t==='past'?'plan':t; }
  function stopIndex(){
    var v=curName(), S=stops();
    for(var i=0;i<S.length;i++){ if(S[i].v===v&&(!S[i].t||S[i].t===subNow()))return i; }
    return -1;
  }
  /* The element that moves under the finger. Between two Schedule sub-tabs only the pane moves —
     the title and the tab row stay put, so it reads as turning a page inside Schedule rather than
     leaving it. Anywhere else the whole view moves, exactly as before. */
  var PANE={mine:'schedMineWrap',watch:'schedWatchWrap',plan:'schedPlanWrap'};
  function neighbour(dx){ var S=stops(), i=stopIndex(); return (i<0)?null:(S[i+(dx<0?1:-1)]||null); }
  function targetFor(dx){
    var S=stops(), i=stopIndex(), n=neighbour(dx);
    if(i>=0&&n&&S[i].v==='sched'&&n.v==='sched'){
      var p=document.getElementById(PANE[S[i].t]); if(p){ p.classList.add('swp'); return p; }
    }
    return activeView();
  }

  /* A horizontally scrollable ancestor owns the gesture — pill rows, the compare tray, the
     friends strip. Without this, swiping a filter row would change tabs instead. */
  function inScroller(el){
    for(var n=el;n&&n!==document.body;n=n.parentElement){
      try{
        var cs=getComputedStyle(n);
        if(/(auto|scroll)/.test(cs.overflowX)&&n.scrollWidth>n.clientWidth+4)return true;
      }catch(e){}
    }
    return false;
  }
  /* Never fight a control or a text field, and never run while something is open on top. */
  function blocked(el){
    if(document.querySelector('.mback.open, .pq-back.open, .fp-back.open'))return true;
    try{ var ob=document.getElementById('onboard');
         if(ob&&ob.style.display!=='none'&&ob.getBoundingClientRect().height>0)return true; }catch(e){}
    for(var n=el;n&&n!==document.body;n=n.parentElement){
      var tag=(n.tagName||'').toLowerCase();
      if(tag==='input'||tag==='textarea'||tag==='select'||n.isContentEditable)return true;
    }
    return false;
  }

  function clearFx(v){ if(!v)return; v.classList.remove('sw-drag','sw-out','sw-in','from-left','from-right'); v.style.transform=''; v.style.opacity=''; }

  document.addEventListener('touchstart',function(e){
    if(e.touches.length!==1)return;
    var t=e.touches[0];
    if(blocked(e.target)||inScroller(e.target))return;
    if(stopIndex()<0)return;
    x0=t.clientX; y0=t.clientY; t0=Date.now();
    w=window.innerWidth||1;
    cur=activeView(); tgt=null; axis=null; dragging=false;
    fromEdge=(x0<=EDGE);
  },{passive:true});

  document.addEventListener('touchmove',function(e){
    if(!cur||e.touches.length!==1)return;
    var t=e.touches[0], dx=t.clientX-x0, dy=t.clientY-y0;
    if(axis===null){
      if(Math.abs(dx)<6&&Math.abs(dy)<6)return;
      /* One decision, once. Re-deciding mid-gesture is what makes a swipe feel like it is
         arguing with you. */
      axis=(Math.abs(dx)>Math.abs(dy)*AXIS_BIAS)?'x':'y';
      if(axis==='x')dragging=true;
    }
    if(axis!=='x')return;
    var i=stopIndex(), n=stops().length;
    /* No wrap-around, and no rubber band into nothing: at the ends the page simply does not
       move, which reads as "there is nothing there" without a bounce animation saying it. */
    if((dx<0&&i>=n-1)||(dx>0&&i<=0&&!fromEdge)){ if(tgt){ clearFx(tgt); tgt=null; } return; }
    /* The finger can reverse. Whatever it was dragging a moment ago goes back to rest before the
       other side's element starts to move — two elements half-slid at once is not a state. */
    var nt=(fromEdge&&dx>0)?activeView():targetFor(dx);
    if(nt!==tgt){ if(tgt)clearFx(tgt); tgt=nt; if(tgt)tgt.classList.add('sw-drag'); }
    if(e.cancelable)e.preventDefault();
    tgt.style.transform='translateX('+(dx*DAMP).toFixed(1)+'px)';
    tgt.style.opacity=String(Math.max(.45,1-Math.abs(dx)/w));
  },{passive:false});

  function finish(dx,dt){
    var v=tgt; cur=null; tgt=null;
    if(!v)return;
    var speed=Math.abs(dx)/Math.max(1,dt);
    var commit=(Math.abs(dx)>w*COMMIT)||speed>FLICK;
    v.classList.remove('sw-drag');
    if(!commit||!dragging){ clearFx(v); return; }

    /* An edge swipe from the left is BACK, not "previous tab" — and back goes through history,
       which already peels the top overlay first via navCloseTop(). No second close path. */
    if(fromEdge&&dx>0){
      clearFx(v);
      try{ history.back(); }catch(e){}
      return;
    }
    var S=stops(), i=stopIndex(), here=S[i], next=S[i+(dx<0?1:-1)];
    if(!here||!next){ clearFx(v); return; }
    var inPlace=(here.v==='sched'&&next.v==='sched');

    v.classList.add('sw-out');
    v.style.transform='translateX('+(dx<0?'-100%':'100%')+')';
    v.style.opacity='0';
    setTimeout(function(){
      clearFx(v);
      try{
        if(!inPlace&&typeof show==='function')show(next.v);
        /* Arriving in Schedule from the side lands on the sub-tab at THAT side — from Explore you
           meet My classes, from Friends you meet My planner. Tapping the Schedule tab is unchanged. */
        /* show('sched') already lands on My classes; only turn again if the target is elsewhere, so
           arriving from Explore renders Schedule once, not twice, in the middle of the transition. */
        if(next.t&&typeof setSchedTab==='function'&&subNow()!==next.t)setSchedTab(next.t);
      }catch(e){}
      var nv=inPlace?document.getElementById(PANE[next.t]):document.getElementById('view-'+next.v);
      if(nv){
        if(inPlace)nv.classList.add('swp');
        nv.classList.add('sw-in', dx<0?'from-right':'from-left');
        setTimeout(function(){ clearFx(nv); },240);
      }
    },170);
  }

  document.addEventListener('touchend',function(e){
    if(!cur)return;
    var t=(e.changedTouches&&e.changedTouches[0])||null;
    finish(t?(t.clientX-x0):0, Date.now()-t0);
    axis=null; dragging=false;
  },{passive:true});
  document.addEventListener('touchcancel',function(){ clearFx(tgt); cur=null; tgt=null; axis=null; dragging=false; },{passive:true});

  window.__swipeNav={ORDER:ORDER,SCHED_SUB:SCHED_SUB,stops:stops,stopIndex:stopIndex,AXIS_BIAS:AXIS_BIAS,COMMIT:COMMIT,FLICK:FLICK,EDGE:EDGE,
                     inScroller:inScroller,blocked:blocked};
})();