import enum


class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DEPOSIT_PAID = "deposit_paid"
    COMPLETED = "completed"
    CANCELED = "canceled"
    NO_SHOW = "no_show"
