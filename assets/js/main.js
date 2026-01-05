document.addEventListener('DOMContentLoaded', () => {
    // Typing Animation for Hero Title
    const typingElement = document.getElementById('typing-text');
    const textLines = [
        'Hi there',
        "I'm Yu-ki =:)"
    ];
    
    let lineIndex = 0;
    let charIndex = 0;
    let currentText = '';
    
    function typeText() {
        if (lineIndex < textLines.length) {
            if (charIndex < textLines[lineIndex].length) {
                currentText += textLines[lineIndex][charIndex];
                typingElement.innerHTML = currentText.replace(/\n/g, '<br>');
                charIndex++;
                setTimeout(typeText, 80); // Typing speed (80ms per character)
            } else {
                // Move to next line
                lineIndex++;
                charIndex = 0;
                if (lineIndex < textLines.length) {
                    currentText += '\n';
                    setTimeout(typeText, 300); // Pause between lines
                }
            }
        }
    }
    
    // Start typing after a short delay
    setTimeout(typeText, 500);

    // Biitsz Character Interaction
    const biitsz = document.querySelector('.biitsz-img');
    const bubble = document.querySelector('.speech-bubble');
    
    const messages = [
        'ようこそ！',
        'ゆっくりしていってね',
        'びっつだよ =:)',
    ];
    
    let currentMessageIndex = 0;
    
    function showMessage(message) {
        if (bubble) {
            bubble.textContent = message;
            bubble.classList.add('show');
            setTimeout(() => {
                bubble.classList.remove('show');
            }, 3000); // Show for 3 seconds
        }
    }
    
    // Auto-show messages on interval
    function autoShowMessages() {
        showMessage(messages[currentMessageIndex]);
        currentMessageIndex = (currentMessageIndex + 1) % messages.length;
    }
    
    // Show first message after 1 second
    setTimeout(autoShowMessages, 1000);
    
    // Then show new message every 8 seconds
    setInterval(autoShowMessages, 8000);
    
    // Also allow clicking for immediate message change
    if (biitsz) {
        biitsz.addEventListener('click', () => {
            const randomMessage = messages[Math.floor(Math.random() * messages.length)];
            showMessage(randomMessage);
        });
    }

    // Section Title Typing Animation on Scroll
    const sectionTitles = document.querySelectorAll('.section-title[data-typing]');
    const typedTitles = new Set(); // Track which titles have been typed
    
    function typeSectionTitle(element) {
        const text = element.getAttribute('data-typing');
        if (!text || typedTitles.has(element)) return; // Skip if already typed
        
        typedTitles.add(element);
        let charIndex = 0;
        
        function typeChar() {
            if (charIndex < text.length) {
                element.textContent += text[charIndex];
                charIndex++;
                setTimeout(typeChar, 80); // 80ms per character
            } else {
                // Animation Complete
                if (element.id === 'events-title') {
                    const mapContainer = document.querySelector('.map-container');
                    const explanation = document.getElementById('events-explanation');
                    
                    setTimeout(() => {
                        if (explanation) explanation.classList.add('visible');
                        if (mapContainer) mapContainer.classList.add('visible');
                    }, 400); // Wait 0.4s after typing
                }
            }
        }
        
        typeChar();
    }
    
    // Intersection Observer to trigger typing when section comes into view
    const observerOptions = {
        threshold: 0.3, // Trigger when 30% of the element is visible
        rootMargin: '0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                typeSectionTitle(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all section titles
    sectionTitles.forEach(title => {
        observer.observe(title);
    });

    // Fade In Up Observer (Scroll Animations)
    const fadeElements = document.querySelectorAll('.fade-in-up:not(.map-container):not(.manual-trigger), .stagger-grid');
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });
    
    fadeElements.forEach(el => fadeObserver.observe(el));

    // Smooth Scrolling for Anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // Active Navigation Highlighting (Optional simple version)
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('nav ul li a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            if (pageYOffset >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href').includes(current)) {
                link.classList.add('active');
            }
        });
    });

    // Theme Toggle
    const toggleBtn = document.getElementById('theme-toggle');
    const body = document.body;
    
    // Check saved preference
    const currentTheme = localStorage.getItem('theme');
    if (currentTheme === 'light') {
        body.classList.add('light-mode');
        toggleBtn.textContent = '☾'; // Moon for light mode (to switch back to dark)
    } else {
        toggleBtn.textContent = '☀'; // Sun for dark mode (to switch to light)
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            body.classList.toggle('light-mode');
            
            // Save preference
            let theme = 'dark';
            if (body.classList.contains('light-mode')) {
                theme = 'light';
                toggleBtn.textContent = '☾';
            } else {
                toggleBtn.textContent = '☀';
            }
            localStorage.setItem('theme', theme);
        });
    }

    // Hamburger Menu Logic
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    const navLinksList = document.querySelectorAll('.nav-menu a');

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            navMenu.classList.toggle('active');
        });

        // Close menu when link is clicked
        navLinksList.forEach(link => {
            link.addEventListener('click', () => {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
    }
});
