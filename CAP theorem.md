# CAP theorem

_If a network partition happens, a distributed system cannot simultaneously guarantee both strong consistency and availability._

In literature it's usually written as pick two of three but this above is what it boils down to. You have to either assume no partitions or give up one of those due to a partition.

- C = consistency = linearised reads ( does not necessarily mean pefect timing guarantees on parallel requests, that can never happen given we are communicating over net )
- A = availability = some response is sent always
- P = partition tolerant = even if there is a blackout/communication error over some nodes, system still continues "working", ofc you define what working is. Per CAP, that cannot be
  both C and A.

That is the main idea, the rest of it is me asking chatgpt to invent scenarios and applying this.

## Scenarios

### Quorom read writes

N (replicas) = 3
R (replica reads to ack success) = 2
W (replica writes to ack success) = 2

let replicas be 1, 2 and 3

Argument being, even if 3 is gone, I can still have CAP as my reads and writes are "consistently" ( once again we've defined "consistency" to be the 2 quorom agreement case, it's different from
a perfect low level linearisation ) working.

It's majority CAP but think of the smaller partitions case ( it's always the smaller one ), a client talkingt to the partitioned 3 will have no response as it'll keep on waiting to get a majority.

### Eventual consistency is not C

C is linearised read writes, there must exist SOME total order, that can explain the system state at EACH point not just final

- CRDTs ( conflict free replicated data types ) solve CAP? No, as they again can only give eventual consistency. You can at best keep on serving requests but won't have C.
- Perfect timestamping / last write wins

The naive argument I hear often is that what if both requests have the exact same timestamp, that can very very easily resolved by just using timestamp + counter or increasing precision; arguing that makes
no sense, always work under the perfect timestamping assumption aka no collisions. The problem remains even when timestamps are different as how would you convey that information about timestamps in the
first place, that just shifts the frame and you still have the same problem; all they help with are an eventual re-conciliation.

### Leader election

Split brain as both sides can elect seprate leader on a split. If one side refuses based on thresholds, you lose A.

### My CAP system is 99.bazillion 9s % available so we practically beat CAP

CAP is defined for "when the network is partitioned", it's conditioned on that, the fact that it did not happen in reality makes no difference.
"Had" it happened, system would lose A or C.
