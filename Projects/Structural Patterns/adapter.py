from abc import ABC, abstractmethod


# my NEW interface that everyone likes
class AlertSender(ABC):
    @abstractmethod
    def send(self, severity: int, title: str) -> str: ...


# the sdk that everyone hates
class LegacySdk:
    def dispatch(self, text: str) -> str:
        return f"well, something failed with {text}"


# the HACK aka adapter
class LegacyPagerAdapter(AlertSender):
    def __init__(self, badSdk: LegacySdk):
        self._sdk = badSdk

    def send(self, severity: int, title: str) -> str:
        msg = self._sdk.dispatch(title)
        return f"same but NEW {msg}"


# now the client can juse use the wrapper and treat it as any nice citizen
# aka as AlertSender
