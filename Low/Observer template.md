# Observer

- Subject ( who )
- Observers ( by whom )
- sub/unsub ( by observers )
- notify ( by subject )

## Python

Two models, if the subject passes "this" and the observers then call on additional methods
on the subject to fetch the data that is a pull model. Problem is if the observers all
call some expensive method on the subject that can be slow.

Push model expects that subject KNOWS what the observer needs, computes it and passes
just that data, observers do not make another call to fetch it.

Impl looks like this for pull method

```python

from abc import ABC, abstractmethod


class Observer(ABC):
    @abstractmethod
    def update(self, subject):
        pass


class Subject(ABC):
    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def detach(self, observer):
        self._observers.remove(observer)

    def notify(self):
        for observer in self._observers:
            observer.update(self)
```
