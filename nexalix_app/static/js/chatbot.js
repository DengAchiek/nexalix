document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("nxChatbot");
    if (!root || window.__nexalixChatbotInitialized) return;
    window.__nexalixChatbotInitialized = true;

    const launcher = document.getElementById("nxChatLauncher");
    const panel = document.getElementById("nxChatPanel");
    const closeBtn = document.getElementById("nxChatClose");
    const messages = document.getElementById("nxChatMessages");
    const form = document.getElementById("nxChatForm");
    const input = document.getElementById("nxChatInput");
    const sendBtn = document.getElementById("nxChatSend");
    const quickRepliesWrap = document.getElementById("nxQuickReplies");

    const leadForm = document.getElementById("nxLeadForm");
    const leadSubmit = document.getElementById("nxLeadSubmit");

    const endpoints = {
        message: root.dataset.messageUrl,
        lead: root.dataset.leadUrl,
        contact: root.dataset.contactUrl,
        quote: root.dataset.quoteUrl,
    };

    const trackEvent = typeof window.nxTrackEvent === "function" ? window.nxTrackEvent : () => {};

    const state = {
        recommendedServices: [],
        lastAssistantMessage: "",
    };

    const quickReplies = [
        "What services does Nexalix offer?",
        "Can I get a quote?",
        "How do I start a project?",
        "I want to talk to a human",
    ];

    const getCsrfToken = () => {
        const cookieValue = document.cookie
            .split(";")
            .map((item) => item.trim())
            .find((item) => item.startsWith("csrftoken="));
        return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
    };

    const appendMessage = (text, role = "assistant") => {
        if (!messages) return;
        const item = document.createElement("article");
        item.className = `nx-chat-msg ${role === "user" ? "nx-chat-msg-user" : "nx-chat-msg-assistant"}`;
        item.textContent = text;
        messages.appendChild(item);
        messages.scrollTop = messages.scrollHeight;
    };

    const showLeadForm = (visible) => {
        if (!leadForm) return;
        leadForm.classList.toggle("visible", visible);
    };

    const setActions = ({ contactUrl, quoteUrl, whatsappUrl }) => {
        const links = root.querySelectorAll(".nx-chat-link");
        if (!links.length) return;
        if (links[0] && quoteUrl) links[0].href = quoteUrl;
        if (links[1] && contactUrl) links[1].href = contactUrl;
        if (links[2] && whatsappUrl) links[2].href = whatsappUrl;
    };

    const showErrorInLeadForm = (message) => {
        if (!leadForm) return;
        leadForm.querySelectorAll(".nx-chat-error").forEach((el) => el.remove());
        if (!message) return;

        const error = document.createElement("div");
        error.className = "nx-chat-error";
        error.textContent = message;
        leadForm.insertBefore(error, leadForm.firstChild.nextSibling);
    };

    const sendMessage = async (message) => {
        const response = await fetch(endpoints.message, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ message }),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok) {
            const messageText = data.error || "Unable to process your request right now.";
            throw new Error(messageText);
        }
        return data;
    };

    const submitLead = async (payload) => {
        const response = await fetch(endpoints.lead, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify(payload),
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok || !data.ok) {
            const messageText = data.error || "Could not submit your details right now.";
            throw new Error(messageText);
        }
        return data;
    };

    const renderQuickReplies = () => {
        if (!quickRepliesWrap) return;
        quickRepliesWrap.innerHTML = quickReplies.map((question) => (
            `<button type="button" class="nx-quick-reply" data-question="${question.replace(/"/g, "&quot;")}">${question}</button>`
        )).join("");
    };

    const handleUserMessage = async (text) => {
        const trimmed = (text || "").trim();
        if (!trimmed) return;

        appendMessage(trimmed, "user");
        trackEvent("chat_message_sent", trimmed.slice(0, 100), { source: "chat_widget" });
        if (input) input.value = "";
        if (sendBtn) {
            sendBtn.disabled = true;
            sendBtn.textContent = "Sending...";
        }

        try {
            const data = await sendMessage(trimmed);
            state.lastAssistantMessage = data.answer || "";
            state.recommendedServices = Array.isArray(data.recommended_services) ? data.recommended_services : [];

            appendMessage(data.answer || "Thanks for your message.", "assistant");
            if (state.recommendedServices.length) {
                appendMessage(`Recommended services: ${state.recommendedServices.join(", ")}`, "assistant");
            }
            if (data.escalation_message) {
                appendMessage(data.escalation_message, "assistant");
            }

            setActions({
                contactUrl: data.contact_url,
                quoteUrl: data.quote_url,
                whatsappUrl: data.whatsapp_url,
            });

            if (data.collect_lead || data.escalate_to_human) {
                showLeadForm(true);
                trackEvent("chat_lead_requested", "lead_form_shown");
                const serviceSelect = document.getElementById("nxLeadServiceInterest");
                if (serviceSelect && state.recommendedServices.length && !serviceSelect.value) {
                    const first = state.recommendedServices[0];
                    const hasOption = Array.from(serviceSelect.options).some((opt) => opt.value === first);
                    if (hasOption) serviceSelect.value = first;
                }
            }
        } catch (error) {
            appendMessage(error.message || "Could not send your message right now.", "assistant");
        } finally {
            if (sendBtn) {
                sendBtn.disabled = false;
                sendBtn.textContent = "Send";
            }
        }
    };

    renderQuickReplies();

    if (quickRepliesWrap) {
        quickRepliesWrap.addEventListener("click", (event) => {
            const btn = event.target.closest(".nx-quick-reply");
            if (!btn) return;
            const question = (btn.dataset.question || "").trim();
            if (!question) return;
            handleUserMessage(question);
        });
    }

    if (launcher && panel) {
        launcher.addEventListener("click", () => {
            const open = !root.classList.contains("open");
            root.classList.toggle("open", open);
            panel.setAttribute("aria-hidden", open ? "false" : "true");
            if (open && input) input.focus();
            if (open) trackEvent("chat_open", "widget_opened");
        });
    }

    if (closeBtn && panel) {
        closeBtn.addEventListener("click", () => {
            root.classList.remove("open");
            panel.setAttribute("aria-hidden", "true");
        });
    }

    if (form && input && sendBtn) {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            await handleUserMessage(input.value);
        });
    }

    if (leadForm && leadSubmit) {
        leadForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            showErrorInLeadForm("");

            const payload = {
                name: (document.getElementById("nxLeadName")?.value || "").trim(),
                full_name: (document.getElementById("nxLeadName")?.value || "").trim(),
                email: (document.getElementById("nxLeadEmail")?.value || "").trim(),
                phone: (document.getElementById("nxLeadPhone")?.value || "").trim(),
                company: (document.getElementById("nxLeadCompany")?.value || "").trim(),
                project_needs: (document.getElementById("nxLeadNeeds")?.value || "").trim(),
                project_description: (document.getElementById("nxLeadNeeds")?.value || "").trim(),
                service_interest:
                    (document.getElementById("nxLeadServiceInterest")?.value || "").trim()
                    || state.recommendedServices,
                assistant_summary: state.lastAssistantMessage,
                source_page: window.location.pathname,
                escalation_channel: "contact",
            };

            leadSubmit.disabled = true;
            leadSubmit.textContent = "Submitting...";

            try {
                const data = await submitLead(payload);
                appendMessage(data.message || "Thanks. We will contact you shortly.", "assistant");
                trackEvent("chat_lead_submitted", payload.service_interest || "unspecified");
                showLeadForm(false);
                leadForm.reset();
            } catch (error) {
                showErrorInLeadForm(error.message || "Could not submit your details.");
            } finally {
                leadSubmit.disabled = false;
                leadSubmit.textContent = "Submit details";
            }
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            root.classList.remove("open");
            if (panel) panel.setAttribute("aria-hidden", "true");
        }
    });
});
