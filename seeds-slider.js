/* Scroll-snap slider. Add future seed cards to #seed-carousel; controls adapt automatically. */
(()=>{
  const rail=document.getElementById('seed-carousel');
  if(!rail)return;
  const cards=[...rail.querySelectorAll('.seed-carousel-card')];
  const prev=document.querySelector('[data-seed-prev]');
  const next=document.querySelector('[data-seed-next]');
  const status=document.querySelector('.seed-carousel-status');
  const gap=()=>parseFloat(getComputedStyle(rail).gap)||0;
  const stride=()=>cards[0]?.getBoundingClientRect().width+gap()||1;
  function update(){
    const index=Math.min(cards.length-1,Math.max(0,Math.round(rail.scrollLeft/stride())));
    if(status)status.textContent=String(index+1).padStart(2,'0')+' / '+String(cards.length).padStart(2,'0');
    if(prev)prev.disabled=rail.scrollLeft<=2;
    if(next)next.disabled=rail.scrollLeft>=rail.scrollWidth-rail.clientWidth-2;
  }
  function move(dir){rail.scrollBy({left:stride()*dir,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
  prev?.addEventListener('click',()=>move(-1));next?.addEventListener('click',()=>move(1));
  rail.addEventListener('scroll',update,{passive:true});window.addEventListener('resize',update);
  update();
})();
