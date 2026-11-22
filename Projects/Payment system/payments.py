# Factory pattern
# Design a system that supports payments through Credit Card, PayPal, and Digital Wallet.
# Each payment method should implement pay(amount) and refund(transaction_id).

# ----------------------

#     <<Abstract>>                         <<Abstract>>
# +---------------------+             +---------------------+
# |   PaymentFactory    | ----------> |   PaymentProcessor  |
# +---------------------+   creates   +---------------------+
#           ^                                    ^
#           | extends                            | implements
#           |                                    |
# +---------------------+             +---------------------+
# |  CreditCardFactory  | ----------> |  CreditCardPayment  |
# +---------------------+   creates   +---------------------+
#      <<Concrete>>                         <<Concrete>>
#           .                                    .
#           .   (PayPal, DigitalWallet, etc.)    .

# Why the factory is actually useful here:
# 1. Base PaymentFactory owns shared validation & double-refund tracking once.
# 2. Concrete factories hide completely different constructor dependencies.
# 3. Client code (process_order) stays blind to concrete classes and configs.

# --------------------------

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from uuid import uuid4


# --- 1. Product Interface ---
class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: Decimal) -> str:
        """Charge the amount and return a provider transaction ID."""

    @abstractmethod
    def refund(self, transaction_id: str) -> None:
        """Reverse a previously completed transaction."""


# --- 2. Concrete Products (notice their completely different constructors) ---
class CreditCardPayment(PaymentProcessor):
    def __init__(self, api_key: str, fee_percent: Decimal) -> None:
        self._api_key = api_key
        self._fee_percent = fee_percent

    def pay(self, amount: Decimal) -> str:
        fee = (amount * self._fee_percent).quantize(Decimal("0.01"))
        tx_id = f"cc_{uuid4().hex[:6]}"
        print(f"[CreditCard] Charged ${amount} (+${fee} fee) via key ***{self._api_key[-4:]}")
        return tx_id

    def refund(self, transaction_id: str) -> None:
        print(f"[CreditCard] Refunded {transaction_id} via key ***{self._api_key[-4:]}")


class PayPalPayment(PaymentProcessor):
    def __init__(self, merchant_email: str) -> None:
        self._merchant_email = merchant_email

    def pay(self, amount: Decimal) -> str:
        tx_id = f"pp_{uuid4().hex[:6]}"
        print(f"[PayPal] Sent ${amount} to {self._merchant_email}")
        return tx_id

    def refund(self, transaction_id: str) -> None:
        print(f"[PayPal] Reversed {transaction_id} from {self._merchant_email}")


@dataclass
class WalletAccount:
    owner: str
    balance: Decimal
    ledger: dict[str, Decimal] = field(default_factory=dict)


class DigitalWalletPayment(PaymentProcessor):
    def __init__(self, account: WalletAccount) -> None:
        self._account = account

    def pay(self, amount: Decimal) -> str:
        if self._account.balance < amount:
            raise ValueError("Insufficient wallet balance")
        self._account.balance -= amount
        tx_id = f"dw_{uuid4().hex[:6]}"
        self._account.ledger[tx_id] = amount
        print(f"[Wallet:{self._account.owner}] Paid ${amount} (left: ${self._account.balance})")
        return tx_id

    def refund(self, transaction_id: str) -> None:
        amount = self._account.ledger.pop(transaction_id)
        self._account.balance += amount
        print(f"[Wallet:{self._account.owner}] Refunded ${amount} (balance: ${self._account.balance})")


# --- 3. Base Factory (owns shared rules so concrete classes stay simple) ---
class PaymentFactory(ABC):
    def __init__(self) -> None:
        self._active_transactions: set[str] = set()

    @abstractmethod
    def create_processor(self) -> PaymentProcessor:
        pass

    def execute_payment(self, amount: Decimal) -> str:
        # Shared validation: written ONCE for all payment types
        if not isinstance(amount, Decimal) or not amount.is_finite() or amount <= 0:
            raise ValueError("Amount must be a positive, finite Decimal")

        processor = self.create_processor()
        tx_id = processor.pay(amount)
        self._active_transactions.add(tx_id)
        return tx_id

    def execute_refund(self, transaction_id: str) -> None:
        # Shared double-refund protection: written ONCE for all payment types
        if transaction_id not in self._active_transactions:
            raise ValueError(f"Unknown or already refunded transaction: {transaction_id}")

        processor = self.create_processor()
        processor.refund(transaction_id)
        self._active_transactions.remove(transaction_id)


# --- 4. Concrete Factories (absorb messy setup / dependencies) ---
class CreditCardFactory(PaymentFactory):
    def __init__(self, api_key: str, fee_percent: Decimal = Decimal("0.029")) -> None:
        # don't read from .env INSIDE THIS, pass above, this makes this boundary testable
        super().__init__()
        self._api_key = api_key
        self._fee_percent = fee_percent

    def create_processor(self) -> PaymentProcessor:
        return CreditCardPayment(self._api_key, self._fee_percent)


class PayPalFactory(PaymentFactory):
    def __init__(self, merchant_email: str) -> None:
        super().__init__()
        self._merchant_email = merchant_email

    def create_processor(self) -> PaymentProcessor:
        return PayPalPayment(self._merchant_email)


class DigitalWalletFactory(PaymentFactory):
    def __init__(self, account: WalletAccount) -> None:
        super().__init__()
        self._account = account

    def create_processor(self) -> PaymentProcessor:
        return DigitalWalletPayment(self._account)


# --- 5. Client Code (completely blind to concrete classes and their configs) ---
def process_order(factory: PaymentFactory, amount: Decimal) -> None:
    tx_id = factory.execute_payment(amount)
    factory.execute_refund(tx_id)


def main() -> None:
    # Wiring happens once at the edge of the app
    wallet = WalletAccount(owner="alex", balance=Decimal("50.00"))
    factories: list[PaymentFactory] = [
        CreditCardFactory(api_key="sk_live_9942"),
        PayPalFactory(merchant_email="store@example.com"),
        DigitalWalletFactory(account=wallet),
    ]

    # Exact same workflow works for every provider
    # in the app ofc there would be one, and it would depend on the ui
    for factory in factories:
        process_order(factory, Decimal("10.00"))
        print("---")


if __name__ == "__main__":
    main()

