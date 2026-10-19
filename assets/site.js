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
