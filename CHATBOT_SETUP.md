# Nexalix Chatbot Setup

This chatbot is implemented with:
- Django backend API endpoints
- OpenAI API (server-side only)
- Session-based conversation memory
- Lead storage in database (`ChatbotLead`)
- Admin email notifications for new chatbot leads
- Frontend widget in base template

## 1) Install dependencies

```bash
pip install -r requirements.txt
```

## 2) Environment variables

Set these in local `.env` or your hosting platform:

- `OPENAI_API_KEY=...`
- `OPENAI_CHAT_MODEL=gpt-4o-mini`
- `OPENAI_CHAT_TEMPERATURE=0.3`
- `OPENAI_CHAT_MAX_TOKENS=500`
- `CHATBOT_SESSION_HISTORY_LIMIT=16`
- `CHATBOT_RATE_LIMIT_COUNT=20`
- `CHATBOT_RATE_LIMIT_WINDOW_SECONDS=600`
- `CHATBOT_LEAD_RATE_LIMIT_COUNT=6`
- `CHATBOT_LEAD_RATE_LIMIT_WINDOW_SECONDS=600`
- `CHATBOT_WHATSAPP_URL=https://wa.me/254768774232`

Also ensure email config is set so admin notifications are sent:

- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `CONTACT_NOTIFICATION_EMAIL`
- `ADMIN_EMAILS`

## 3) Migrate

```bash
python manage.py migrate
```

## 4) Endpoints

- `POST /api/chatbot/message/`
- `POST /api/chatbot/lead/`

Both expect JSON and use CSRF protection.

## 5) Production notes

- Keep `OPENAI_API_KEY` only on server environment.
- Do not expose API key in frontend code.
- Rate limiting uses Django cache backend (Redis recommended in production).
- Conversation history is stored in Django session under `chatbot_history`.
- Lead records are visible in Django admin under `Chatbot Leads`.

## 6) Basic smoke test

1. Open site and click `Chat with Nexalix`.
2. Ask service/pricing question.
3. Confirm assistant responds and shows recommendations.
4. Submit lead details in widget.
5. Verify record in Django admin (`ChatbotLead`).
6. Verify notification email reaches configured admin inbox.
