import json
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import redis_client
from app.models import Booking, BookingStatus, Staff


class AIBookingChat:
    def __init__(self, db: AsyncSession, user_id: int):
        self.db = db
        self.user_id = user_id
        self.conversation_history = []

        today = datetime.utcnow().strftime("%Y-%m-%d")
        self.redis_key = f"chat:{user_id}:{today}"

    async def _load_history(self):
        history = await redis_client.get(self.redis_key)
        if history:
            self.conversation_history = json.loads(history)

    async def _save_history(self):
        await redis_client.setex(
            self.redis_key,
            timedelta(hours=24),
            json.dumps(self.conversation_history),
        )

    async def get_schedule_context(
        self,
        staff_id: int,
        date: datetime,
        duration_time: int,
    ) -> dict:
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        result = await self.db.execute(
            select(Booking).where(
                Booking.staff_id == staff_id,
                Booking.start_time >= day_start,
                Booking.start_time < day_end,
                Booking.status.in_([
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.DEPOSIT_PAID,
                ]),
            ).order_by(Booking.start_time)
        )
        bookings = result.scalars().all()

        staff = await self.db.get(Staff, staff_id)

        busy = [
            {
                "start": b.start_time.strftime("%H:%M"),
                "end": b.end_time.strftime("%H:%M"),
            }
            for b in bookings
        ]

        return {
            "date": date.strftime("%Y-%m-%d"),
            "staff_name": staff.name if staff else "Unknown",
            "work_hours": "09:00-17:00",
            "busy_slots": busy,
            "duration_time": duration_time,
            "buffer_minutes": 15,
        }

    async def chat(self, user_message: str, context: dict) -> dict:
        await self._load_history()
        self.conversation_history.append({"role": "user", "content": user_message})

        system_prompt = f"""
Jesteś asystentem rezerwacji w salonie beauty. Rozmawiasz z klientem.

KONTEKST GRAFIKU:
- Data: {context['date']}
- Pracownik: {context['staff_name']}
- Godziny pracy: {context['work_hours']}
- Zajęte przedziały: {context['busy_slots']}
- Usługa trwa: {context['duration_time']} minut
- Przerwa między klientami: {context['buffer_minutes']} minut

TWOJE ZADANIE:
1. Rozmawiaj naturalnie po polsku
2. Proponuj terminy, które nie kolidują z zajętymi
3. Minimalizuj luki – proponuj terminy przylegające do istniejących rezerwacji
4. Gdy klient potwierdzi – zwróć dane rezerwacji

FORMAT ODPOWIEDZI (ZAWSZE JSON):
{{
  "message": "Twoja odpowiedź do klienta",
  "suggested_slots": [
    {{"start": "HH:MM", "end": "HH:MM", "reason": "uzasadnienie"}}
  ],
  "ready_to_book": false,
  "booking_details": null
}}

Gdy klient potwierdzi, ustaw "ready_to_book": true i wypełnij "booking_details":
{{
  "start_time": "YYYY-MM-DDTHH:MM:00"
}}
"""

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
                json={
                    "model": "openai/gpt-oss-120b",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *self.conversation_history,
                    ],
                    "temperature": 0.3,
                },
                timeout=30.0,
            )

        data = response.json()
        print("=== Groq response ===")
        print(f"Status: {response.status_code}")
        print(f"Data: {data}")
        print("=========================")

        if "choices" not in data:
            return {
                "message": "Przepraszam, asystent jest chwilowo niedostępny. "
                           "Spróbuj ponownie lub wybierz termin samodzielnie.",
                "suggested_slots": [],
                "ready_to_book": False,
                "booking_details": None,
                "error": data.get("error", {}).get("message", "Unknown error"),
            }

        ai_response = data["choices"][0]["message"]["content"]
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        await self._save_history()

        try:
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].split("```")[0].strip()

            parsed = json.loads(ai_response)
        except (json.JSONDecodeError, IndexError):
            parsed = {
                "message": ai_response,
                "suggested_slots": [],
                "ready_to_book": False,
                "booking_details": None,
            }

        return parsed