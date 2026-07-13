COMPANY_PROFILE = {
    "name": "Nexalix",
    "description": (
        "Nexalix is a technology solutions company that helps businesses grow using modern digital systems. "
        "We specialize in software development, AI solutions, machine learning, data analytics, "
        "automation systems, and technology consulting."
    ),
    "industries": [
        "Healthcare",
        "Education",
        "Finance",
        "Retail",
        "Logistics",
        "Startups",
    ],
    "services": [
        "Software Development",
        "AI Solutions",
        "Machine Learning",
        "Data Analytics",
        "Automation Systems",
        "Technology Consulting",
    ],
}

CHATBOT_CONFIG = {
    "assistant_name": "Nexalix Virtual Assistant",
    "tone": "professional, clear, helpful, concise",
    "fallback_response": (
        "I can help with Nexalix services, solutions, consultations, and project inquiries. "
        "Could you tell me what service you are interested in?"
    ),
    "human_handoff_response": (
        "Sure - I can help connect you with a Nexalix advisor. "
        "Please share your name, email, and project need."
    ),
    "quote_response": (
        "Pricing depends on the scope, features, and complexity of your project. "
        "Please share your requirements so our team can prepare a customized quote."
    ),
}

INTENTS = [
    {
        "intent": "company_overview",
        "training_phrases": [
            "What does Nexalix do?",
            "Tell me about Nexalix",
            "Who are you?",
            "What services does Nexalix offer?",
        ],
        "response": COMPANY_PROFILE["description"],
    },
    {
        "intent": "industries_served",
        "training_phrases": [
            "What industries do you work with?",
            "Who do you serve?",
            "Which sectors does Nexalix support?",
        ],
        "response": (
            "Nexalix works with organizations across healthcare, education, finance, retail, "
            "logistics, and startups, helping them adopt modern technology solutions."
        ),
    },
    {
        "intent": "business_help",
        "training_phrases": [
            "How can Nexalix help my business?",
            "How do you support businesses?",
            "How can you help us grow?",
        ],
        "response": (
            "Nexalix helps businesses automate operations, analyze data, build custom software, "
            "and integrate AI-driven systems that improve productivity and support smarter decision-making."
        ),
    },
    {
        "intent": "custom_software",
        "training_phrases": [
            "Do you build custom software?",
            "Can you develop a system for my business?",
            "Do you create custom applications?",
        ],
        "response": (
            "Yes. Nexalix develops custom software tailored to business needs, including web platforms, "
            "enterprise systems, portals, and digital tools designed to improve workflow efficiency and support growth."
        ),
    },
    {
        "intent": "software_technologies",
        "training_phrases": [
            "What technologies do you use for software development?",
            "What stack do you use?",
            "Which tools do you develop with?",
        ],
        "response": (
            "Our development stack includes technologies such as Python, Django, JavaScript, React, APIs, "
            "cloud platforms, and database systems for scalable applications."
        ),
    },
    {
        "intent": "upgrade_existing_system",
        "training_phrases": [
            "Can you upgrade an existing system?",
            "Can you improve my current software?",
            "Do you modernize old systems?",
        ],
        "response": (
            "Absolutely. Nexalix can modernize legacy systems, improve performance, add features, "
            "and migrate applications to more efficient and scalable architectures."
        ),
    },
    {
        "intent": "ai_solutions",
        "training_phrases": [
            "Do you provide AI solutions?",
            "Can Nexalix build AI systems?",
            "Do you offer artificial intelligence services?",
        ],
        "response": (
            "Yes. Nexalix develops AI-powered systems that help businesses automate processes, "
            "analyze patterns, generate insights, and improve operational efficiency."
        ),
    },
    {
        "intent": "types_of_ai_systems",
        "training_phrases": [
            "What AI systems can you build?",
            "What type of AI solutions do you offer?",
            "Can you build chatbots or recommendation systems?",
        ],
        "response": (
            "We build AI solutions such as intelligent chatbots, predictive systems, recommendation engines, "
            "automated decision tools, and AI-driven data analysis platforms."
        ),
    },
    {
        "intent": "ai_business_value",
        "training_phrases": [
            "Can AI help my company?",
            "How does AI benefit a business?",
            "Why should I use AI?",
        ],
        "response": (
            "AI can help automate repetitive tasks, analyze large datasets, detect trends, "
            "predict outcomes, and improve customer engagement through intelligent systems."
        ),
    },
    {
        "intent": "machine_learning_explained",
        "training_phrases": [
            "What is machine learning?",
            "How can machine learning help my business?",
            "Explain machine learning services",
        ],
        "response": (
            "Machine learning allows systems to learn from data and make predictions without explicit programming. "
            "Businesses use it for forecasting, fraud detection, recommendation systems, and data-driven decision-making."
        ),
    },
    {
        "intent": "predictive_models",
        "training_phrases": [
            "Do you build predictive models?",
            "Can you create forecasting systems?",
            "Do you offer prediction models?",
        ],
        "response": (
            "Yes. Nexalix develops predictive models that help businesses forecast customer behavior, "
            "demand patterns, financial risks, and operational performance."
        ),
    },
    {
        "intent": "ml_efficiency",
        "training_phrases": [
            "Can machine learning improve business efficiency?",
            "How does machine learning improve operations?",
            "Is machine learning useful for performance?",
        ],
        "response": (
            "Definitely. Machine learning can optimize operations, improve forecasting accuracy, "
            "and identify opportunities that traditional analysis may miss."
        ),
    },
    {
        "intent": "data_analytics",
        "training_phrases": [
            "Can Nexalix analyze business data?",
            "Do you offer data analytics?",
            "Can you help us understand our data?",
        ],
        "response": (
            "Yes. Nexalix provides data analytics solutions that transform raw data into meaningful insights "
            "to help organizations make better strategic decisions."
        ),
    },
    {
        "intent": "analytics_services",
        "training_phrases": [
            "What data analysis services do you offer?",
            "What can you do with company data?",
            "What analytics solutions do you provide?",
        ],
        "response": (
            "Our services include data cleaning, data visualization, predictive analytics, reporting dashboards, "
            "and advanced analytical models for business intelligence."
        ),
    },
    {
        "intent": "dashboards",
        "training_phrases": [
            "Can you build data dashboards?",
            "Do you create reporting dashboards?",
            "Can you make real-time dashboards?",
        ],
        "response": (
            "Yes. Nexalix builds interactive dashboards that allow businesses to monitor key metrics, "
            "visualize trends, and track performance in real time."
        ),
    },
    {
        "intent": "automation_systems",
        "training_phrases": [
            "What business processes can you automate?",
            "Do you offer automation services?",
            "Can you automate workflows?",
        ],
        "response": (
            "Nexalix automates workflows such as customer management, marketing campaigns, reporting systems, "
            "lead generation, data processing, and other operational tasks."
        ),
    },
    {
        "intent": "automation_benefits",
        "training_phrases": [
            "How does automation help businesses?",
            "What are the benefits of automation?",
            "Why should I automate operations?",
        ],
        "response": (
            "Automation reduces manual work, improves accuracy, speeds up processes, and allows teams to focus "
            "on strategic activities instead of repetitive tasks."
        ),
    },
    {
        "intent": "technology_consulting",
        "training_phrases": [
            "Do you offer technology consulting?",
            "Can you advise us on technology?",
            "Do you provide IT consulting?",
        ],
        "response": (
            "Yes. Nexalix provides technology consulting to help organizations choose the right tools, "
            "design scalable systems, and implement digital transformation strategies."
        ),
    },
    {
        "intent": "digital_transformation",
        "training_phrases": [
            "Can Nexalix help with digital transformation?",
            "Do you help businesses modernize?",
            "Can you help us go digital?",
        ],
        "response": (
            "Yes. We help businesses modernize operations by adopting cloud systems, AI solutions, "
            "data analytics platforms, and automated workflows."
        ),
    },
    {
        "intent": "start_project",
        "training_phrases": [
            "How do I start a project with Nexalix?",
            "How can we begin working together?",
            "How do I get started?",
        ],
        "response": (
            "Starting a project is simple. Share your requirements with us, and our team will schedule a consultation "
            "to understand your needs and recommend the best solution."
        ),
    },
    {
        "intent": "project_timeline",
        "training_phrases": [
            "How long does a project take?",
            "What is the typical timeline?",
            "How much time do you need to complete a system?",
        ],
        "response": (
            "Project timelines depend on the scope and complexity. After the initial consultation, "
            "Nexalix provides a detailed timeline and implementation plan."
        ),
    },
    {
        "intent": "consultation_request",
        "training_phrases": [
            "Do you offer consultations?",
            "Can I book a consultation?",
            "I need a consultation",
        ],
        "response": (
            "Yes. Nexalix offers consultations to help businesses explore technology solutions and determine "
            "the best approach for their project."
        ),
    },
    {
        "intent": "quote_request",
        "training_phrases": [
            "Can I get a quote?",
            "How much will it cost?",
            "Can you give me pricing?",
        ],
        "response": (
            "Pricing depends on the project scope and complexity. Please share your project details and contact "
            "information so our team can prepare a customized quote."
        ),
        "action": "collect_lead",
    },
    {
        "intent": "build_system_request",
        "training_phrases": [
            "I want to build a system for my business",
            "I need software for my company",
            "Can you build a platform for us?",
        ],
        "response": (
            "Great. We would love to help. Please share your name, email, company name, and the type of system "
            "you want to build, and our team will contact you shortly."
        ),
        "action": "collect_lead",
    },
    {
        "intent": "contact_nexalix",
        "training_phrases": [
            "How can I contact Nexalix?",
            "How do I reach your team?",
            "What is the best way to contact you?",
        ],
        "response": (
            "You can contact Nexalix through our website contact form or request a consultation directly "
            "through this chat. Our team will respond promptly."
        ),
    },
    {
        "intent": "location_question",
        "training_phrases": [
            "Where is Nexalix located?",
            "Are you based locally?",
            "Where do you operate from?",
        ],
        "response": (
            "Nexalix operates digitally and supports businesses across different regions, "
            "collaborating remotely with clients worldwide."
        ),
    },
    {
        "intent": "human_handoff",
        "training_phrases": [
            "I want to talk to a human",
            "Can I speak to someone?",
            "Connect me with an advisor",
        ],
        "response": (
            "No problem. I can connect you with a Nexalix advisor. "
            "Please share your name and email so our team can reach out to you shortly."
        ),
        "action": "collect_lead",
    },
]

