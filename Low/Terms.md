- aggregation root vs composition root
  - agg root (DDD)
    - main entity that controls some related group of objects
  - composition root
    - this is the app "edge" where root level deps are loaded and connected
- DSL = Domain Specific Language
  - it's like a mini language that's meant to be a specific job as opposed to a general one like pyhon
  - external DSL = sql, regex, css
  - internal (embedded) DSL = just a fancy name if you make a nice library api that's easy to use

For example, when people say fluent dsl, they basically mean objects support chaining like this

```python
query = (
    QueryBuilder("orders")
    .where(amount_gt=100)
    .order_by("created_at")
    .limit(10)
    .build()
)
```
