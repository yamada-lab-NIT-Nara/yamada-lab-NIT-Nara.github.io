(()=>{
 const root=document.querySelector('.cms-facility-slider');if(!root)return;
 const slides=[...root.querySelectorAll('.cms-facility-slide')],dots=[...root.querySelectorAll('.cms-facility-dot')];let active=0;
 const show=i=>{if(!slides.length)return;active=(i+slides.length)%slides.length;slides.forEach((s,j)=>{const current=j===active;s.classList.toggle('is-active',current);s.setAttribute('aria-hidden',String(!current));s.tabIndex=current?0:-1});dots.forEach((d,j)=>{d.classList.toggle('is-active',j===active);d.setAttribute('aria-current',String(j===active))})};
 root.querySelector('.cms-facility-prev')?.addEventListener('click',()=>show(active-1));
 root.querySelector('.cms-facility-next')?.addEventListener('click',()=>show(active+1));
 dots.forEach((dot,i)=>dot.addEventListener('click',()=>show(i)));show(0);
 if(slides.length>1&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){let timer=setInterval(()=>{if(!document.hidden&&!root.matches(':hover')&&!root.contains(document.activeElement))show(active+1)},5000);}
})();
