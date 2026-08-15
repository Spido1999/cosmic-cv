"""
app.py - COSMIC CV  |  Universe AI Resume Builder
Powered by DeepSeek V4 Pro  |  ATS-Optimised Resumes
"""
import os, re, json, datetime, hashlib
import streamlit as st

st.set_page_config(
    page_title="COSMIC CV - AI Resume Builder",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded",
)

from dotenv import load_dotenv
load_dotenv()
from config import ATS_PASS_SCORE, ATS_TARGET_SCORE, OUTPUT_DIR, PROVIDER_MODELS

# ===========================================================================
# 1. SPACE UNIVERSE BACKGROUND  (canvas + planets + nebulas + parallax JS)
# ===========================================================================
SPACE_BG = """
<style>
/* ---- transparent streamlit shell ---- */
[data-testid="stApp"],[data-testid="stAppViewContainer"],[data-testid="stHeader"],
[data-testid="stDecoration"],.stApp,.main { background:transparent !important; }
body,html { background:#030610 !important; }

/* ---- full-screen canvas ---- */
#cosmic-cv { position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:-30;pointer-events:none; }

/* ---- nebulas ---- */
.csm-neb { position:fixed;border-radius:50%;pointer-events:none;filter:blur(80px);z-index:-25; }
.nb1 { width:660px;height:660px;
       background:radial-gradient(circle,rgba(108,28,198,0.24),transparent 68%);
       top:calc(-10% + var(--py,0px));left:-8%;
       animation:nb1d 34s ease-in-out infinite; }
.nb2 { width:780px;height:560px;
       background:radial-gradient(circle,rgba(14,68,200,0.19),transparent 68%);
       top:calc(28% + var(--py,0px));right:-14%;
       animation:nb2d 44s ease-in-out infinite; }
.nb3 { width:520px;height:520px;
       background:radial-gradient(circle,rgba(0,168,200,0.13),transparent 68%);
       top:calc(62% + var(--py,0px));left:7%;
       animation:nb3d 38s ease-in-out infinite; }
.nb4 { width:400px;height:300px;
       background:radial-gradient(circle,rgba(180,40,120,0.10),transparent 68%);
       top:calc(40% + var(--py,0px));left:35%;
       animation:nb4d 50s ease-in-out infinite; }
@keyframes nb1d{0%,100%{transform:translate(0,0)scale(1)}40%{transform:translate(48px,36px)scale(1.1)}80%{transform:translate(-26px,58px)scale(0.93)}}
@keyframes nb2d{0%,100%{transform:translate(0,0)}50%{transform:translate(-58px,-38px)scale(1.13)}}
@keyframes nb3d{0%,100%{transform:translate(0,0)scale(1)}33%{transform:translate(36px,-24px)scale(1.08)}66%{transform:translate(-30px,20px)scale(0.94)}}
@keyframes nb4d{0%,100%{transform:translate(0,0)scale(1)}50%{transform:translate(20px,-40px)scale(1.12)}}

/* ---- galaxy spirals ---- */
.csm-gal { position:fixed;border-radius:50%;pointer-events:none;z-index:-22; }
.gl1 { width:440px;height:440px;
       background:conic-gradient(from 0deg,transparent 12%,rgba(88,28,220,0.09)28%,transparent 44%,rgba(28,88,220,0.07)60%,transparent 74%,rgba(68,28,180,0.06)86%,transparent);
       filter:blur(20px);top:calc(2% + var(--py,0px));right:2%;
       animation:gspin 95s linear infinite; }
.gl2 { width:320px;height:320px;
       background:conic-gradient(from 130deg,transparent 14%,rgba(36,188,220,0.07)30%,transparent 50%,rgba(88,48,200,0.06)70%,transparent);
       filter:blur(15px);top:calc(48% + var(--py,0px));left:0%;
       animation:gspin 68s linear infinite reverse; }
.gl3 { width:200px;height:200px;
       background:conic-gradient(from 60deg,transparent 18%,rgba(200,80,180,0.05)35%,transparent 55%,rgba(80,200,160,0.04)72%,transparent);
       filter:blur(12px);top:calc(75% + var(--py,0px));right:28%;
       animation:gspin 50s linear infinite; }
@keyframes gspin{from{transform:rotate(0)}to{transform:rotate(360deg)}}

/* ---- PLANETS ---- */
/* Jupiter - gas giant top-right */
.pl-jup {
  position:fixed;width:118px;height:118px;border-radius:50%;pointer-events:none;z-index:-10;
  top:calc(7% + var(--py,0px));right:6%;
  background:repeating-linear-gradient(0deg,#c8844a 0px,#e09060 8px,#b06030 16px,#d08050 24px,#a86028 32px,#c87040 40px);
  box-shadow:-18px -14px 30px rgba(0,0,0,0.55) inset,0 0 42px rgba(200,120,60,0.22),0 0 80px rgba(200,100,40,0.08);
  animation:pfl1 13s ease-in-out infinite; }
.pl-jup::after {
  content:"";position:absolute;width:140%;height:22%;border-radius:50%;
  background:rgba(148,76,28,0.35);top:36%;left:-20%;filter:blur(4px); }

/* Saturn with ring */
.pl-sat-w {
  position:fixed;z-index:-10;pointer-events:none;
  top:calc(52% + var(--py,0px));right:1%;
  animation:pfl2 16s ease-in-out infinite; }
.pl-sat {
  width:80px;height:80px;border-radius:50%;
  background:radial-gradient(circle at 34% 32%,#f5e07a,#c8a020,#7a5c00);
  box-shadow:-12px -10px 22px rgba(0,0,0,0.55) inset,0 0 30px rgba(240,200,60,0.25); }
.pl-sat-r {
  position:absolute;width:158px;height:32px;
  border:9px solid rgba(212,170,32,0.42);border-radius:50%;
  top:24px;left:-39px;transform:rotateX(74deg);
  box-shadow:0 0 14px rgba(212,170,32,0.18); }

/* Earth */
.pl-ear {
  position:fixed;width:70px;height:70px;border-radius:50%;pointer-events:none;z-index:-10;
  top:calc(72% + var(--py,0px));right:15%;
  background:radial-gradient(circle at 38% 36%,#6bc5f8,#1a70c2,#0a3d7c);
  box-shadow:-10px -8px 18px rgba(0,0,0,0.55) inset,0 0 24px rgba(60,168,248,0.32);
  animation:pfl3 11s ease-in-out infinite; }
.pl-ear::before {
  content:"";position:absolute;width:54%;height:34%;border-radius:35%;
  background:rgba(36,180,80,0.68);top:26%;left:18%;filter:blur(2px); }
.pl-ear::after {
  content:"";position:absolute;width:74%;height:20%;border-radius:50%;
  background:rgba(255,255,255,0.14);top:8%;left:10%;filter:blur(3px); }

/* Mars */
.pl-mar {
  position:fixed;width:46px;height:46px;border-radius:50%;pointer-events:none;z-index:-10;
  top:calc(37% + var(--py,0px));left:3%;
  background:radial-gradient(circle at 37% 35%,#e87252,#b84022,#7a2012);
  box-shadow:-6px -5px 12px rgba(0,0,0,0.55) inset,0 0 18px rgba(220,80,42,0.28);
  animation:pfl4 9s ease-in-out infinite; }

/* Moon orbiting earth area */
.pl-moon {
  position:fixed;width:26px;height:26px;border-radius:50%;pointer-events:none;z-index:-10;
  top:calc(46% + var(--py,0px));left:6%;
  background:radial-gradient(circle at 36% 34%,#cacac6,#8c8c88,#585854);
  box-shadow:-4px -3px 9px rgba(0,0,0,0.62) inset;
  animation:pfl5 7s ease-in-out infinite; }

/* Ice planet */
.pl-ice {
  position:fixed;width:52px;height:52px;border-radius:50%;pointer-events:none;z-index:-10;
  top:calc(18% + var(--py,0px));left:8%;
  background:radial-gradient(circle at 36% 34%,#90d8f0,#3090c0,#104878);
  box-shadow:-7px -6px 13px rgba(0,0,0,0.55) inset,0 0 20px rgba(80,180,240,0.28);
  animation:pfl6 14s ease-in-out infinite; }

/* Tiny distant worlds */
.pl-d1 {
  position:fixed;width:14px;height:14px;border-radius:50%;pointer-events:none;z-index:-18;
  top:calc(55% + var(--py,0px));right:22%;
  background:radial-gradient(circle at 38%,#e0a062,#a06022);
  box-shadow:-2px -2px 4px rgba(0,0,0,0.5) inset;
  animation:pfl4 22s ease-in-out infinite; }
.pl-d2 {
  position:fixed;width:10px;height:10px;border-radius:50%;pointer-events:none;z-index:-18;
  top:calc(84% + var(--py,0px));left:20%;
  background:radial-gradient(circle at 38%,#b0a0e0,#504080);
  box-shadow:-2px -1px 3px rgba(0,0,0,0.5) inset;
  animation:pfl6 18s ease-in-out infinite; }

@keyframes pfl1{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-20px) rotate(4deg)}}
@keyframes pfl2{0%,100%{transform:translateY(0)}50%{transform:translateY(-16px)}}
@keyframes pfl3{0%,100%{transform:translateY(0) rotate(0deg)}33%{transform:translateY(-14px) rotate(-4deg)}66%{transform:translateY(-5px) rotate(3deg)}}
@keyframes pfl4{0%,100%{transform:translateY(0) translateX(0)}50%{transform:translateY(-12px) translateX(6px)}}
@keyframes pfl5{0%,100%{transform:translateY(0)}50%{transform:translateY(-10px)}}
@keyframes pfl6{0%,100%{transform:translateY(0) translateX(0)}33%{transform:translateY(-8px) translateX(-5px)}66%{transform:translateY(-14px) translateX(4px)}}
</style>

<canvas id="cosmic-cv"></canvas>
<div class="csm-neb nb1"></div><div class="csm-neb nb2"></div>
<div class="csm-neb nb3"></div><div class="csm-neb nb4"></div>
<div class="csm-gal gl1"></div><div class="csm-gal gl2"></div><div class="csm-gal gl3"></div>
<div class="pl-jup"></div>
<div class="pl-sat-w"><div class="pl-sat"></div><div class="pl-sat-r"></div></div>
<div class="pl-ear"></div><div class="pl-mar"></div><div class="pl-moon"></div>
<div class="pl-ice"></div><div class="pl-d1"></div><div class="pl-d2"></div>

<script>
(function(){
  if(window._cosmicCVinit) return; window._cosmicCVinit=true;
  var cv=document.getElementById("cosmic-cv");
  if(!cv){ setTimeout(function(){ window._cosmicCVinit=false; },800); return; }
  var cx=cv.getContext("2d");
  function rsz(){ cv.width=window.innerWidth; cv.height=window.innerHeight; }
  rsz(); window.addEventListener("resize",rsz);

  // Stars
  var SC=["#ffffff","#b8d8ff","#ffe4a0","#ffc4d4","#c0e8ff","#ffd880","#d0c0ff"];
  var ST=[];
  for(var i=0;i<420;i++){
    ST.push({x:Math.random()*3000,y:Math.random()*2000,r:Math.random()*1.8+0.15,
             op:Math.random(),dir:Math.random()<0.5?1:-1,spd:Math.random()*0.007+0.002,
             c:SC[Math.floor(Math.random()*SC.length)]});
  }

  // Asteroids (small slow drifters)
  var AS=[];
  for(var i=0;i<30;i++){
    AS.push({x:Math.random()*window.innerWidth,y:Math.random()*window.innerHeight,
             vx:(Math.random()-0.5)*0.15,vy:(Math.random()-0.5)*0.08,r:Math.random()*1.2+0.4});
  }

  // Shooting stars
  var SH=[]; var lsh=0;
  function nsh(){ return{x:Math.random()*cv.width*0.85,y:Math.random()*cv.height*0.38,
    len:Math.random()*120+55,spd:Math.random()*12+5,op:1,
    a:Math.PI/4+(Math.random()-0.5)*0.55}; }

  function frame(ts){
    cx.clearRect(0,0,cv.width,cv.height);

    // Galaxy core glow
    var gx=cv.width*0.77,gy=cv.height*0.17;
    var gg=cx.createRadialGradient(gx,gy,0,gx,gy,160);
    gg.addColorStop(0,"rgba(160,80,255,0.08)"); gg.addColorStop(0.4,"rgba(80,40,200,0.04)"); gg.addColorStop(1,"transparent");
    cx.fillStyle=gg; cx.beginPath(); cx.ellipse(gx,gy,160,96,0.38,0,Math.PI*2); cx.fill();

    // Stars
    for(var i=0;i<ST.length;i++){
      var s=ST[i]; s.op+=s.spd*s.dir;
      if(s.op>=1){s.op=1;s.dir=-1;} if(s.op<=0.08){s.op=0.08;s.dir=1;}
      cx.globalAlpha=s.op; cx.fillStyle=s.c;
      if(s.r>1.1){cx.shadowBlur=5;cx.shadowColor=s.c;}
      cx.beginPath(); cx.arc(s.x%cv.width,s.y%cv.height,s.r,0,Math.PI*2); cx.fill();
      cx.shadowBlur=0;
    }
    cx.globalAlpha=1;

    // Asteroids
    for(var i=0;i<AS.length;i++){
      var a=AS[i]; a.x+=a.vx; a.y+=a.vy;
      if(a.x<0)a.x=cv.width; if(a.x>cv.width)a.x=0;
      if(a.y<0)a.y=cv.height; if(a.y>cv.height)a.y=0;
      cx.globalAlpha=0.35; cx.fillStyle="#8090a0";
      cx.beginPath(); cx.arc(a.x,a.y,a.r,0,Math.PI*2); cx.fill();
    }
    cx.globalAlpha=1;

    // Shooting stars
    if(ts-lsh>6000+Math.random()*9000){ SH.push(nsh()); lsh=ts; }
    for(var j=SH.length-1;j>=0;j--){
      var sh=SH[j]; sh.x+=Math.cos(sh.a)*sh.spd; sh.y+=Math.sin(sh.a)*sh.spd; sh.op-=0.016;
      if(sh.op<=0){SH.splice(j,1);continue;}
      var sg=cx.createLinearGradient(sh.x,sh.y,sh.x-Math.cos(sh.a)*sh.len,sh.y-Math.sin(sh.a)*sh.len);
      sg.addColorStop(0,"rgba(255,255,255,"+sh.op+")");
      sg.addColorStop(0.5,"rgba(180,220,255,"+(sh.op*0.55)+")");
      sg.addColorStop(1,"rgba(255,255,255,0)");
      cx.strokeStyle=sg; cx.lineWidth=1.8; cx.beginPath();
      cx.moveTo(sh.x,sh.y); cx.lineTo(sh.x-Math.cos(sh.a)*sh.len,sh.y-Math.sin(sh.a)*sh.len); cx.stroke();
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  // ---- PARALLAX (rAF-based, works in all Streamlit scroll containers) ----
  var farEls=[".nb1",".gl1",".gl2",".gl3"];
  var midEls=[".nb2",".nb3",".nb4"];
  var nearEls=[".pl-jup",".pl-sat-w",".pl-ear",".pl-mar",".pl-moon",".pl-ice",".pl-d1",".pl-d2"];
  var lastSY=-1;
  function qAll(sels){ return sels.map(function(s){return Array.from(document.querySelectorAll(s))}).flat(); }
  function applyPY(sy){
    qAll(farEls).forEach(function(e){  e.style.setProperty("--py",(sy*0.22)+"px"); });
    qAll(midEls).forEach(function(e){  e.style.setProperty("--py",(sy*0.12)+"px"); });
    qAll(nearEls).forEach(function(e){ e.style.setProperty("--py",(sy*0.05)+"px"); });
  }
  function pollSY(){
    var sy=window.scrollY||0;
    var sc=document.querySelector("[data-testid=\"stAppViewContainer\"]");
    if(sc&&sc.scrollTop>sy) sy=sc.scrollTop;
    if(sy!==lastSY){ lastSY=sy; applyPY(sy); }
    requestAnimationFrame(pollSY);
  }
  pollSY();
})();
</script>
"""

