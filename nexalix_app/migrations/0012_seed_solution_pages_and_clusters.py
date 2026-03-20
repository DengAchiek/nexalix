from django.db import migrations


SERVICE_CLUSTERS = [
    {
        "slug": "software-development",
        "title": "Software Development",
        "icon": "fas fa-laptop-code",
        "value_statement": "Custom digital systems that remove operational friction and support growth.",
        "business_problem": "When teams outgrow spreadsheets, disconnected tools, or off-the-shelf platforms, we design software that matches the real operating model.",
        "deliverables": "Custom web platforms\nClient portals\nInternal business systems",
        "who_for": "Operations-heavy teams, service businesses, and organizations launching new digital products.",
        "keywords": "software, platform, portal, web, mobile, app, system, product, cloud, infrastructure",
        "order": 0,
    },
    {
        "slug": "ai-automation",
        "title": "AI and Automation",
        "icon": "fas fa-robot",
        "value_statement": "AI workflows and automation systems that reduce manual work and improve response speed.",
        "business_problem": "We help teams remove repetitive tasks, improve lead handling, and create faster customer and internal workflows.",
        "deliverables": "Lead qualification systems\nAI chat assistants\nWorkflow automation",
        "who_for": "Teams handling high-volume inquiries, repeatable operations, or service processes that need automation.",
        "keywords": "ai, automation, machine learning, chatbot, assistant, workflow, predictive",
        "order": 1,
    },
    {
        "slug": "data-analytics",
        "title": "Data and Analytics",
        "icon": "fas fa-chart-line",
        "value_statement": "Reporting systems and data visibility tools that improve decision-making.",
        "business_problem": "When reporting is fragmented or delayed, we create dashboards and data systems that give teams operational clarity.",
        "deliverables": "Dashboards\nReporting systems\nBI implementation",
        "who_for": "Leadership, operations, finance, and growth teams that need trustworthy reporting and performance visibility.",
        "keywords": "data, analytics, dashboard, report, bi, insight, reporting",
        "order": 2,
    },
    {
        "slug": "consulting-transformation",
        "title": "Consulting and Transformation",
        "icon": "fas fa-sitemap",
        "value_statement": "Consulting-led planning and implementation for modernization, scale, and digital transformation.",
        "business_problem": "We turn unclear requirements, legacy process friction, and scaling challenges into a phased execution roadmap.",
        "deliverables": "Solution architecture\nProcess digitization\nDigital transformation roadmap",
        "who_for": "Leaders planning modernization, transformation programs, or cross-functional delivery initiatives.",
        "keywords": "consult, transformation, strategy, roadmap, digitization, advisory, training",
        "order": 3,
    },
]

