from dataclasses import dataclass
from decimal import Decimal
from typing import Self


# The final, immutable product (cannot be mutated once created)
@dataclass(frozen=True)
class PaymentRequest:
    amount: Decimal
    currency: str
    discount: Decimal
    webhook_url: str | None
    max_retries: int


# The mutable staging object
class PaymentRequestBuilder:
    def __init__(self, amount: Decimal, currency: str = "USD") -> None:
        # Required fields go in __init__
        self._amount = amount
        self._currency = currency
        # Optional fields start with safe defaults
        self._discount = Decimal("0")
        self._webhook_url: str | None = None
        self._max_retries = 0

    def set_discount(self, discount: Decimal) -> None:
        self._discount = discount

    def set_webhook(self, url: str) -> None:
        self._webhook_url = url

    def set_retries(self, count: int) -> None:
        self._max_retries = count

    def build(self) -> PaymentRequest:
        # Cross-field validation happens once all stages are done
        if self._amount <= 0:
            raise ValueError("amount must be positive")
        if not (0 <= self._discount < self._amount):
            raise ValueError("discount must be >= 0 and < amount")
        if self._max_retries > 0 and not self._webhook_url:
            raise ValueError("retries require a webhook_url")

        return PaymentRequest(
            amount=self._amount,
            currency=self._currency,
            discount=self._discount,
            webhook_url=self._webhook_url,
            max_retries=self._max_retries,
        )


# --- Usage: different layers can mutate the same builder before .build() ---
builder = PaymentRequestBuilder(Decimal("100.00"))
builder.set_discount(Decimal("15.00"))  # Promo layer
builder.set_webhook("https://app.io/hook")  # Reliability layer
builder.set_retries(3)  # Reliability layer

req = builder.build()  # Validates & locks it

# ======================== upgrading to fluent


class PaymentRequestBuilderFluent:
    # init and build are meant to be the same as above
    # so fluent is more of a wrapper over builder
    def __init__(self, amt: Decimal): ...

    def build(self): ...

    def with_discount(self, discount: Decimal) -> Self:
        self._discount = discount
        return self

    def with_webhook(self, url: str) -> Self:
        self._webhook_url = url
        return self

    def with_retries(self, count: int) -> Self:
        self._max_retries = count
        return self


# --- Usage: same behavior, chained like a mini-DSL ---
req = (
    PaymentRequestBuilderFluent(Decimal("100.00"))
    .with_discount(Decimal("15.00"))
    .with_webhook("https://app.io/hook")
    .with_retries(3)
    .build()
)