# ===========================================================================
# 2. MAIN APP CSS
# ===========================================================================
APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html,body,[class*="css"],[data-testid="stApp"] {
  font-family:"Space Grotesk",sans-serif !important;
  color:#dde8f8 !important;
  overflow-x:hidden !important;
}
.block-container { padding-top:1.4rem !important; max-width:1380px !important; }

/* ---- COSMIC TITLE ---- */
.cosmic-title {
  font-family:"Exo 2",sans-serif; font-size:2.6rem; font-weight:900;
  letter-spacing:5px; text-transform:uppercase; line-height:1.15;
  background:linear-gradient(90deg,#00c8ff 0%,#b060ff 35%,#ff6090 60%,#ffcc00 80%,#00c8ff 100%);
  background-size:300% auto;
  -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  animation:titleShimmer 5s linear infinite;
}
@keyframes titleShimmer{0%{background-position:300% center}100%{background-position:-300% center}}
.cosmic-sub {
  font-family:"JetBrains Mono",monospace; font-size:0.8rem; letter-spacing:3px;
  color:#5ab4d8; text-transform:uppercase; margin-top:2px;
}

/* ---- GLASS CARD ---- */
.g-card {
  background:rgba(4,10,30,0.82); border-radius:14px; padding:1.2rem 1.4rem;
  border:1px solid rgba(90,180,255,0.14); margin-bottom:0.9rem;
  backdrop-filter:blur(14px); -webkit-backdrop-filter:blur(14px);
  box-shadow:0 0 30px rgba(0,0,0,0.5),0 0 60px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.04);
  color:#dde8f8; transition:border-color 0.4s;
}
.g-card:hover { border-color:rgba(90,180,255,0.35); }
.g-card.gc-cyan   { border-color:rgba(0,200,255,0.28); box-shadow:0 0 25px rgba(0,200,255,0.08); }
.g-card.gc-purple { border-color:rgba(176,96,255,0.28); box-shadow:0 0 25px rgba(176,96,255,0.08); }
.g-card.gc-green  { border-color:rgba(0,240,128,0.28); box-shadow:0 0 25px rgba(0,240,128,0.08); }
.g-card.gc-red    { border-color:rgba(255,80,100,0.28); box-shadow:0 0 25px rgba(255,80,100,0.08); }
.g-card.gc-gold   { border-color:rgba(255,200,0,0.28);  box-shadow:0 0 25px rgba(255,200,0,0.08); }