SOLUTION_PAGES = [
    {
        "slug": "software-development",
        "nav_title": "Software Development",
        "headline": "Software development that replaces friction with scalable digital systems",
        "subheadline": "We design and build web platforms, internal business systems, and customer portals that improve execution, visibility, and growth.",
        "solution_cluster_slug": "software-development",
        "problems": "Manual workflows slow down delivery and increase operational risk.\nTeams are relying on disconnected tools that do not match the real business process.\nExisting systems cannot scale with new customers, users, or reporting needs.",
        "deliverables": "Custom web platforms\nClient portals\nInternal business systems",
        "technologies": "Python\nDjango\nReact\nPostgreSQL\nAPIs",
        "keywords": "software, platform, portal, web, system, product, application",
        "faq_items": "What kind of software does Nexalix build? | Nexalix builds custom web platforms, client portals, internal systems, and digital products tailored to specific business workflows.\nHow do projects usually start? | We begin with business discovery, scope the core requirements, and then define the architecture, delivery phases, and implementation plan.\nCan you modernize an existing system? | Yes. Nexalix can improve, extend, or re-platform existing systems while preserving critical workflows and integrations.",
        "order": 0,
    },
    {
        "slug": "ai-automation",
        "nav_title": "AI Automation",
        "headline": "AI automation that helps teams respond faster and do more with less manual work",
        "subheadline": "From chat assistants to lead handling and workflow orchestration, we implement AI and automation systems that remove bottlenecks and improve service speed.",
        "solution_cluster_slug": "ai-automation",
        "problems": "Leads, service requests, or internal tasks are handled manually and inconsistently.\nTeams spend time on repetitive coordination instead of strategic work.\nCustomer interactions need faster first-response and better routing.",
        "deliverables": "AI chat assistants\nWorkflow automation\nLead qualification systems",
        "technologies": "Python\nOpenAI\nDjango\nAPIs\nAutomation Integrations",
        "keywords": "ai, automation, assistant, chatbot, workflow, lead, process",
        "faq_items": "What AI automation services do you provide? | We implement AI chat assistants, automated lead qualification, workflow orchestration, and process-support systems.\nDo you expose AI APIs on the frontend? | No. Nexalix uses server-side integrations so keys and orchestration logic remain protected.\nCan AI automation connect to existing systems? | Yes. We can integrate automation with forms, CRMs, email workflows, internal tools, and reporting systems.",
        "order": 1,
    },
    {
        "slug": "machine-learning-solutions",
        "nav_title": "Machine Learning Solutions",
        "headline": "Machine learning solutions for forecasting, decision support, and smarter operations",
        "subheadline": "We help businesses turn historical data into predictive models and decision-support tools that improve planning, prioritization, and risk visibility.",
        "solution_cluster_slug": "ai-automation",
        "problems": "Teams have data but no predictive layer for planning or forecasting.\nDecisions are being made without reliable pattern detection or trend analysis.\nOperational or commercial risk is hard to quantify in advance.",
        "deliverables": "Predictive models\nRecommendation systems\nDecision-support analytics",
        "technologies": "Python\nTensorFlow\nPandas\nPostgreSQL\nDashboards",
        "keywords": "machine learning, prediction, forecast, model, recommendation, analytics",
        "faq_items": "When is machine learning the right fit? | Machine learning is useful when you have historical data and want to improve forecasting, classification, recommendations, or pattern detection.\nCan Nexalix help with model deployment? | Yes. We support the full path from use-case definition and model development to deployment and monitoring.\nDo you also build the reporting layer around ML outputs? | Yes. We can connect predictive outputs to dashboards, alerts, and operational workflows.",
        "order": 2,
    },
    {
        "slug": "data-analytics",
        "nav_title": "Data Analytics",
        "headline": "Data analytics systems that make business performance visible and actionable",
        "subheadline": "We build dashboards, reporting systems, and data workflows that give leadership and operations teams a clearer view of performance, trends, and risk.",
        "solution_cluster_slug": "data-analytics",
        "problems": "Reporting is fragmented across spreadsheets and siloed tools.\nDecision-makers do not have timely visibility into key business metrics.\nOperational performance issues are discovered too late to act quickly.",
        "deliverables": "Dashboards\nReporting systems\nBI implementation",
        "technologies": "Python\nSQL\nPostgreSQL\nBI Dashboards\nAPIs",
        "keywords": "data, analytics, dashboard, reporting, bi, metrics",
        "faq_items": "What analytics solutions does Nexalix offer? | We deliver dashboards, reporting systems, data integration workflows, and visibility tools for business intelligence.\nCan you work with existing data sources? | Yes. We can connect operational databases, spreadsheets, APIs, and third-party systems into reporting layers.\nDo you build real-time dashboards? | Yes, where the source systems and update patterns support real-time or near-real-time reporting.",
        "order": 3,
    },
    {
        "slug": "business-automation",
        "nav_title": "Business Automation",
        "headline": "Business automation that removes repetitive work and improves delivery speed",
        "subheadline": "We digitize and automate operational workflows so teams can reduce errors, improve turnaround time, and scale with fewer manual dependencies.",
        "solution_cluster_slug": "ai-automation",
        "problems": "Manual approvals, handoffs, and updates are slowing down execution.\nTeams repeat the same operational tasks every day with inconsistent quality.\nAs the business grows, coordination overhead is increasing faster than output.",
        "deliverables": "Approval workflows\nOperational automations\nProcess digitization systems",
        "technologies": "Django\nAPIs\nAutomation Logic\nNotifications\nDashboards",
        "keywords": "automation, business, workflow, digitization, process, operations",
        "faq_items": "What processes can be automated? | Typical candidates include approvals, lead routing, follow-up workflows, status tracking, notifications, and repetitive operational tasks.\nDoes automation replace the team? | The goal is to remove low-value manual work so the team can focus on exceptions, quality, and strategic decisions.\nCan automation include reporting? | Yes. Automation can be paired with dashboards and alerts so teams see outcomes, delays, and workload trends.",
        "order": 4,
    },
    {
        "slug": "technology-consulting",
        "nav_title": "Technology Consulting",
        "headline": "Technology consulting for organizations planning digital change with less risk",
        "subheadline": "We help leaders define the right systems, roadmap, architecture, and execution plan before committing budget and delivery effort.",
        "solution_cluster_slug": "consulting-transformation",
        "problems": "Leadership knows change is needed but the next technical step is unclear.\nTransformation initiatives lack a phased roadmap and delivery structure.\nMultiple systems, stakeholders, or integrations make decision-making difficult.",
        "deliverables": "Solution architecture\nProcess digitization roadmap\nTransformation planning",
        "technologies": "Architecture Planning\nDiscovery Workshops\nRoadmaps\nIntegration Mapping",
        "keywords": "consulting, strategy, architecture, transformation, roadmap, digitization",
        "faq_items": "What does consulting-led execution mean? | It means Nexalix helps define the solution and then stays close to implementation so planning and delivery remain aligned.\nCan you support only the strategy phase? | Yes. We can deliver discovery, roadmap, and architecture work as a standalone engagement.\nDo you also support implementation after consulting? | Yes. Nexalix can move from strategy into build, launch, support, and optimization.",
        "order": 5,
    },
]

