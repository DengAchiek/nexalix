document.addEventListener("DOMContentLoaded", function () {

    
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileMenuOverlay = document.getElementById('mobileMenuOverlay');
    const mobileMenu = document.getElementById('mobileMenu');
    const body = document.body;

    function toggleMobileMenu() {
        mobileMenuBtn.classList.toggle('active');
        mobileMenuOverlay.classList.toggle('active');
        mobileMenu.classList.toggle('active');
        body.classList.toggle('menu-open');

        body.style.overflow = body.classList.contains('menu-open') ? 'hidden' : '';
    }

    if (mobileMenuBtn && mobileMenuOverlay) {
        mobileMenuBtn.addEventListener('click', toggleMobileMenu);
        mobileMenuOverlay.addEventListener('click', toggleMobileMenu);
    }

    // Close menu when clicking a link
    const mobileLinks = document.querySelectorAll('.mobile-menu-links a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', toggleMobileMenu);
    });

    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && body.classList.contains('menu-open')) {
            toggleMobileMenu();
        }
    });

    // Responsive behavior
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && body.classList.contains('menu-open')) {
            toggleMobileMenu();
        }
    });

    
    const video = document.querySelector(".hero-video");
    if (video) {
        video.muted = true;
        video.setAttribute("playsinline", "");
        video.play().catch(err => {
            console.log("Autoplay blocked:", err);
        });
    }

});

document.addEventListener("DOMContentLoaded", function() {
    // Stats counter animation
    const counters = document.querySelectorAll('.stat-item h3');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-count'));
                const increment = target / 100;
                let current = 0;
                
                const timer = setInterval(() => {
                    current += increment;
                    if (current > target) {
                        counter.textContent = target + (counter.getAttribute('data-count') === '98' ? '%' : '+');
                        clearInterval(timer);
                    } else {
                        counter.textContent = Math.floor(current) + (counter.getAttribute('data-count') === '98' ? '%' : '+');
                    }
                }, 20);
                
                observer.unobserve(counter);
            }
        });
    }, { threshold: 0.5 });
    
    counters.forEach(counter => observer.observe(counter));
    
    // Partners marquee animation
    const partnersTrack = document.querySelector('.partners-track');
    if (partnersTrack) {
        let animationId;
        let position = 0;
        
        function animateMarquee() {
            position -= 1;
            if (position <= -partnersTrack.scrollWidth / 2) {
                position = 0;
            }
            partnersTrack.style.transform = `translateX(${position}px)`;
            animationId = requestAnimationFrame(animateMarquee);
        }
        
        const marqueeObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                animationId = requestAnimationFrame(animateMarquee);
            } else {
                cancelAnimationFrame(animationId);
            }
        });
        
        marqueeObserver.observe(document.querySelector('.partners-marquee'));
    }
});
