(()=>{
  const menu=document.getElementById('menu-toggle'),nav=document.getElementById('nav');
  menu?.addEventListener('click',()=>{const opened=nav.classList.toggle('open');menu.setAttribute('aria-expanded',String(opened))});
  const slides=[...document.querySelectorAll('[data-hero]')],dots=[...document.querySelectorAll('[data-target]')];let active=0;
  function show(n){if(!slides.length)return;active=(n+slides.length)%slides.length;slides.forEach((s,i)=>{s.classList.toggle('active',i===active);s.setAttribute('aria-hidden',String(i!==active))});dots.forEach((d,i)=>{d.classList.toggle('selected',i===active);d.setAttribute('aria-pressed',String(i===active))})}
  dots.forEach((d,i)=>d.addEventListener('click',()=>show(i)));
  document.querySelector('.hero-prev')?.addEventListener('click',()=>show(active-1));
  document.querySelector('.hero-next')?.addEventListener('click',()=>show(active+1));
  show(0);
  if(slides.length>1&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches)setInterval(()=>{if(!document.hidden)show(active+1)},7000);
  const filters=[...document.querySelectorAll('[data-news]')];
  const rows=[...document.querySelectorAll('.home-news-list .home-news-row')];
  const homeNews=document.querySelector('.home-news-list');
  const empty=document.createElement('p');
  empty.className='cms-news-filter-empty';
  empty.textContent='該当する記事はありません。';
  empty.hidden=true;
  homeNews?.after(empty);
  function filterHomeNews(category){
    let shown=0;
    rows.forEach(row=>{
      const groups=(row.dataset.category||'').split(/\s+/);
      const match=category==='all'||groups.includes(category);
      const visible=match&&shown<5;
      row.hidden=!visible;
      if(visible)shown++;
    });
    empty.hidden=shown!==0;
  }
  filters.forEach(btn=>btn.addEventListener('click',()=>{
    filters.forEach(b=>{b.classList.toggle('active',b===btn);b.setAttribute('aria-pressed',String(b===btn))});
    filterHomeNews(btn.dataset.news);
  }));
  if(rows.length)filterHomeNews(document.querySelector('[data-news].active')?.dataset.news||'all');
})();

// CMS research-facility carousel. Independent of the NEWS and hero controls.
(()=>{
  const carousel=document.querySelector('.cms-facility-slider');
  if(!carousel)return;
  const slides=[...carousel.querySelectorAll('.cms-facility-slide')];
  const dots=[...carousel.querySelectorAll('.cms-facility-dot')];
  if(!slides.length)return;
  let current=Math.max(0,slides.findIndex(slide=>slide.classList.contains('is-active')));
  function show(index){
    current=(index+slides.length)%slides.length;
    slides.forEach((slide,i)=>{
      const active=i===current;
      slide.classList.toggle('is-active',active);
      slide.setAttribute('aria-hidden',String(!active));
      slide.hidden=!active;
      slide.tabIndex=active?0:-1;
    });
    dots.forEach((dot,i)=>{
      const active=i===current;
      dot.classList.toggle('is-active',active);
      dot.setAttribute('aria-pressed',String(active));
    });
  }
  // Ensure hidden slides remain hidden even if a layout CSS rule sets display:grid.
  if(!document.getElementById('cms-facility-slide-visibility')){
    const style=document.createElement('style');
    style.id='cms-facility-slide-visibility';
    style.textContent='.cms-facility-slide[hidden]{display:none!important}';
    document.head.append(style);
  }
  carousel.querySelector('.cms-facility-prev')?.addEventListener('click',()=>show(current-1));
  carousel.querySelector('.cms-facility-next')?.addEventListener('click',()=>show(current+1));
  dots.forEach((dot,i)=>dot.addEventListener('click',()=>show(Number(dot.dataset.index??i))));
  show(current);
  if(slides.length>1&&!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
    setInterval(()=>{if(!document.hidden)show(current+1)},7000);
  }
})();