PROCESS_BLUEPRINTS = [
    {
        "number": "01",
        "title": "Discovery",
        "legacy_titles": {"requirement gathering", "discovery & analysis"},
        "icon": "fas fa-magnifying-glass-chart",
        "description": "Understand business goals, user needs, operational bottlenecks, and implementation constraints.",
        "outputs": "Discovery notes\nPriority use cases\nStakeholder requirements",
        "order": 0,
    },
    {
        "number": "02",
        "title": "Solution Planning",
        "legacy_titles": {"research & analysis", "research", "planning & architecture"},
        "icon": "fas fa-diagram-project",
        "description": "Map features, integrations, architecture, milestones, and delivery phases before build starts.",
        "outputs": "Solution blueprint\nDelivery roadmap\nIntegration plan",
        "order": 1,
    },
    {
        "number": "03",
        "title": "Build and QA",
        "legacy_titles": {"design & development", "design & build", "development & implementation"},
        "icon": "fas fa-code-branch",
        "description": "Develop, test, secure, and validate the solution in focused sprints with visible progress.",
        "outputs": "MVP or build sprint\nQA checklist\nRelease-ready system",
        "order": 2,
    },
    {
        "number": "04",
        "title": "Launch and Support",
        "legacy_titles": {"qa & delivery", "delivery", "support & optimization"},
        "icon": "fas fa-rocket",
        "description": "Deploy, monitor, optimize, and support the system after launch so teams can scale with confidence.",
        "outputs": "Deployment plan\nSupport handoff\nOptimization backlog",
        "order": 3,
    },
]

SERVICE_CATEGORY_CLUSTER_MAP = {
    "development": "software-development",
    "cloud": "software-development",
    "ai": "ai-automation",
    "marketing": "data-analytics",
    "consulting": "consulting-transformation",
    "training": "consulting-transformation",
}


