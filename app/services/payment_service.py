from abc import ABC, abstractmethod

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Booking, BookingStatus


class PaymentProvider(ABC):
    """Abstract Payment Provider"""

    @abstractmethod
    async def create_payment(self, booking: Booking, amount: float) -> dict:
        """Create payment for booking and returns the data for redirect"""
        pass

    @abstractmethod
    async def verify_payment(self, payment_id: str) -> bool:
        """Verifies whether the payment has been completed"""
        pass


class MockPaymentProvider(PaymentProvider):
    """Mock provider - simulates a payment (for testing purposes)"""

    async def create_payment(self, booking: Booking, amount: float) -> dict:
        return {
            "payment_id": f"mock_{booking.id}",
            "amount": amount,
            "redirect_url": f"/payments/mock/{booking.id}",
            "status": "pending",
        }

    async def verify_payment(self, payment_id: str) -> bool:
        return True


class PaymentService:
    """Payment Service"""

    def __init__(self, provider: PaymentProvider):
        self.provider = provider

    async def create_deposit_payment(self, booking: Booking) -> dict:
        """Create deposit payment for booking"""
        if booking.deposit_amount <= 0:
            raise ValueError("Booking has no deposit")
        return await self.provider.create_payment(booking, booking.deposit_amount)

    async def confirm_payment(
        self, booking: Booking, payment_id: str, db: AsyncSession
    ) -> Booking:
        """Confirm payment and updates booking"""
        verified = await self.provider.verify_payment(payment_id)
        if not verified:
            raise ValueError("Payment verification failed")

        booking.deposit_paid = True
        booking.status = BookingStatus.CONFIRMED
        booking.payment_intent_id = payment_id

        db.add(booking)
        await db.commit()
        await db.refresh(booking)
        return booking


def get_payment_service() -> PaymentService:
    return PaymentService(provider=MockPaymentProvider())
