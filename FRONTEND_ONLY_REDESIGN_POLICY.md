# Frontend-Only Redesign Policy

This project is a Django application with admin-managed content. Visual redesign work must not change database-backed content, user accounts, or admin behavior unless the change is explicitly approved as backend work.

## Goal

Keep design work limited to presentation:

- templates
- CSS
- JavaScript
- static assets

Do not let design work silently change:

- Django admin data
- user records
- seeded content
- deployment behavior
- migrations

## Default Rule

If a task is described as a redesign, polish, spacing fix, styling update, layout refactor, or frontend consistency pass, it must stay frontend-only unless backend approval is explicit.

## Safe Paths For Frontend-Only Work

These paths are allowed by default for redesign work:

- `nexalix_app/templates/**`
- `nexalix_app/static/css/**`
- `nexalix_app/static/js/**`
- `nexalix_app/static/images/**`
- `nexalix_app/static/fonts/**`

Project guardrail files are also allowed:

- `FRONTEND_ONLY_REDESIGN_POLICY.md`
- `scripts/check_frontend_only_redesign.sh`

## Backend Paths That Require Explicit Approval

Changes in these files or directories can affect admin-backed content, users, or deployment behavior. Treat them as backend work:

- `nexalix_app/views.py`
- `nexalix_app/forms.py`
- `nexalix_app/models.py`
- `nexalix_app/admin.py`
- `nexalix_app/signals.py`
- `nexalix_app/context_processors.py`
- `nexalix_app/cache_utils.py`
- `nexalix_app/chatbot.py`
- `nexalix_app/urls.py`
- `nexalix_app/migrations/**`
- `manage.py`
- `nexalix_site/settings.py`
- `nexalix_site/urls.py`
- `render.yaml`
- `Procfile`
- deployment scripts and environment files

## Known Data-Changing Surfaces

These existing backend paths already mutate data and should not be touched during frontend-only redesigns:

- `nexalix_app/forms.py`
  - `AdminAccessRequestForm.save()` creates users.
- `nexalix_app/views.py`
  - admin account request creates users
  - updates subscriber signup creates/reactivates subscribers
  - activity dashboard updates user profile fields and saved filters
  - SEO topic generator creates draft blog posts
  - quote generator creates quote requests
  - chatbot lead endpoint creates chatbot leads
  - contact form creates contact messages
- `nexalix_app/admin.py`
  - admin actions mark messages read/unread
  - admin actions grant/remove staff access
- `nexalix_app/migrations/0012_seed_solution_pages_and_clusters.py`
  - seeds solution content
  - reverse migration deletes seeded `SolutionPage` and `ServiceSolutionCluster` records

## Deployment Risk

Deployments run migrations:

- `render.yaml`
- `Procfile`

That means any migration included in a design deploy can alter database content even if the visible task sounds “frontend-only.”

## Required Workflow For Frontend-Only Redesigns

1. Limit edits to safe frontend paths.
2. Do not change views, models, forms, admin, signals, migrations, or deploy files.
3. Run the guardrail check before committing or pushing:

```bash
./scripts/check_frontend_only_redesign.sh --staged
```

4. If the check flags backend files, stop and either:
   - split the work into separate commits, or
   - get explicit approval for backend changes

## Frontend-Safe Techniques

Use these approaches first:

- template partial refactors
- page-scoped CSS overrides
- shared component styling in CSS
- non-destructive JS interactions
- graceful fallbacks for missing admin content
- hiding placeholder text in templates instead of rewriting stored data

## Avoid During Frontend-Only Work

- adding or editing migrations
- changing model fields
- changing admin actions
- changing POST handlers
- changing form save behavior
- changing seed scripts
- changing deploy commands

## Notes

- Cache invalidation in signals is backend behavior, even if it does not delete content.
- If a redesign truly needs new data shaping, that should be reviewed as a separate backend task.
- When in doubt, assume the change is not frontend-only and review it first.