/* ---- SECTION LABEL ---- */
.sp-label {
  font-family:"JetBrains Mono",monospace; font-size:0.7rem; font-weight:700;
  letter-spacing:3px; text-transform:uppercase; color:#5ab4d8;
  border-bottom:1px solid rgba(90,180,255,0.18); padding-bottom:8px; margin-bottom:0.9rem;
}

/* ---- KEYWORDS ---- */
.kw-found   { background:rgba(0,220,100,0.1);  color:#4dffa0; border:1px solid rgba(0,220,100,0.3);
              padding:3px 10px; border-radius:20px; margin:2px; display:inline-block;
              font-size:0.77rem; font-family:"JetBrains Mono",monospace; font-weight:500; }
.kw-missing { background:rgba(255,60,100,0.1); color:#ff8099; border:1px solid rgba(255,60,100,0.3);
              padding:3px 10px; border-radius:20px; margin:2px; display:inline-block;
              font-size:0.77rem; font-family:"JetBrains Mono",monospace; font-weight:500; }
.kw-neutral { background:rgba(0,180,255,0.08); color:#64d0f8; border:1px solid rgba(0,180,255,0.25);
              padding:3px 10px; border-radius:20px; margin:2px; display:inline-block;
              font-size:0.77rem; font-family:"JetBrains Mono",monospace; font-weight:500; }
.kw-purple  { background:rgba(176,96,255,0.1); color:#c890ff; border:1px solid rgba(176,96,255,0.3);
              padding:3px 10px; border-radius:20px; margin:2px; display:inline-block;
              font-size:0.77rem; font-family:"JetBrains Mono",monospace; font-weight:500; }
.kw-gold    { background:rgba(255,196,0,0.1);  color:#ffd84d; border:1px solid rgba(255,196,0,0.3);
              padding:3px 10px; border-radius:20px; margin:2px; display:inline-block;
              font-size:0.77rem; font-family:"JetBrains Mono",monospace; font-weight:500; }