def seed_dynamic_site_content(apps, schema_editor):
    ServiceSolutionCluster = apps.get_model("nexalix_app", "ServiceSolutionCluster")
    SolutionPage = apps.get_model("nexalix_app", "SolutionPage")
    ProcessStep = apps.get_model("nexalix_app", "ProcessStep")
    Service = apps.get_model("nexalix_app", "Service")

    cluster_objects = {}
    for cluster in SERVICE_CLUSTERS:
        obj, _ = ServiceSolutionCluster.objects.update_or_create(
            slug=cluster["slug"],
            defaults={
                "title": cluster["title"],
                "icon": cluster["icon"],
                "value_statement": cluster["value_statement"],
                "business_problem": cluster["business_problem"],
                "who_for": cluster["who_for"],
                "deliverables": cluster["deliverables"],
                "keywords": cluster["keywords"],
                "order": cluster["order"],
                "is_active": True,
                "show_on_homepage": True,
                "primary_cta_text": "Get Proposal",
                "secondary_cta_text": "Book Consultation",
            },
        )
        cluster_objects[cluster["slug"]] = obj

    for page in SOLUTION_PAGES:
        SolutionPage.objects.update_or_create(
            slug=page["slug"],
            defaults={
                "nav_title": page["nav_title"],
                "headline": page["headline"],
                "subheadline": page["subheadline"],
                "solution_cluster": cluster_objects.get(page["solution_cluster_slug"]),
                "problems": page["problems"],
                "deliverables": page["deliverables"],
                "technologies": page["technologies"],
                "keywords": page["keywords"],
                "faq_items": page["faq_items"],
                "order": page["order"],
                "is_active": True,
            },
        )

    existing_steps = list(ProcessStep.objects.all().order_by("order", "id"))
    unmatched_steps = existing_steps[:]
    for blueprint in PROCESS_BLUEPRINTS:
        matched = None
        blueprint_number = (blueprint["number"] or "").lstrip("0") or "0"
        for step in unmatched_steps:
            title = (step.title or "").strip().lower()
            step_number = (step.number or "").strip().lstrip("0") or "0"
            if (
                title == blueprint["title"].lower()
                or title in blueprint["legacy_titles"]
                or step_number == blueprint_number
            ):
                matched = step
                break

        if matched:
            matched.number = matched.number or blueprint["number"]
            matched.title = matched.title or blueprint["title"]
            matched.icon = matched.icon or blueprint["icon"]
            matched.description = matched.description or blueprint["description"]
            matched.outputs = matched.outputs or blueprint["outputs"]
            matched.order = matched.order if matched.order is not None else blueprint["order"]
            matched.save(update_fields=["number", "title", "icon", "description", "outputs", "order"])
            unmatched_steps.remove(matched)
        else:
            ProcessStep.objects.create(
                number=blueprint["number"],
                title=blueprint["title"],
                icon=blueprint["icon"],
                description=blueprint["description"],
                outputs=blueprint["outputs"],
                order=blueprint["order"],
            )

    keyword_map = {
        cluster["slug"]: [item.strip().lower() for item in cluster["keywords"].split(",") if item.strip()]
        for cluster in SERVICE_CLUSTERS
    }
    for service in Service.objects.all():
        if service.solution_cluster_id:
            continue
        haystack = " ".join(
            [
                service.title or "",
                service.short_description or "",
                service.full_description or "",
                service.key_features or "",
                service.technologies or "",
            ]
        ).lower()
        cluster_slug = None
        for slug, keywords in keyword_map.items():
            if any(keyword in haystack for keyword in keywords):
                cluster_slug = slug
                break
        if not cluster_slug:
            cluster_slug = SERVICE_CATEGORY_CLUSTER_MAP.get(service.category, "software-development")
        service.solution_cluster = cluster_objects.get(cluster_slug)
        service.save(update_fields=["solution_cluster"])


def unseed_dynamic_site_content(apps, schema_editor):
    ServiceSolutionCluster = apps.get_model("nexalix_app", "ServiceSolutionCluster")
    SolutionPage = apps.get_model("nexalix_app", "SolutionPage")
    Service = apps.get_model("nexalix_app", "Service")

    Service.objects.filter(solution_cluster__slug__in=[item["slug"] for item in SERVICE_CLUSTERS]).update(solution_cluster=None)
    SolutionPage.objects.filter(slug__in=[item["slug"] for item in SOLUTION_PAGES]).delete()
    ServiceSolutionCluster.objects.filter(slug__in=[item["slug"] for item in SERVICE_CLUSTERS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("nexalix_app", "0011_servicesolutioncluster_processstep_icon_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_dynamic_site_content, unseed_dynamic_site_content),
    ]
