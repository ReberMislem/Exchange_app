// theme toggling & sidebar behavior
document.addEventListener('DOMContentLoaded', function(){
  const root = document.documentElement;
  const stored = localStorage.getItem('theme') || 'light';
  if(stored === 'dark') document.documentElement.setAttribute('data-theme','dark');
  
  // Update icon based on theme
  function updateThemeIcon() {
    const toggles = document.querySelectorAll('.theme-toggle');
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const iconClass = isDark ? 'bi-sun' : 'bi-moon-stars';
    
    toggles.forEach(btn => {
      const icon = btn.querySelector('i');
      if (icon) {
        icon.className = 'bi ' + iconClass;
      }
    });
  }

  // Set initial icon
  updateThemeIcon();

  // toggle button
  const toggles = document.querySelectorAll('.theme-toggle');
  toggles.forEach(btn => btn.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    if(next === 'dark') document.documentElement.setAttribute('data-theme','dark'); else document.documentElement.removeAttribute('data-theme');
    localStorage.setItem('theme', next);
    updateThemeIcon();
    
    // Add animation effect when toggling theme
    document.body.classList.add('theme-transition');
    setTimeout(() => {
      document.body.classList.remove('theme-transition');
    }, 300);
  }));

  // sidebar open/close on mobile
  const sidebar = document.querySelector('.sidebar');
  const openBtn = document.getElementById('sidebarOpen');
  const closeBtn = document.getElementById('sidebarClose');
  const overlay = document.querySelector('.content-overlay');
  
  if(openBtn){
    openBtn.addEventListener('click', ()=>{ 
      sidebar.classList.add('open'); 
      overlay.classList.add('show'); 
      // Add animation class
      sidebar.classList.add('slide-in');
    });
  }
  
  if(closeBtn){
    closeBtn.addEventListener('click', ()=>{ 
      sidebar.classList.remove('open'); 
      overlay.classList.remove('show'); 
      // Remove animation class
      sidebar.classList.remove('slide-in');
    });
  }
  
  if(overlay){
    overlay.addEventListener('click', ()=>{ 
      sidebar.classList.remove('open'); 
      overlay.classList.remove('show'); 
      // Remove animation class
      sidebar.classList.remove('slide-in');
    });
  }
  
  // Close sidebar when clicking on a nav link on mobile
  const navLinks = document.querySelectorAll('.sidebar .nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 992) {
        sidebar.classList.remove('open');
        overlay.classList.remove('show');
        // Remove animation class
        sidebar.classList.remove('slide-in');
      }
    });
  });
  
  // Add scroll animations
  function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    elements.forEach(element => {
      const elementPosition = element.getBoundingClientRect().top;
      const screenPosition = window.innerHeight / 1.3;
      
      if (elementPosition < screenPosition) {
        element.classList.add('visible');
      }
    });
  }
  
  // Trigger animations on scroll
  window.addEventListener('scroll', animateOnScroll);
  // Trigger once on page load
  animateOnScroll();
  
  // Add hover effects to cards
  const cards = document.querySelectorAll('.card');
  cards.forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.classList.add('hovered');
    });
    
    card.addEventListener('mouseleave', () => {
      card.classList.remove('hovered');
    });
  });
  
  // Add ripple effect to buttons
  const buttons = document.querySelectorAll('.btn');
  buttons.forEach(button => {
    button.addEventListener('click', function(e) {
      // Remove any existing ripple elements
      const existingRipple = this.querySelector('.ripple');
      if (existingRipple) {
        existingRipple.remove();
      }
      
      // Create ripple element
      const ripple = document.createElement('span');
      ripple.classList.add('ripple');
      
      // Position ripple
      const rect = this.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      const x = e.clientX - rect.left - size / 2;
      const y = e.clientY - rect.top - size / 2;
      
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = x + 'px';
      ripple.style.top = y + 'px';
      
      this.appendChild(ripple);
      
      // Remove ripple after animation completes
      setTimeout(() => {
        ripple.remove();
      }, 600);
    });
  });
});