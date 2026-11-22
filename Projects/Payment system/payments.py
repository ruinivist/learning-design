from abc import ABC, abstractmethod
from decimal import Decimal
import typing


# --- this is the prodcut's high level interface
# as a library creator, what I'll do is jusk ask people to satisfy this
class PaymentProcessor(ABC):
    @abstractmethod
    def pay(self, amount: Decimal) -> str:
        """takes in an amount and returnx txn id"""

    @abstractmethod
    def refund(self, txn_id: str) -> None:
        """refund on some txn id"""


# --- now you need some concrete impls
### qq: will it complain if I don't define pay here
### ans: only when you instatiate it
class CreditCardPayment(PaymentProcessor):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def pay(self, amount: Decimal) -> str:
        return "1234"

    def refund(self, txn_id: str) -> None:
        print(f"Refunded {txn_id}")


class PaypalPayment(PaymentProcessor):
    def __init__(self, client_id: str) -> None:
        self.client_id = client_id

    def pay(self, amount: Decimal) -> str:
        return "9876"

    def refund(self, txn_id: str) -> None:
        print(f"Refunded {txn_id}")


# --- now naturally you want to use these
# but instaed of coupling you want to use it at the processor level
# as a library owner I wanted to log all the "pay" and "refund" calls
# so I can't let you directly use things
# Here's antother interface that MY platform will support --- and that YOU
# must implement


class PaymentFactory(ABC):
    @abstractmethod
    def create_processor(self) -> PaymentProcessor:
        pass

    # my funcs for logging -- I don't want people to override these
    # but I don't think python allows me to stop -- it'll show the problem in
    # type checker but unlike java's final, not enforced at runtime
    @typing.final
    def exec_payment(self, amount: Decimal) -> str:
        # some validations ...
        processor = self.create_processor()
        # treat this print as some custom logging I have
        # that you PLEBS can't skip
        print(f"Starting payment: {amount}")

        # more so whatever
        return processor.pay(amount)

    @typing.final
    def exec_refund(self, txn_id: str) -> None:
        processor = self.create_processor()
        # more of just the same
        processor.refund(txn_id)


# --- now the other team, I'll believe there would be one for each payment system
# will impl their processor and a factory per MY interface
# there would be some central registry too at the composition root where they will
# register aka the place where the request gets mapped to some processor


class PaypalFactory(PaymentFactory):
    def __init__(self) -> None:
        # ideally this will be an arg to make it testable and the key would be passed
        # from composition root
        self.client_id = "my-super-secret-key-store"

    def create_processor(self) -> PaymentProcessor:
        return PaypalPayment(self.client_id)

    # leave the actual payemnt and refund calls to the other team


# --- as the library owner on my end I have something like this that I then give them
# or that I use internally
def process_order(factory: PaymentFactory, amount: Decimal) -> None:
    tx_id = factory.exec_payment(amount)
    factory.exec_refund(tx_id)


def main() -> None:
    # composition root
    factories = {"paypal_button": PaypalFactory()}
    process_order(factories["paypal_button"], Decimal(10))
