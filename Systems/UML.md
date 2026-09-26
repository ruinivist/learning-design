# UML

Just enough of it so that it's still somewhat useful.

```text
[Service]                 component

Service A ---> Service B  request/dependency

DB
====                     database/storage
field1
field2

A 1 ----- N B            one-to-many

A ---> B                  synchronous call

A - - -> B                asynchronous/event

A <----> B                bidirectional communication
```
