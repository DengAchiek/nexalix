document.addEventListener("DOMContentLoaded", () => {
    if (window.__nexalixMainInitialized) return;
    window.__nexalixMainInitialized = true;

    const body = document.body;
    const siteHeader = document.getElementById("siteHeader");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const mobileMenu = document.getElementById("mobileMenu");
    const mobileMenuOverlay = document.getElementById("mobileMenuOverlay");

    const searchData = [
        { title: "Home", description: "Company overview and featured solutions", url: "/", category: "Page" },
        { title: "About", description: "Vision, mission, and core values", url: "/about/", category: "Page" },
        { title: "Services", description: "Technology and consulting offerings", url: "/services/", category: "Page" },
        { title: "Auto Quote", description: "Generate a live project cost estimate", url: "/quote-generator/", category: "Page" },
        { title: "Industries", description: "Sector-focused transformation work", url: "/industries/", category: "Page" },
        { title: "How We Work", description: "Delivery process and methodology", url: "/how_we_work/", category: "Page" },
        { title: "Why Choose Us", description: "Differentiators and value proposition", url: "/why_choose_us/", category: "Page" },
        { title: "Contact", description: "Get proposal and consultation support", url: "/contact/", category: "Page" },
        { title: "Web Development", description: "Scalable web platforms and portals", url: "/web_dev/", category: "Service" },
        { title: "Mobile Apps", description: "Cross-platform app engineering", url: "/mobile_app/", category: "Service" },
        { title: "Cloud Solutions", description: "Migration, infrastructure, and optimization", url: "/cloud/", category: "Service" },
        { title: "Digital Marketing", description: "Growth strategy and demand generation", url: "/digital_marketing/", category: "Service" },
        { title: "SEO", description: "Search visibility and technical optimization", url: "/seo/", category: "Service" },
        { title: "IT Consulting", description: "Strategic advisory and architecture", url: "/it_consult/", category: "Service" },
        { title: "AI Training", description: "Upskilling teams for AI adoption", url: "/ai_training/", category: "Service" }
    ];

    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        document.querySelectorAll(".nav-links a").forEach((link) => {
            const linkPath = new URL(link.href).pathname;
            if (currentPath === linkPath || (linkPath !== "/" && currentPath.startsWith(linkPath))) {
                link.classList.add("active");
            }
        });
    }

    function handleHeaderScroll() {
        if (!siteHeader) return;
        if (window.scrollY > 12) {
            siteHeader.classList.add("scrolled");
        } else {
            siteHeader.classList.remove("scrolled");
        }
    }

    function toggleMobileMenu(forceState) {
        if (!mobileMenuBtn || !mobileMenu || !mobileMenuOverlay) return;

        const shouldOpen = typeof forceState === "boolean" ? forceState : !mobileMenu.classList.contains("active");

        mobileMenuBtn.classList.toggle("active", shouldOpen);
        mobileMenu.classList.toggle("active", shouldOpen);
        mobileMenuOverlay.classList.toggle("active", shouldOpen);
        body.style.overflow = shouldOpen ? "hidden" : "";
    }

    function wireMobileMenu() {
        if (!mobileMenuBtn || !mobileMenu || !mobileMenuOverlay) return;

        mobileMenuBtn.addEventListener("click", () => toggleMobileMenu());
        mobileMenuOverlay.addEventListener("click", () => toggleMobileMenu(false));

        document.querySelectorAll(".mobile-menu-links a").forEach((link) => {
            link.addEventListener("click", () => toggleMobileMenu(false));
        });

        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") toggleMobileMenu(false);
        });

        window.addEventListener("resize", () => {
            if (window.innerWidth > 1120) toggleMobileMenu(false);
        });
    }

    function displaySearchResults(results, container) {
        if (!container) return;

        if (!results.length) {
            container.innerHTML = '<div class="no-results">No results found. Try a different keyword.</div>';
            container.classList.add("active");
            return;
        }

        container.innerHTML = results.map((result) => {
            return `
                <a href="${result.url}" class="search-result-item">
                    <div class="result-title">${result.title}</div>
                    <div class="result-description">${result.description}</div>
                    <div class="result-tag">${result.category}</div>
                </a>
            `;
        }).join("");

        container.classList.add("active");
    }

    function wireSearch(inputId, resultsId) {
        const input = document.getElementById(inputId);
        const resultsContainer = document.getElementById(resultsId);
        if (!input || !resultsContainer) return;

        input.addEventListener("input", () => {
            const query = input.value.trim().toLowerCase();
            if (query.length < 2) {
                resultsContainer.classList.remove("active");
                resultsContainer.innerHTML = "";
                return;
            }

            const results = searchData.filter((item) => {
                return item.title.toLowerCase().includes(query)
                    || item.description.toLowerCase().includes(query)
                    || item.category.toLowerCase().includes(query);
            }).slice(0, 7);

            displaySearchResults(results, resultsContainer);
        });

        input.addEventListener("focus", () => {
            if (resultsContainer.innerHTML) resultsContainer.classList.add("active");
        });
    }

    function wireSearchClose() {
        document.addEventListener("click", (event) => {
            const isSearchClick = event.target.closest(".search-shell");
            if (isSearchClick) return;

            document.querySelectorAll(".search-results").forEach((resultsContainer) => {
                resultsContainer.classList.remove("active");
            });
        });
    }

    function animateCounter(element) {
        const target = Number.parseInt(element.dataset.count || "0", 10);
        if (!target || Number.isNaN(target)) return;

        const suffix = element.dataset.suffix || "";
        const duration = 1200;
        const startTime = performance.now();

        function update(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            element.textContent = `${Math.floor(target * eased)}${suffix}`;
            if (progress < 1) requestAnimationFrame(update);
        }

        requestAnimationFrame(update);
    }

    function wireCounters() {
        const counters = document.querySelectorAll("[data-count]");
        if (!counters.length || !("IntersectionObserver" in window)) return;

        const observer = new IntersectionObserver((entries, currentObserver) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                animateCounter(entry.target);
                currentObserver.unobserve(entry.target);
            });
        }, { threshold: 0.45 });

        counters.forEach((counter) => observer.observe(counter));
    }

    function wireRevealAnimation() {
        const selectors = [
            ".about-section", ".value-card", ".work-step", ".advantage", ".industry-card",
            ".service-card", ".case-card", ".blog-card", ".stat-card", ".partner-card",
            ".award-card", ".pricing-plan-card", ".step-card", ".contact-form",
            ".quote-form-card", ".quote-summary-card"
        ];

        const elements = document.querySelectorAll(selectors.join(","));
        if (!elements.length) return;

        elements.forEach((element) => element.setAttribute("data-reveal", ""));

        if (!("IntersectionObserver" in window)) {
            elements.forEach((element) => element.classList.add("revealed"));
            return;
        }

        const observer = new IntersectionObserver((entries, currentObserver) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add("revealed");
                currentObserver.unobserve(entry.target);
            });
        }, { threshold: 0.18 });

        elements.forEach((element) => observer.observe(element));
    }

    function wireBackToTop() {
        const backToTop = document.getElementById("backToTop");
        if (!backToTop) return;

        backToTop.addEventListener("click", (event) => {
            event.preventDefault();
            window.scrollTo({ top: 0, behavior: "smooth" });
        });
    }

    function wireTechToggle() {
        const toggleBtn = document.getElementById("techToggle");
        const techCloud = document.getElementById("techCloud");
        if (!toggleBtn || !techCloud) return;

        toggleBtn.addEventListener("click", () => {
            const isExpanded = toggleBtn.dataset.expanded === "true";
            const next = !isExpanded;
            techCloud.classList.toggle("expanded", next);
            toggleBtn.dataset.expanded = String(next);
            toggleBtn.textContent = next ? "Show Less" : "Show More";
        });
    }

    function wireContactEnhancements() {
        const messageField = document.getElementById("message");
        const form = document.querySelector(".contact-form form");
        if (!form) return;

        if (messageField) {
            const counter = document.createElement("small");
            counter.className = "contact-privacy";
            counter.style.marginTop = "6px";
            messageField.insertAdjacentElement("afterend", counter);

            const updateCounter = () => {
                counter.textContent = `${messageField.value.length}/1000 characters`;
            };

            messageField.setAttribute("maxlength", "1000");
            messageField.addEventListener("input", updateCounter);
            updateCounter();
        }

        form.addEventListener("submit", () => {
            const button = form.querySelector("button[type='submit']");
            if (!button) return;
            button.disabled = true;
            button.textContent = "Sending...";
        });
    }

    function wireHeroVideo() {
        const video = document.getElementById("homeHeroVideo") || document.querySelector(".hero-video");
        if (!video) return;

        // Keep autoplay compatible across modern browsers (especially Safari/iOS).
        video.muted = true;
        video.defaultMuted = true;
        video.autoplay = true;
        video.loop = true;
        video.playsInline = true;
        video.setAttribute("muted", "");
        video.setAttribute("autoplay", "");
        video.setAttribute("loop", "");
        video.setAttribute("playsinline", "");
        video.setAttribute("webkit-playsinline", "");

        const tryPlay = () => {
            const promise = video.play();
            if (promise && typeof promise.catch === "function") {
                promise.catch(() => {
                    // Retry after first interaction if autoplay is temporarily blocked.
                });
            }
        };

        if (video.readyState >= 2) {
            tryPlay();
        } else {
            video.addEventListener("loadeddata", tryPlay, { once: true });
            video.addEventListener("canplay", tryPlay, { once: true });
        }

        document.addEventListener("visibilitychange", () => {
            if (!document.hidden && video.paused) tryPlay();
        });

        window.addEventListener("focus", () => {
            if (video.paused) tryPlay();
        });

        window.addEventListener("pointerdown", () => {
            if (video.paused) tryPlay();
        }, { once: true });
    }

    function wireQuoteCalculator() {
        const form = document.getElementById("quoteForm");
        if (!form) return;

        const serviceSelect = document.getElementById("service");
        const complexitySelect = document.getElementById("complexity");
        const timelineSelect = document.getElementById("timeline");
        const supportSelect = document.getElementById("support_plan");
        const addonInputs = form.querySelectorAll("input[name='addons']");

        const quoteBase = document.getElementById("quoteBase");
        const quoteAddons = document.getElementById("quoteAddons");
        const quoteSupport = document.getElementById("quoteSupport");
        const quoteTotal = document.getElementById("quoteTotal");
        const quoteRange = document.getElementById("quoteRange");
        const quoteWeeks = document.getElementById("quoteWeeks");

        if (!serviceSelect || !complexitySelect || !timelineSelect || !supportSelect) return;

        const formatUSD = (value) => {
            return new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0
            }).format(value);
        };

        const toNumber = (value) => {
            const numeric = Number.parseFloat(value);
            return Number.isFinite(numeric) ? numeric : 0;
        };

        const calculate = () => {
            const selectedService = serviceSelect.options[serviceSelect.selectedIndex];
            const selectedComplexity = complexitySelect.options[complexitySelect.selectedIndex];
            const selectedTimeline = timelineSelect.options[timelineSelect.selectedIndex];
            const selectedSupport = supportSelect.options[supportSelect.selectedIndex];

            const basePrice = toNumber(selectedService?.dataset.basePrice || "0");
            const baseWeeks = toNumber(selectedService?.dataset.weeks || "0");
            const complexityMultiplier = toNumber(selectedComplexity?.dataset.multiplier || "1");
            const complexityWeeksMultiplier = toNumber(selectedComplexity?.dataset.weeksMultiplier || "1");
            const timelineMultiplier = toNumber(selectedTimeline?.dataset.multiplier || "1");
            const timelineWeeksMultiplier = toNumber(selectedTimeline?.dataset.weeksMultiplier || "1");
            const supportRate = toNumber(selectedSupport?.dataset.rate || "0");

            const coreBuild = basePrice * complexityMultiplier * timelineMultiplier;
            const addonsTotal = Array.from(addonInputs).reduce((sum, input) => {
                if (!input.checked) return sum;
                return sum + toNumber(input.dataset.addonPrice || "0");
            }, 0);
            const supportTotal = coreBuild * supportRate;
            const total = coreBuild + addonsTotal + supportTotal;
            const minEstimate = total * 0.9;
            const maxEstimate = total * 1.1;

            let weeks = 0;
            if (baseWeeks > 0) {
                weeks = Math.max(2, Math.ceil(baseWeeks * complexityWeeksMultiplier * timelineWeeksMultiplier));
            }

            if (quoteBase) quoteBase.textContent = formatUSD(coreBuild);
            if (quoteAddons) quoteAddons.textContent = formatUSD(addonsTotal);
            if (quoteSupport) quoteSupport.textContent = formatUSD(supportTotal);
            if (quoteTotal) quoteTotal.textContent = formatUSD(total);
            if (quoteRange) quoteRange.textContent = `${formatUSD(minEstimate)} - ${formatUSD(maxEstimate)}`;
            if (quoteWeeks) quoteWeeks.textContent = weeks ? `~${weeks} weeks` : "~0 weeks";
        };

        form.addEventListener("input", calculate);
        form.addEventListener("change", calculate);
        calculate();
    }

    setActiveNavLink();
    handleHeaderScroll();
    wireMobileMenu();
    wireSearch("desktopSearch", "desktopSearchResults");
    wireSearch("mobileSearch", "mobileSearchResults");
    wireSearchClose();
    wireCounters();
    wireRevealAnimation();
    wireBackToTop();
    wireTechToggle();
    wireContactEnhancements();
    wireHeroVideo();
    wireQuoteCalculator();

    window.addEventListener("scroll", handleHeaderScroll);
});
