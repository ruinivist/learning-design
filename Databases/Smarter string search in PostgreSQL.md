# Smarter string search in PostgreSQL

This is a writeup of me trying to improve search over strings in PostgreSQL to make "fuzzy-like" and typo-tolerant while still being
fast enough such that everything still lives in pg ( so not elasticsearch of equivalent off db alternatives ).

## The dataset

Around ~123k stream titles from a snapshot of all live streams taken point in time. These contain emojis and different languages
as well.

## Defining a "good" search

We NEED to do some analysis on the data to even answer the question as to what is a good search and build some manual test cases that
cover the sort of behavior that we want.

Here are some questions to ask and answer.

_data quality check like nulls, blank values, duplicates to spot anomalies_

```sql
SELECT
    count(*) AS rows,
    count(DISTINCT title) AS distinct_titles,
    count(*) FILTER (WHERE title IS NULL) AS null_titles,
    count(*) FILTER (WHERE btrim(title) = '') AS blank_titles
FROM streams;
```

| rows   | distinct_titles | null_titles | blank_titles |
| ------ | --------------- | ----------- | ------------ |
| 123476 | 113414          | 0           | 2685         |

For out case, not having nulls is good, and it's ok to ignore the blank titles as well.

_what is the length of strings we are dealing with and their distribution?_

A lot of sql magic here, that windowing using "over" does a LOT here.

```sql;
SELECT
  (length(title) / 10) * 10 AS length_bucket,
  count(*) * 100.0 / sum(count(*)) OVER () AS pct,
  sum(count(*)) OVER (
    ORDER BY (length(title) / 10) * 10
  ) * 100.0 / sum(count(*)) OVER () AS cumsum_pct
FROM streams
GROUP BY (length(title) / 10) * 10
ORDER BY length_bucket;
```

| length_bucket | pct                    | cumsum_pct           |
| ------------- | ---------------------- | -------------------- |
| 0             | 13.7338430140270174    | 13.7338430140270174  |
| 10            | 17.9808221840681590    | 31.7146651980951764  |
| 20            | 15.9512779811461337    | 47.6659431792413101  |
| 30            | 12.8041076808448605    | 60.4700508600861706  |
| 40            | 10.1874048398069260    | 70.6574556998930966  |
| 50            | 8.0533868929994493     | 78.7108425928925459  |
| 60            | 6.2611357672746121     | 84.9719783601671580  |
| 70            | 4.5782176293368752     | 89.5501959895040332  |
| 80            | 3.3796041335968123     | 92.9298001231008455  |
| 90            | 2.4352910687097088     | 95.3650911918105543  |
| 100           | 1.6691502802163983     | 97.0342414720269526  |
| 110           | 1.1605494185104798     | 98.1947908905374324  |
| 120           | 0.84631831287051734750 | 99.0411092034079497  |
| 130           | 0.83498007710000323950 | 99.8760892805079530  |
| 140           | 0.12391071949204703748 | 100.0000000000000000 |