LEAD_CAPTURE_FIELDS = [
    {"name": "full_name", "label": "Full Name", "type": "text", "required": True},
    {"name": "email", "label": "Email Address", "type": "email", "required": True},
    {"name": "phone", "label": "Phone Number", "type": "text", "required": False},
    {"name": "company", "label": "Company Name", "type": "text", "required": False},
    {
        "name": "service_interest",
        "label": "Service of Interest",
        "type": "select",
        "required": True,
        "options": COMPANY_PROFILE["services"],
    },
    {
        "name": "project_description",
        "label": "Project Description",
        "type": "textarea",
        "required": True,
    },
]

FAQ_EXAMPLES = [
    {
        "question": "What does Nexalix do?",
        "answer": COMPANY_PROFILE["description"],
    },
    {
        "question": "Do you build custom software?",
        "answer": (
            "Yes. Nexalix develops custom software tailored to business needs, including web platforms, "
            "enterprise systems, portals, and digital tools."
        ),
    },
    {
        "question": "Do you provide AI solutions?",
        "answer": (
            "Yes. Nexalix develops AI-powered systems that help businesses automate processes, "
            "analyze patterns, and improve decision-making."
        ),
    },
    {
        "question": "Can you build data dashboards?",
        "answer": (
            "Yes. Nexalix builds interactive dashboards for monitoring key metrics, "
            "visualizing trends, and tracking performance in real time."
        ),
    },
    {
        "question": "Can I get a quote?",
        "answer": (
            "Pricing depends on project scope and complexity. Please share your project details and contact "
            "information so our team can prepare a customized quote."
        ),
    },
]
