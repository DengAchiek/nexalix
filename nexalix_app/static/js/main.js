document.addEventListener("DOMContentLoaded", () => {
    if (window.__nexalixMainInitialized) return;
    window.__nexalixMainInitialized = true;

    const body = document.body;
    const siteHeader = document.getElementById("siteHeader");
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const mobileMenu = document.getElementById("mobileMenu");
    const mobileMenuOverlay = document.getElementById("mobileMenuOverlay");
    const uxEventUrl = body?.dataset.uxEventUrl || "";
    let lastSearchTracked = "";

    const getCsrfToken = () => {
        const cookieValue = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith("csrftoken="));
        return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
    };

    const trackEvent = (eventType, label = "", metadata = {}) => {
        if (!uxEventUrl || !eventType) return;

        const payload = {
            event_type: eventType,
            label: String(label || "").slice(0, 120),
            metadata,
            page_path: window.location.pathname,
        };

        fetch(uxEventUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            credentials: "same-origin",
            keepalive: true,
            body: JSON.stringify(payload),
        }).catch(() => {});
    };

    window.nxTrackEvent = trackEvent;

    const fallbackSearchData = [
        { title: "Home", description: "Company overview and featured solutions", url: "/", category: "Page", keywords: ["home"] },
        { title: "About", description: "Vision, mission, and core values", url: "/about/", category: "Page", keywords: ["company"] },
        { title: "Services", description: "Technology and consulting offerings", url: "/services/", category: "Page", keywords: ["solutions"] },
        { title: "Auto Quote", description: "Generate a live project cost estimate", url: "/quote-generator/", category: "Page", keywords: ["pricing", "quote"] },
        { title: "Industries", description: "Sector-focused transformation work", url: "/industries/", category: "Page", keywords: ["sector"] },
        { title: "How We Work", description: "Delivery process and methodology", url: "/how_we_work/", category: "Page", keywords: ["delivery"] },
        { title: "Why Choose Us", description: "Differentiators and value proposition", url: "/why_choose_us/", category: "Page", keywords: ["advantages"] },
        { title: "Contact", description: "Get proposal and consultation support", url: "/contact/", category: "Page", keywords: ["email", "phone"] },
    ];

    const readSearchDataFromDom = () => {
        const scriptEl = document.getElementById("globalSearchIndexData");
        if (!scriptEl) return [];
        try {
            const parsed = JSON.parse(scriptEl.textContent || "[]");
            if (!Array.isArray(parsed)) return [];
            return parsed.map((item) => ({
                title: String(item.title || "").trim().slice(0, 120),
                description: String(item.description || "").trim().slice(0, 220),
                url: String(item.url || "").trim() || "/",
                category: String(item.category || "Page").trim().slice(0, 40),
                keywords: Array.isArray(item.keywords)
                    ? item.keywords.map((kw) => String(kw || "").trim().toLowerCase()).filter(Boolean).slice(0, 12)
                    : [],
            })).filter((item) => item.title && item.url);
        } catch (_err) {
            return [];
        }
    };

    const searchData = (() => {
        const dynamicData = readSearchDataFromDom();
        return dynamicData.length ? dynamicData : fallbackSearchData;
    })();

    function setActiveNavLink() {
        const currentPath = window.location.pathname;
        const navSelectors = [".nav-links a", ".mobile-menu-links a"];

        navSelectors.forEach((selector) => {
            document.querySelectorAll(selector).forEach((link) => {
                const linkPath = new URL(link.href, window.location.origin).pathname;
                const isActive = currentPath === linkPath || (linkPath !== "/" && currentPath.startsWith(linkPath));
                link.classList.toggle("active", isActive);
                if (isActive && selector === ".mobile-menu-links a") {
                    link.setAttribute("aria-current", "page");
                }
            });
        });
    }

    function handleHeaderScroll() {
        if (!siteHeader) return;
        siteHeader.classList.toggle("scrolled", window.scrollY > 12);
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

        mobileMenuBtn.addEventListener("click", () => {
            const isOpening = !mobileMenu.classList.contains("active");
            trackEvent("cta_click", isOpening ? "mobile_menu_open" : "mobile_menu_close");
            toggleMobileMenu();
        });
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

        container.innerHTML = results.map((result, idx) => {
            return `
                <a href="${result.url}" class="search-result-item" data-result-index="${idx}" data-result-title="${result.title}">
                    <div class="result-title">${result.title}</div>
                    <div class="result-description">${result.description}</div>
                    <div class="result-tag">${result.category}</div>
                </a>
            `;
        }).join("");

        container.classList.add("active");
    }

    function scoreSearchResult(item, query, queryTerms) {
        const title = item.title.toLowerCase();
        const description = item.description.toLowerCase();
        const category = item.category.toLowerCase();
        const keywords = (item.keywords || []).join(" ").toLowerCase();
        let score = 0;

        if (title.startsWith(query)) score += 8;
        if (title.includes(query)) score += 5;
        if (description.includes(query)) score += 2;
        if (category.includes(query)) score += 1;
        if (keywords.includes(query)) score += 3;

        queryTerms.forEach((term) => {
            if (title.includes(term)) score += 2;
            if (description.includes(term)) score += 1;
            if (keywords.includes(term)) score += 1;
        });

        return score;
    }

    function wireSearch(inputId, resultsId) {
        const input = document.getElementById(inputId);
        const resultsContainer = document.getElementById(resultsId);
        if (!input || !resultsContainer) return;

        let latestResults = [];

        input.addEventListener("input", () => {
            const query = input.value.trim().toLowerCase();
            if (query.length < 2) {
                resultsContainer.classList.remove("active");
                resultsContainer.innerHTML = "";
                latestResults = [];
                return;
            }

            const queryTerms = query.split(/\s+/).filter(Boolean).slice(0, 5);

            const results = searchData
                .map((item) => ({ ...item, _score: scoreSearchResult(item, query, queryTerms) }))
                .filter((item) => item._score > 0)
                .sort((a, b) => b._score - a._score)
                .slice(0, 7)
                .map((item) => {
                    const cleaned = { ...item };
                    delete cleaned._score;
                    return cleaned;
                });

            latestResults = results;
            displaySearchResults(results, resultsContainer);

            if (query !== lastSearchTracked) {
                trackEvent("search_query", query, { source: inputId, results: results.length });
                lastSearchTracked = query;
            }
        });

        input.addEventListener("focus", () => {
            if (resultsContainer.innerHTML) resultsContainer.classList.add("active");
        });

        input.addEventListener("keydown", (event) => {
            if (event.key !== "Enter") return;
            if (!latestResults.length) return;
            event.preventDefault();
            const firstResult = latestResults[0];
            trackEvent("search_result_click", firstResult.title, { source: inputId, position: 1, href: firstResult.url });
            window.location.href = firstResult.url;
        });

        resultsContainer.addEventListener("click", (event) => {
            const link = event.target.closest(".search-result-item");
            if (!link) return;
            trackEvent("search_result_click", link.dataset.resultTitle || "", {
                source: inputId,
                position: Number.parseInt(link.dataset.resultIndex || "0", 10) + 1,
                href: link.getAttribute("href") || "",
            });
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
            ".quote-form-card", ".quote-summary-card", ".project-completed-card",
            ".partner-home-card", ".portfolio-card", ".industry-modern-card",
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
            trackEvent("cta_click", "back_to_top");
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
            trackEvent("cta_click", next ? "tech_show_less" : "tech_show_more");
        });
    }

    function wireFormValidation() {
        const forms = [
            document.querySelector(".contact-form form"),
            document.getElementById("quoteForm"),
        ].filter(Boolean);

        const validateField = (field) => {
            if (!field || !("checkValidity" in field)) return true;
            const valid = field.checkValidity();
            field.classList.toggle("field-invalid", !valid);
            field.setAttribute("aria-invalid", String(!valid));
            return valid;
        };

        forms.forEach((form) => {
            const fields = Array.from(form.querySelectorAll("input, select, textarea"));
            fields.forEach((field) => {
                field.addEventListener("blur", () => validateField(field));
                field.addEventListener("input", () => {
                    if (field.classList.contains("field-invalid")) validateField(field);
                });
            });

            form.addEventListener("submit", () => {
                fields.forEach((field) => validateField(field));
                const formType = form.id === "quoteForm" ? "quote_form_submit" : "contact_form_submit";
                trackEvent(formType, "submit", { form_id: form.id || "contact_form" });
            });
        });

        const successBanner = document.querySelector(".form-message.success");
        if (successBanner) {
            trackEvent("cta_click", "form_submission_success", { page: window.location.pathname });
        }
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
                promise.catch(() => {});
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
                maximumFractionDigits: 0,
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

    function wireMediaOptimization() {
        if ("loading" in HTMLImageElement.prototype) {
            document.querySelectorAll("img:not([loading])").forEach((img) => {
                if (img.classList.contains("brand-logo")) return;
                img.setAttribute("loading", "lazy");
            });
        }

        document.querySelectorAll("img").forEach((img) => {
            if (!img.getAttribute("decoding")) {
                img.setAttribute("decoding", "async");
            }
        });

        const sections = document.querySelectorAll(".site-main section");
        sections.forEach((section, index) => {
            if (index > 1) section.classList.add("deferred-section");
        });
    }

    function wireCtaTracking() {
        document.addEventListener("click", (event) => {
            const interactiveEl = event.target.closest("a, button");
            if (!interactiveEl) return;

            const isTrackable = interactiveEl.matches(
                ".btn, .header-cta, .nav-links a, .mobile-menu-links a, .nx-chat-link, .partner-home-card, .project-link-btn, .case-link"
            );
            if (!isTrackable) return;

            const label = (interactiveEl.textContent || interactiveEl.getAttribute("aria-label") || "cta")
                .replace(/\s+/g, " ")
                .trim()
                .slice(0, 120);

            trackEvent("cta_click", label || "cta_click", {
                href: interactiveEl.getAttribute("href") || "",
                class_name: interactiveEl.className || "",
            });
        });
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
    wireFormValidation();
    wireContactEnhancements();
    wireHeroVideo();
    wireQuoteCalculator();
    wireMediaOptimization();
    wireCtaTracking();

    window.addEventListener("scroll", handleHeaderScroll);
});