/* ---- VAL ---- */
.val-pass{color:#4dffa0;font-weight:600;} .val-fail{color:#ff5566;font-weight:600;}
.val-item{padding:0.38rem 0;border-bottom:1px solid rgba(255,255,255,0.05);font-size:0.87rem;}

/* ---- SCORE DISPLAY ---- */
.score-ring {
  border-radius:16px; padding:20px 28px;
  background:rgba(4,10,30,0.85); border:1px solid rgba(255,255,255,0.08);
  backdrop-filter:blur(12px); display:inline-block;
  box-shadow:0 0 40px rgba(0,0,0,0.6);
}
.score-num {
  font-family:"Exo 2",sans-serif; font-size:3.2rem; font-weight:900; line-height:1;
  display:block;
}
.score-excellent .score-num { color:#00f882; text-shadow:0 0 20px #00f882,0 0 40px rgba(0,248,130,0.3); }
.score-good      .score-num { color:#ffd200; text-shadow:0 0 20px #ffd200,0 0 40px rgba(255,210,0,0.3); }
.score-poor      .score-num { color:#ff3a5c; text-shadow:0 0 20px #ff3a5c,0 0 40px rgba(255,58,92,0.3); }
.score-excellent { border-color:rgba(0,248,130,0.3); box-shadow:0 0 30px rgba(0,248,130,0.12); }
.score-good      { border-color:rgba(255,210,0,0.3);  box-shadow:0 0 30px rgba(255,210,0,0.12); }
.score-poor      { border-color:rgba(255,58,92,0.3);  box-shadow:0 0 30px rgba(255,58,92,0.12); }

/* ---- SIDEBAR ---- */
section[data-testid="stSidebar"] {
  background:linear-gradient(180deg,rgba(3,7,22,0.97) 0%,rgba(2,5,18,0.98) 100%) !important;
  border-right:1px solid rgba(0,180,255,0.12) !important;
  box-shadow:4px 0 24px rgba(0,0,0,0.6) !important;
}
section[data-testid="stSidebar"] > div { background:transparent !important; }
section[data-testid="stSidebar"] * { color:#9ab8d0 !important; }
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 { color:#00c8ff !important; font-family:"JetBrains Mono",monospace !important; }
section[data-testid="stSidebar"] label { color:#6aa8be !important; font-size:0.8rem !important; letter-spacing:0.5px; }
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stTextArea textarea {
  background:rgba(0,180,255,0.04) !important;
  border:1px solid rgba(0,180,255,0.2) !important; border-radius:8px !important; color:#dde8f8 !important;
}
section[data-testid="stSidebar"] .stTextInput input:focus,
section[data-testid="stSidebar"] .stTextArea textarea:focus {
  border-color:rgba(0,180,255,0.6) !important; box-shadow:0 0 12px rgba(0,180,255,0.18) !important;
}
section[data-testid="stSidebar"] hr { border-color:rgba(0,180,255,0.1) !important; }
section[data-testid="stSidebar"] .stExpander { border:1px solid rgba(0,180,255,0.12) !important; border-radius:10px !important; background:rgba(0,180,255,0.02) !important; }

/* ---- MAIN TEXT AREAS ---- */
[data-testid="stTextArea"] textarea { background:rgba(4,10,30,0.8) !important; border:1px solid rgba(0,180,255,0.14) !important; border-radius:10px !important; color:#dde8f8 !important; font-family:"Space Grotesk",sans-serif !important; }
[data-testid="stTextArea"] textarea:focus { border-color:rgba(0,180,255,0.5) !important; box-shadow:0 0 16px rgba(0,180,255,0.14) !important; }

/* ---- GENERATE BUTTON ---- */
div[data-testid="stButton"] button[kind="primary"] {
  background:linear-gradient(135deg,rgba(0,190,255,0.1),rgba(160,40,255,0.12)) !important;
  border:1px solid rgba(0,190,255,0.55) !important; border-radius:12px !important;
  color:#00c8ff !important; font-family:"Exo 2",sans-serif !important;
  font-size:0.92rem !important; font-weight:800 !important;
  letter-spacing:3px !important; text-transform:uppercase !important;
  padding:0.78rem 2.2rem !important;
  box-shadow:0 0 22px rgba(0,190,255,0.18),0 0 44px rgba(0,190,255,0.06) !important;
  transition:all 0.35s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
  box-shadow:0 0 44px rgba(0,190,255,0.55),0 0 80px rgba(0,190,255,0.12) !important;
  border-color:rgba(0,190,255,0.95) !important; color:#ffffff !important;
  transform:translateY(-3px) !important;
}
div[data-testid="stButton"] button:not([kind="primary"]) {
  background:rgba(255,255,255,0.04) !important; border:1px solid rgba(255,255,255,0.1) !important;
  border-radius:8px !important; color:#8ab0c8 !important;
}
div[data-testid="stButton"] button:not([kind="primary"]):hover {
  border-color:rgba(0,180,255,0.4) !important; color:#00c8ff !important;
}

/* ---- DOWNLOAD BUTTONS ---- */
[data-testid="stDownloadButton"] button {
  background:rgba(0,220,100,0.07) !important; border:1px solid rgba(0,220,100,0.32) !important;
  border-radius:10px !important; color:#4dffa0 !important; font-weight:600 !important;
  box-shadow:0 0 12px rgba(0,220,100,0.1) !important;
}
[data-testid="stDownloadButton"] button:hover { box-shadow:0 0 28px rgba(0,220,100,0.35) !important; }

/* ---- TABS ---- */
.stTabs [data-baseweb="tab-list"] {
  background:rgba(4,10,30,0.7) !important; border-radius:10px !important;
  padding:4px !important; gap:4px !important; border:1px solid rgba(0,180,255,0.1) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius:8px !important; font-family:"Space Grotesk",sans-serif !important;
  font-weight:600 !important; font-size:0.82rem !important;
  color:#5a8aaa !important; background:transparent !important; border:none !important;
}
.stTabs [aria-selected="true"] {
  background:rgba(0,180,255,0.14) !important; color:#00c8ff !important;
  box-shadow:0 0 12px rgba(0,180,255,0.18) !important;
}

/* ---- EXPANDERS ---- */
[data-testid="stExpander"] { background:rgba(4,10,30,0.7) !important; border:1px solid rgba(0,180,255,0.1) !important; border-radius:10px !important; }
[data-testid="stExpander"] summary { color:#64d0f8 !important; font-weight:600 !important; font-size:0.87rem !important; }

/* ---- PROGRESS BAR ---- */
.stProgress > div > div > div { background:linear-gradient(90deg,#00c8ff,#b060ff) !important; border-radius:10px !important; box-shadow:0 0 10px rgba(0,180,255,0.4) !important; }
.stProgress > div > div { background:rgba(255,255,255,0.06) !important; border-radius:10px !important; }

/* ---- METRICS ---- */
[data-testid="stMetric"] { background:rgba(0,180,255,0.04) !important; border:1px solid rgba(0,180,255,0.1) !important; border-radius:10px !important; padding:0.6rem !important; }
[data-testid="stMetricValue"] { color:#00c8ff !important; font-family:"Exo 2",sans-serif !important; font-weight:700 !important; }
[data-testid="stMetricLabel"] { color:#5ab4d8 !important; font-size:0.72rem !important; }

/* ---- ALERTS ---- */
.stSuccess { background:rgba(0,220,100,0.07) !important; border-color:#00dc64 !important; color:#80ffb8 !important; }
.stInfo    { background:rgba(0,180,255,0.07) !important; border-color:#00b4ff !important; color:#7cd8f8 !important; }
.stWarning { background:rgba(255,196,0,0.08) !important; border-color:#ffc400 !important; color:#ffe08a !important; }
.stError   { background:rgba(255,60,80,0.07) !important; border-color:#ff3c50 !important; color:#ff9aaa !important; }

/* ---- SCROLLBAR ---- */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:#030610}
::-webkit-scrollbar-thumb{background:rgba(0,180,255,0.32);border-radius:2px}
hr{border-color:rgba(0,180,255,0.1) !important;}

/* ---- MOBILE ---- */
@media screen and (max-width:768px){
  .cosmic-title{font-size:1.6rem !important;letter-spacing:2px !important;}
  [data-testid="collapsedControl"],button[kind="header"]{display:none !important;}
  section[data-testid="stSidebar"][aria-expanded="false"]{display:none !important;width:0 !important;}
  section[data-testid="stSidebar"][aria-expanded="true"]{min-width:88vw !important;}
  .block-container{padding-left:0.7rem !important;padding-right:0.7rem !important;}
  [data-testid="stHorizontalBlock"]{flex-direction:column !important;}
  [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{width:100% !important;min-width:100% !important;}
  input,textarea{font-size:16px !important;}
}
</style>
"""

# inject both at top level so they appear before any content
st.markdown(SPACE_BG, unsafe_allow_html=True)
st.markdown(APP_CSS,  unsafe_allow_html=True)
st.markdown('<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">', unsafe_allow_html=True)


# ===========================================================================
# 3. CACHED GENERATORS
# ===========================================================================
@st.cache_resource
def get_jd_parser():
    from utils.jd_parser import JDParser; return JDParser()

@st.cache_resource
def get_resume_generator(provider: str = "DeepSeek", model: str = "deepseek-v4-pro"):
    from resume_generator import ResumeGenerator; return ResumeGenerator(provider, model)

@st.cache_resource
def get_cover_letter_generator(provider: str = "DeepSeek", model: str = "deepseek-v4-pro"):
    from cover_letter_generator import CoverLetterGenerator; return CoverLetterGenerator(provider, model)

@st.cache_resource
def get_latex_compiler():
    from latex_compiler import LatexCompiler; return LatexCompiler()


# ===========================================================================
# 4. HELPERS
# ===========================================================================
def score_cls(s):
    return "score-excellent" if s>=85 else "score-good" if s>=70 else "score-poor"

def score_hex(s):
    return "#00f882" if s>=85 else "#ffd200" if s>=70 else "#ff3a5c"

def render_ats_scorecard(ats_result):
    score=ats_result["total_score"]; grade=ats_result["grade"]
    cls=score_cls(score); col=score_hex(score)
    cl,cr=st.columns([1,2])
    with cl:
        st.markdown(f'<div class="score-ring {cls}"><span class="score-num">{score}</span>'
                    f'<span style="font-size:0.65rem;color:#5ab4d8;letter-spacing:2px;text-transform:uppercase;">/100 ATS SCORE</span></div>',
                    unsafe_allow_html=True)
        st.progress(int(score)/100)
    with cr:
        st.markdown(f'<div style="font-family:Exo 2,sans-serif;font-size:1.3rem;font-weight:800;color:{col};text-shadow:0 0 10px {col};margin-bottom:6px;">{grade}</div>', unsafe_allow_html=True)
        if score>=85: st.success("Excellent — will pass most ATS filters and impress recruiters.")
        elif score>=70: st.warning("Good — a few more keywords could push you to the top shortlist.")
        else: st.error("Needs improvement — may be auto-filtered.")

    st.markdown('<div class="sp-label" style="margin-top:1.2rem;">Score Breakdown</div>', unsafe_allow_html=True)
    breakdown=ats_result.get("breakdown",{})
    labels={"must_have_keywords":"Must-Have KW","hard_skills":"Hard Skills",
            "tools_and_technologies":"Tools","soft_skills":"Soft Skills",
            "job_title":"Job Title","education":"Education","experience":"Experience","formatting":"Formatting"}
    cols=st.columns(4)
    for i,(key,label) in enumerate(labels.items()):
        if key in breakdown:
            info=breakdown[key]; pts=info.get("score",0); mx=info.get("max",0)
            ratio=pts/mx if mx>0 else 1
            cv2="#00f882" if ratio>=0.85 else "#ffd200" if ratio>=0.6 else "#ff3a5c"
            with cols[i%4]:
                st.markdown(f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:0.6rem;text-align:center;"><div style="font-family:Exo 2,sans-serif;font-size:1rem;font-weight:700;color:{cv2};text-shadow:0 0 7px {cv2};">{pts}/{mx}</div><div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;">{label}</div></div>', unsafe_allow_html=True)
    missing=ats_result.get("missing_keywords",[])
    if missing:
        st.markdown('<div class="sp-label" style="margin-top:1rem;">Missing Keywords</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="kw-missing">{k}</span>' for k in missing[:25]), unsafe_allow_html=True)
    found=ats_result.get("found_keywords",[])
    if found:
        st.markdown('<div class="sp-label" style="margin-top:1rem;">Keywords Detected</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="kw-found">{k}</span>' for k in found[:30]), unsafe_allow_html=True)


def render_validation_report(validation):
    if validation.get("passed"):
        st.markdown('<div class="g-card gc-green"><b style="color:#4dffa0;">\u2714 SYSTEM CHECK PASSED</b> — All critical JD requirements are covered.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="g-card gc-gold"><b style="color:#ffd84d;">\u26a0 GAPS DETECTED</b> — Auto-fix pass was applied by AI.</div>', unsafe_allow_html=True)
    for label,ok in [("Experience bullets populated",validation.get("experience_ok",True)),
                     ("Projects section present",validation.get("projects_ok",True)),
                     ("Skills section populated",validation.get("skills_ok",True))]:
        icon,css=("\u2714 OK","val-pass") if ok else ("\u2716 FAIL","val-fail")
        st.markdown(f'<div class="val-item"><span class="{css}">{icon}&nbsp; {label}</span></div>', unsafe_allow_html=True)
    mm=validation.get("missing_must_haves",[])
    if mm:
        st.markdown('<div class="sp-label" style="margin-top:0.8rem;">Missing Must-Haves</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="kw-missing">{k}</span>' for k in mm), unsafe_allow_html=True)
    else:
        st.markdown('<div class="val-item"><span class="val-pass">\u2714 OK&nbsp; All must-have keywords present</span></div>', unsafe_allow_html=True)
    mh=validation.get("missing_hard_skills",[])
    if mh:
        st.markdown('<div class="sp-label" style="margin-top:0.8rem;">Missing Hard Skills</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="kw-missing">{k}</span>' for k in mh), unsafe_allow_html=True)
    else:
        st.markdown('<div class="val-item"><span class="val-pass">\u2714 OK&nbsp; All hard skills demonstrated</span></div>', unsafe_allow_html=True)
    mt=validation.get("missing_tools",[])
    if mt:
        st.markdown('<div class="sp-label" style="margin-top:0.8rem;">Unmentioned Tools</div>', unsafe_allow_html=True)
        st.markdown(" ".join(f'<span class="kw-neutral">{k}</span>' for k in mt), unsafe_allow_html=True)


def _extract_text_from_file(uploaded_file):
    name=uploaded_file.name.lower()
    try:
        if name.endswith(".pdf"):
            import pypdf; reader=pypdf.PdfReader(uploaded_file)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        elif name.endswith(".docx"):
            import docx; doc=docx.Document(uploaded_file)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        st.error(f"File read error: {e}")
    return ""


@st.cache_data(show_spinner=False)
def _parse_resume_text(resume_text):
    import httpx, openai
    from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, OPENAI_MODEL
    client=openai.OpenAI(api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL, http_client=httpx.Client(verify=False))
    system='Extract info from resume. Return ONLY JSON: {"full_name":"","email":"","phone":"","location":"","linkedin":"","github":""}. No markdown.'
    r=client.chat.completions.create(model=OPENAI_MODEL, temperature=0,
        messages=[{"role":"system","content":system},{"role":"user","content":resume_text[:4000]}])
    raw=re.sub(r"^```(?:json)?\s*","",r.choices[0].message.content.strip())
    raw=re.sub(r"\s*```$","",raw)
    try:    return json.loads(raw)
    except: return {}


# ===========================================================================
# 5. SIDEBAR
# ===========================================================================
def render_sidebar():
    with st.sidebar:
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:1rem;font-weight:700;color:#00c8ff;letter-spacing:3px;text-shadow:0 0 12px rgba(0,200,255,0.6);">COSMIC CV</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.68rem;color:#3a8aaa;letter-spacing:2px;margin-top:-2px;margin-bottom:4px;">AI RESUME SYNTHESIS ENGINE</div>', unsafe_allow_html=True)
        st.divider()

        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;letter-spacing:2px;color:#5ab4d8;text-transform:uppercase;margin-bottom:8px;">Identity Module</div>', unsafe_allow_html=True)
        with st.expander("Upload / Paste Resume to Auto-Fill", expanded=not st.session_state.get("profile_loaded")):
            upload_tab,paste_tab=st.tabs(["File Upload","Paste Text"])
            with upload_tab:
                uploaded_file=st.file_uploader("PDF or DOCX",type=["pdf","docx"],key="resume_file_upload")
                if st.button("Extract & Auto-Fill",use_container_width=True,type="primary",key="btn_file"):
                    if uploaded_file:
                        with st.spinner("Parsing..."):
                            extracted=_extract_text_from_file(uploaded_file)
                            if extracted:
                                info=_parse_resume_text(extracted)
                                for k,sk in [("full_name","si_full_name"),("email","si_email"),("phone","si_phone"),("location","si_location"),("linkedin","si_linkedin"),("github","si_github")]:
                                    if info.get(k): st.session_state[sk]=info[k]
                                st.session_state["si_background"]=extracted
                                st.session_state["profile_loaded"]=True
                                st.success("Fields auto-filled."); st.rerun()
                            else: st.error("Could not extract text.")
                    else: st.warning("Upload a file first.")
            with paste_tab:
                pasted=st.text_area("Resume text",height=120,placeholder="Paste your full resume...",key="pasted_resume_raw")
                if st.button("Parse & Auto-Fill",use_container_width=True,type="primary",key="btn_paste"):
                    if pasted.strip():
                        with st.spinner("Parsing..."): info=_parse_resume_text(pasted)
                        for k,sk in [("full_name","si_full_name"),("email","si_email"),("phone","si_phone"),("location","si_location"),("linkedin","si_linkedin"),("github","si_github")]:
                            if info.get(k): st.session_state[sk]=info[k]
                        st.session_state["si_background"]=pasted; st.session_state["profile_loaded"]=True
                        st.success("Done!"); st.rerun()
                    else: st.warning("Paste your resume first.")

        st.divider()
        full_name=st.text_input("Full Name *",  key="si_full_name", placeholder="Your Full Name")
        email    =st.text_input("Email *",       key="si_email",     placeholder="you@email.com")
        phone    =st.text_input("Phone",         key="si_phone",     placeholder="+65 XXXX XXXX")
        location =st.text_input("Location",      key="si_location",  placeholder="Singapore")
        linkedin =st.text_input("LinkedIn URL",  key="si_linkedin",  placeholder="https://linkedin.com/in/...")
        github   =st.text_input("GitHub URL",    key="si_github",    placeholder="https://github.com/...")

        st.divider()
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;letter-spacing:2px;color:#5ab4d8;text-transform:uppercase;margin-bottom:8px;">Engine Config</div>', unsafe_allow_html=True)

        # ── AI Provider + Model selectors ──────────────────────────────────
        ai_provider = st.selectbox(
            "🤖 AI Provider",
            options=list(PROVIDER_MODELS.keys()),
            index=0,
            key="ai_provider",
            help="Choose which AI to power resume generation.",
        )
        ai_model = st.selectbox(
            "🧠 Model",
            options=PROVIDER_MODELS[ai_provider],
            index=0,
            key="ai_model",
            help="Select the model for the chosen provider.",
        )
        # Show a subtle info badge
        provider_color = "#00c8ff" if ai_provider == "DeepSeek" else "#10a37f"
        st.markdown(
            f'<div style="background:rgba(4,10,30,0.7);border:1px solid {provider_color}33;'
            f'border-radius:8px;padding:6px 10px;font-size:0.72rem;color:{provider_color};'
            f'letter-spacing:1px;margin-bottom:4px;">⚡ {ai_provider} · {ai_model}</div>',
            unsafe_allow_html=True,
        )

        target_score   =st.slider("Target ATS Score",      min_value=70,max_value=100,value=ATS_TARGET_SCORE, help="AI iterates until this score is reached.")
        max_iterations =st.slider("Max Improvement Rounds",min_value=1, max_value=6,  value=2, help="2 = best speed/score balance.")

        st.divider()
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;letter-spacing:2px;color:#5ab4d8;text-transform:uppercase;margin-bottom:8px;">Mode Settings</div>', unsafe_allow_html=True)
        allow_title_change=st.toggle("Optimise titles to match JD",value=False, help="OFF = freeze your exact titles. ON = AI aligns titles with JD.")
        if allow_title_change:
            st.markdown('<div style="background:rgba(176,96,255,0.08);border:1px solid rgba(176,96,255,0.22);border-radius:8px;padding:8px;font-size:0.74rem;color:#c890ff;">AI will align role titles to JD. Company names and dates stay frozen.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="background:rgba(0,220,100,0.07);border:1px solid rgba(0,220,100,0.2);border-radius:8px;padding:8px;font-size:0.74rem;color:#4dffa0;">Your exact job titles preserved.</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown('<div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;letter-spacing:2px;color:#5ab4d8;text-transform:uppercase;margin-bottom:8px;">Output Config</div>', unsafe_allow_html=True)
        gen_cover_letter =st.checkbox("Generate Cover Letter",value=True)
        show_latex_source=st.checkbox("Show LaTeX source",   value=False)

        if "ats_result" in st.session_state:
            st.divider()
            sc=st.session_state["ats_result"]["total_score"]; col=score_hex(sc)
            st.markdown(f'<div style="text-align:center;padding:14px;background:rgba(4,10,30,0.8);border:1px solid rgba(255,255,255,0.07);border-radius:12px;"><div style="font-family:Exo 2,sans-serif;font-size:2rem;font-weight:900;color:{col};text-shadow:0 0 16px {col};">{sc}</div><div style="font-size:0.63rem;color:#5ab4d8;letter-spacing:2px;text-transform:uppercase;">Last ATS Score</div></div>', unsafe_allow_html=True)

    return (full_name,email,phone,location,linkedin,github,
            target_score,max_iterations,allow_title_change,
            gen_cover_letter,show_latex_source,
            ai_provider,ai_model)


# ===========================================================================
# 6. MAIN
# ===========================================================================
def main():
    (full_name,email,phone,location,linkedin,github,
     target_score,max_iterations,allow_title_change,
     gen_cover_letter,show_latex_source,
     ai_provider,ai_model)=render_sidebar()

    # ---- COSMIC HEADER ----
    h1,h2=st.columns([5,1])
    with h1:
        st.markdown('<p class="cosmic-title">COSMIC CV</p>', unsafe_allow_html=True)
        st.markdown('<p class="cosmic-sub">// Universe AI Resume Synthesis  //  DeepSeek V4 Pro  //  ATS-Optimised  //</p>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div style="background:rgba(4,10,30,0.8);border:1px solid rgba(0,180,255,0.2);border-radius:12px;padding:12px;text-align:center;margin-top:6px;backdrop-filter:blur(10px);"><div style="font-family:Exo 2,sans-serif;font-size:1.1rem;font-weight:900;color:#00c8ff;text-shadow:0 0 10px #00c8ff;">95%+</div><div style="font-size:0.62rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;">ATS Pass Rate</div></div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

    # ---- INPUT PANELS ----
    left,right=st.columns([1,1],gap="large")
    with left:
        st.markdown('<div class="sp-label">// Job Description</div>', unsafe_allow_html=True)
        jd_text=st.text_area("JD",height=330,label_visibility="collapsed",
            placeholder="Paste full Job Description here...\n\n• Job title & company\n• Responsibilities & requirements\n• Required skills\n• Nice-to-have skills\n\nMore detail = higher ATS score")
        if jd_text and st.button("Scan JD Intelligence",use_container_width=True,key="btn_scan_jd"):
            with st.spinner("Scanning..."):
                try:
                    parser=get_jd_parser(); parsed=parser.parse(jd_text)
                    st.session_state["parsed_jd"]=parsed
                    st.session_state["parsed_jd_hash"]=hashlib.md5(jd_text.encode()).hexdigest()
                    st.success("JD intelligence extracted.")
                except Exception as e: st.error(f"Parse failed: {e}")
        if "parsed_jd" in st.session_state:
            p=st.session_state["parsed_jd"]
            with st.expander("JD Intelligence Report",expanded=False):
                ic1,ic2=st.columns(2)
                with ic1:
                    st.markdown(f'<div class="g-card gc-cyan"><div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;">ROLE</div><div style="font-weight:700;color:#dde8f8;">{p.get("job_title","")}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="g-card"><div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;">SENIORITY</div><div style="font-weight:700;color:#dde8f8;">{p.get("seniority_level","")}</div></div>', unsafe_allow_html=True)
                with ic2:
                    st.markdown(f'<div class="g-card"><div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;">COMPANY</div><div style="font-weight:700;color:#dde8f8;">{p.get("company_name","N/A")}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="g-card"><div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;">EXPERIENCE</div><div style="font-weight:700;color:#dde8f8;">{p.get("experience_years_min",0)}-{p.get("experience_years_max",10)} yrs</div></div>', unsafe_allow_html=True)
                mh=p.get("must_have_keywords",[])
                if mh:
                    st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;margin:8px 0 4px;">MUST-HAVE KEYWORDS</div>', unsafe_allow_html=True)
                    st.markdown(" ".join(f'<span class="kw-found">{k}</span>' for k in mh), unsafe_allow_html=True)
                hs=p.get("hard_skills",[])
                if hs:
                    st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;margin:8px 0 4px;">HARD SKILLS</div>', unsafe_allow_html=True)
                    st.markdown(" ".join(f'<span class="kw-neutral">{k}</span>' for k in hs), unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sp-label">// Your Background</div>', unsafe_allow_html=True)
        user_background=st.text_area("BG",value=st.session_state.get("si_background",""),height=330,
            label_visibility="collapsed",
            placeholder="Paste your full resume (or sidebar auto-fill)\n\nWORK EXPERIENCE:\n• [Company], [Title], [Dates]: achievements\n\nSKILLS: Python, AWS, Docker, LangChain...\n\nEDUCATION: B.Eng Computer Engineering, NUS\n\nPROJECTS: Multi-agent RAG pipeline...\n\nMore detail = higher ATS score",
            key="si_background")
        bg_len=len(user_background)
        if bg_len>0:
            if bg_len>800:   qual='<span style="color:#4dffa0;font-weight:700;">SIGNAL STRONG</span>'
            elif bg_len>300: qual='<span style="color:#ffd84d;font-weight:700;">ADD MORE DATA</span>'
            else:            qual='<span style="color:#ff8099;font-weight:700;">INSUFFICIENT DATA</span>'
            st.markdown(f'<div style="font-family:JetBrains Mono,monospace;font-size:0.7rem;color:#5ab4d8;margin-top:4px;">{qual} &nbsp;|&nbsp; {bg_len:,} chars &nbsp;|&nbsp; ~{bg_len//5:,} words</div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin:0.8rem 0;">', unsafe_allow_html=True)

    # ---- GENERATE BUTTON ----
    ready=bool(jd_text and user_background and full_name and email)
    g1,g2,g3=st.columns([1,2,1])
    with g2:
        btn_label="LAUNCH RESUME  //  TITLES OPTIMISED" if allow_title_change else "LAUNCH RESUME SYNTHESIS"
        generate_btn=st.button(btn_label,use_container_width=True,type="primary",disabled=not ready)

    if not ready:
        missing=[]
        if not jd_text:         missing.append("Job Description")
        if not user_background: missing.append("Your Background")
        if not full_name:       missing.append("Full Name (sidebar)")
        if not email:           missing.append("Email (sidebar)")
        st.markdown(f'<div style="text-align:center;font-family:JetBrains Mono,monospace;font-size:0.76rem;color:#5ab4d8;margin-top:6px;">[ AWAITING: {" // ".join(missing)} ]</div>', unsafe_allow_html=True)

    if ready:
        st.markdown('<div style="background:rgba(255,196,0,0.06);border:1px solid rgba(255,196,0,0.24);border-radius:10px;padding:10px 14px;font-size:0.81rem;color:#ffe08a;margin-top:6px;">MOBILE: Keep this tab open + screen awake during generation. Tab switching kills the process.</div>', unsafe_allow_html=True)

    # ---- GENERATION PIPELINE ----
    if generate_btn:
        st.toast("Keep this tab open during synthesis!", icon="\U0001f680")
        user_profile=f"Name: {full_name}\nEmail: {email}\nPhone: {phone}\nLocation: {location}\nLinkedIn: {linkedin}\nGitHub: {github}\n\nPROFESSIONAL BACKGROUND:\n{user_background}".strip()
        pb=st.progress(0,text="Initialising..."); msg=st.empty()
        try:
            jd_hash=hashlib.md5(jd_text.encode()).hexdigest()
            if st.session_state.get("parsed_jd_hash")==jd_hash and "parsed_jd" in st.session_state:
                parsed_jd=st.session_state["parsed_jd"]
                pb.progress(15,text="JD cached — skipping re-scan")
            else:
                msg.info("SCANNING JD — Extracting role intelligence...")
                parser=get_jd_parser(); parsed_jd=parser.parse(jd_text)
                st.session_state["parsed_jd"]=parsed_jd; st.session_state["parsed_jd_hash"]=jd_hash
                pb.progress(15,text="JD intelligence extracted")

            jd_title=parsed_jd.get("job_title","Role"); jd_co=parsed_jd.get("company_name","Company")
            msg.info(f"SYNTHESISING — Crafting resume for {jd_title} @ {jd_co}  |  Target {target_score}+  |  {max_iterations} rounds")
            resume_gen=get_resume_generator(ai_provider, ai_model)
            gen_opts={"allow_title_change":allow_title_change,"max_iterations":max_iterations}
            gen_result=resume_gen.generate(user_profile,parsed_jd,target_score,gen_opts)

            resume_data=gen_result["resume_data"]
            if isinstance(resume_data,str):
                try:   resume_data=json.loads(resume_data)
                except: resume_data={}
            resume_data.update({"full_name":full_name,"email":email,"phone":phone,
                                 "location":location,"linkedin":linkedin,"github":github})
            ats_result=gen_result["ats_result"]; validation=gen_result.get("validation",{})
            pb.progress(55,text=f"Resume synthesised — ATS: {ats_result['total_score']}/100")

            cover_letter_data=None
            if gen_cover_letter:
                msg.info("COMPOSING — Writing targeted cover letter...")
                cover_letter_data=get_cover_letter_generator(ai_provider, ai_model).generate(user_profile,parsed_jd,resume_data)
                pb.progress(68,text="Cover letter composed")

            msg.info("RENDERING — Compiling LaTeX document...")
            compiler=get_latex_compiler()
            resume_tex=compiler.render_resume(resume_data)
            ts=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name=re.sub(r"\W+","_",full_name.strip())
            res_file=f"Resume_{safe_name}_{ts}"
            res_pdf=compiler.compile_to_pdf(resume_tex,res_file,resume_data=resume_data)

            cl_tex,cl_pdf,cl_file="",{},f"CoverLetter_{safe_name}_{ts}"
            if cover_letter_data:
                cl_tex=compiler.render_cover_letter(cover_letter_data,
                    {"full_name":full_name,"email":email,"phone":phone,"location":location,"linkedin":linkedin,"github":github},jd_co)
                cl_pdf=compiler.compile_to_pdf(cl_tex,cl_file,cover_letter_data=cover_letter_data,
                    user_info={"full_name":full_name,"email":email,"phone":phone,"location":location,"linkedin":linkedin,"github":github})
            pb.progress(95,text="Documents rendered")

            st.session_state.update({
                "resume_data":resume_data,"resume_tex":resume_tex,"resume_pdf_result":res_pdf,
                "ats_result":ats_result,"validation":validation,"gen_history":gen_result["history"],
                "cl_data":cover_letter_data,"cl_tex":cl_tex,"cl_pdf_result":cl_pdf,
                "resume_file":res_file,"cl_file":cl_file,"gen_opts":gen_opts,
                "jd_title":jd_title,"jd_company":jd_co,
            })
            pb.progress(100,text="SYNTHESIS COMPLETE")
            vs="ALL SYSTEMS GO" if validation.get("passed") else "GAPS AUTO-PATCHED"
            msg.success(f"MISSION COMPLETE  //  ATS: {ats_result['total_score']}/100  //  {gen_result['iterations']} rounds  //  {vs}")

        except Exception as e:
            pb.empty(); msg.error(f"SYNTHESIS FAILED: {e}"); st.exception(e)

    # ---- RESULTS ----
    if "ats_result" in st.session_state:
        sc=st.session_state["ats_result"]["total_score"]
        col=score_hex(sc); jd_t=st.session_state.get("jd_title",""); jd_c=st.session_state.get("jd_company","")
        val=st.session_state.get("validation",{}); n_it=len(st.session_state.get("gen_history",[]))
        vst="VALIDATED" if val.get("passed") else "PATCHED"
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(0,160,255,0.08),rgba(150,30,255,0.08));'
            f'border:1px solid rgba(0,160,255,0.2);border-radius:16px;padding:18px 28px;'
            f'margin:1rem 0;backdrop-filter:blur(10px);display:flex;align-items:center;gap:24px;flex-wrap:wrap;">'
            f'<div style="font-family:Exo 2,sans-serif;font-size:2.8rem;font-weight:900;color:{col};text-shadow:0 0 22px {col};">{sc}</div>'
            f'<div><div style="font-size:0.6rem;color:#5ab4d8;letter-spacing:2px;text-transform:uppercase;">ATS Score / 100</div>'
            f'<div style="font-size:1rem;font-weight:700;color:#dde8f8;">{jd_t} @ {jd_c}</div>'
            f'<div style="font-size:0.72rem;color:#5ab4d8;font-family:JetBrains Mono,monospace;">{vst} &nbsp;|&nbsp; {n_it} AI ROUNDS</div></div>'
            f'</div>', unsafe_allow_html=True)

        tab1,tab2,tab3,tab4,tab5=st.tabs(["Resume","Cover Letter","ATS Score","Validation","Raw Data"])

        with tab1:
            rd=st.session_state["resume_data"]
            dl1,dl2=st.columns(2)
            with dl1:
                st.download_button("Download .tex",data=st.session_state["resume_tex"],
                    file_name=f"{st.session_state['resume_file']}.tex",mime="text/plain",use_container_width=True)
            with dl2:
                rp=st.session_state["resume_pdf_result"]
                if rp.get("success") and rp.get("pdf_path"):
                    with open(rp["pdf_path"],"rb") as f:
                        st.download_button("Download PDF",data=f.read(),
                            file_name=f"{st.session_state['resume_file']}.pdf",mime="application/pdf",use_container_width=True)
                else: st.warning("PDF unavailable — download .tex above.")

            st.markdown('<div class="sp-label" style="margin-top:1rem;">Professional Summary</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="g-card">{rd.get("summary","")}</div>', unsafe_allow_html=True)
            if rd.get("headline"):
                st.markdown(f'<div class="g-card gc-purple"><span style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;">Headline</span><br><span style="font-weight:600;color:#dde8f8;">{rd["headline"]}</span></div>', unsafe_allow_html=True)

            st.markdown('<div class="sp-label" style="margin-top:1rem;">Work Experience</div>', unsafe_allow_html=True)
            for job in rd.get("experience",[]):
                if not isinstance(job,dict): continue
                title=job.get("title",""); company=job.get("company","")
                start=job.get("start_date",""); end=job.get("end_date","")
                ctx=job.get("context",""); bullets=job.get("bullets",[])
                with st.expander(f"{title}  //  {company}  //  {start} \u2192 {end}",expanded=True):
                    if ctx: st.markdown(f'<div style="color:#5ab4d8;font-style:italic;font-size:0.84rem;margin-bottom:8px;border-left:2px solid rgba(0,180,255,0.35);padding-left:10px;">{ctx}</div>', unsafe_allow_html=True)
                    for b in (bullets if isinstance(bullets,list) else []):
                        st.markdown(f'<div style="padding:4px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:0.87rem;"><span style="color:#00c8ff;">\u25b8</span> {b}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sp-label" style="margin-top:1rem;">Skills Matrix</div>', unsafe_allow_html=True)
            cats=rd.get("skill_categories",[])
            if cats:
                sc_cols=st.columns(min(3,len(cats)))
                for i,cat in enumerate(cats):
                    if not isinstance(cat,dict): continue
                    with sc_cols[i%3]:
                        st.markdown(f'<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">{cat.get("category","")}</div>', unsafe_allow_html=True)
                        sl=cat.get("skills",[])
                        if isinstance(sl,list):
                            st.markdown(" ".join(f'<span class="kw-neutral">{s}</span>' for s in sl), unsafe_allow_html=True)
                        st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
            else:
                sk=rd.get("skills",{})
                if sk:
                    sc1,sc2=st.columns(2)
                    with sc1:
                        ts_=sk.get("technical_skills",[])
                        if ts_:
                            st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">Technical</div>', unsafe_allow_html=True)
                            st.markdown(" ".join(f'<span class="kw-neutral">{s}</span>' for s in (ts_ if isinstance(ts_,list) else [])), unsafe_allow_html=True)
                        tt_=sk.get("tools_technologies",[])
                        if tt_:
                            st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin:8px 0 6px;">Tools</div>', unsafe_allow_html=True)
                            st.markdown(" ".join(f'<span class="kw-neutral">{s}</span>' for s in (tt_ if isinstance(tt_,list) else [])), unsafe_allow_html=True)
                    with sc2:
                        ss_=sk.get("soft_skills",[])
                        if ss_:
                            st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">Soft Skills</div>', unsafe_allow_html=True)
                            st.markdown(" ".join(f'<span class="kw-purple">{s}</span>' for s in (ss_ if isinstance(ss_,list) else [])), unsafe_allow_html=True)

            projs=rd.get("projects",[])
            if projs:
                st.markdown('<div class="sp-label" style="margin-top:1rem;">Projects</div>', unsafe_allow_html=True)
                for proj in projs:
                    if not isinstance(proj,dict): continue
                    with st.expander(f"{proj.get('name','')}  //  {proj.get('year','')}"):
                        if proj.get("description"): st.markdown(f'<div style="color:#5ab4d8;font-style:italic;font-size:0.84rem;margin-bottom:8px;">{proj["description"]}</div>', unsafe_allow_html=True)
                        for b in (proj.get("bullets",[]) or []):
                            st.markdown(f'<div style="padding:4px 0;font-size:0.87rem;"><span style="color:#00c8ff;">\u25b8</span> {b}</div>', unsafe_allow_html=True)
                        techs=proj.get("technologies",[])
                        if isinstance(techs,list) and techs:
                            st.markdown("<div style='margin-top:8px;'>"+(" ".join(f'<span class="kw-neutral">{t}</span>' for t in techs))+"</div>", unsafe_allow_html=True)

            edu_list=rd.get("education",[])
            if edu_list:
                st.markdown('<div class="sp-label" style="margin-top:1rem;">Education</div>', unsafe_allow_html=True)
                for edu in edu_list:
                    if not isinstance(edu,dict): continue
                    st.markdown(f'<div class="g-card"><span style="font-weight:700;color:#dde8f8;">{edu.get("degree","")} in {edu.get("field","")}</span> \u2014 {edu.get("institution","")} ({edu.get("graduation_year","")})</div>', unsafe_allow_html=True)

            certs=rd.get("certifications",[])
            if certs:
                st.markdown('<div class="sp-label" style="margin-top:1rem;">Certifications</div>', unsafe_allow_html=True)
                st.markdown(" ".join(f'<span class="kw-gold">{c if isinstance(c,str) else c.get("name","")}</span>' for c in certs), unsafe_allow_html=True)

            if show_latex_source:
                with st.expander("LaTeX Source"):
                    st.code(st.session_state["resume_tex"],language="latex")

        with tab2:
            if st.session_state.get("cl_data"):
                cl=st.session_state["cl_data"]
                st.markdown(f'<div class="g-card gc-cyan"><span style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;">Subject Line</span><br><span style="font-weight:700;color:#dde8f8;">{cl.get("subject_line","")}</span></div>', unsafe_allow_html=True)
                cld1,cld2=st.columns(2)
                with cld1:
                    if st.session_state.get("cl_tex"):
                        st.download_button("Download .tex",data=st.session_state["cl_tex"],file_name=f"{st.session_state['cl_file']}.tex",mime="text/plain",use_container_width=True)
                with cld2:
                    cp=st.session_state.get("cl_pdf_result",{})
                    if cp.get("success") and cp.get("pdf_path"):
                        with open(cp["pdf_path"],"rb") as f:
                            st.download_button("Download PDF",data=f.read(),file_name=f"{st.session_state['cl_file']}.pdf",mime="application/pdf",use_container_width=True)
                st.markdown(f'<div class="g-card" style="white-space:pre-line;line-height:1.8;font-size:0.87rem;">{cl.get("full_text","")}</div>', unsafe_allow_html=True)
                if show_latex_source and st.session_state.get("cl_tex"):
                    with st.expander("LaTeX Source"): st.code(st.session_state["cl_tex"],language="latex")
            else:
                st.info("Enable 'Generate Cover Letter' in the sidebar and regenerate.")

        with tab3:
            render_ats_scorecard(st.session_state["ats_result"])
            hist=st.session_state.get("gen_history",[])
            if len(hist)>1:
                st.markdown('<div class="sp-label" style="margin-top:1rem;">Score Trajectory</div>', unsafe_allow_html=True)
                import pandas as pd
                df=pd.DataFrame(hist)
                df["label"]=df.apply(lambda r:f"Round {r['iteration']}"+(f" ({r['note']})" if r.get("note") else ""),axis=1)
                st.line_chart(df.set_index("label")["score"])

        with tab4:
            st.markdown('<div class="sp-label">System Validation Report</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:0.81rem;color:#6aa8be;margin-bottom:1rem;">Post-generation check: verifies all critical JD requirements are embedded in the resume. If gaps found, AI ran an auto-patch pass.</div>', unsafe_allow_html=True)
            val=st.session_state.get("validation",{})
            if val: render_validation_report(val)
            else:   st.info("No validation data available.")
            if "parsed_jd" in st.session_state:
                p=st.session_state["parsed_jd"]
                with st.expander("Full JD Requirements Reference"):
                    for section,title,cls in [("must_have_keywords","MUST-HAVE KEYWORDS","kw-found"),("hard_skills","HARD SKILLS","kw-neutral"),("tools_and_technologies","TOOLS & TECH","kw-neutral")]:
                        items=p.get(section,[])
                        if items:
                            st.markdown(f'<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;">{title}</div>', unsafe_allow_html=True)
                            st.markdown(" ".join(f'<span class="{cls}">{k}</span>' for k in items), unsafe_allow_html=True)
                    resp=p.get("responsibilities",[])
                    if resp:
                        st.markdown('<div style="font-size:0.66rem;color:#5ab4d8;letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;">KEY RESPONSIBILITIES</div>', unsafe_allow_html=True)
                        for i,r in enumerate(resp[:10],1):
                            st.markdown(f'<div style="font-size:0.82rem;padding:3px 0;color:#9ab8d0;"><span style="color:#00c8ff;font-family:JetBrains Mono,monospace;">{i:02d}.</span> {r}</div>', unsafe_allow_html=True)

        with tab5:
            rt1,rt2,rt3,rt4=st.tabs(["Resume JSON","Cover Letter JSON","Parsed JD","Generation Log"])
            with rt1: st.json(st.session_state["resume_data"])
            with rt2: st.json(st.session_state["cl_data"]) if st.session_state.get("cl_data") else st.info("No cover letter.")
            with rt3: st.json(st.session_state["parsed_jd"]) if "parsed_jd" in st.session_state else st.info("No JD parsed.")
            with rt4: st.json({"options":st.session_state.get("gen_opts",{}),"score_history":st.session_state.get("gen_history",[]),"validation":st.session_state.get("validation",{})})


if __name__ == "__main__":
    main()
