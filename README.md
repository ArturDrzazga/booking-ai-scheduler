# Booking AI Scheduler

Async REST API for beauty salon appointment booking with AI assistant.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (asyncpg)
- **ORM**: SQLAlchemy
- **Cache**: Redis
- **Background Tasks**: Celery
- **Payments**: Stripe
- **AI**: DeepSeek API
- **Deployment**: Docker + AWS Lightsail

## Quick Start

```bash
# Clone
git clone https://github.com/twoja-nazwa/booking-ai-scheduler.git
cd booking-ai-scheduler

# Setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload