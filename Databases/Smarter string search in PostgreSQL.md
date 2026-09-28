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

For our case, not having nulls is good, and it's ok to ignore the blank titles as well.

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

What we notice is that most of the titles are failyr short, 80% of them are less than 50 characters.
When building an evaluation metric, we should then try to mirror such a distribution and focus more on the
shorter titles than catering to longer titles.

_what about repeated data?_

How much of stream titles are verbatim the same ( with just trimming for spaces at ends )?

```sql
SELECT
  lower(btrim(title)) AS normalized_title,
  count(*) AS stream_count
FROM streams
WHERE btrim(title) <> ''
GROUP BY lower(btrim(title))
HAVING count(*) > 1
ORDER BY stream_count DESC
LIMIT 20;
```

| normalized_title | stream_count |
| ---------------- | ------------ |
| fortnite         | 416          |
| warzone          | 181          |
| roblox           | 126          |
| wolverine        | 121          |
| my stream        | 107          |
| fc27             | 107          |
| minecraft        | 100          |
| aniimo           | 98           |
| hi               | 96           |
| r6               | 90           |
| cod              | 85           |
| .                | 83           |
| ranked           | 83           |
| gaming           | 81           |
| chillin          | 76           |
| 2k27             | 73           |
| chill            | 72           |
| fc 27            | 68           |
| apex             | 67           |
| once human       | 66           |

Very small titles make up bulk of the distribution, same as the popular ones. Something like "hi" where we do an exact
match and rank based on similarity might be good from a text perspective but then this means our logic to search must
be smarter as well.

_What languages do I need to cover?_

I'll prefer just english but what's the distribution like.

```sql
SELECT
  language,
  count(*) AS stream_count
FROM streams
GROUP BY language
ORDER BY stream_count DESC;
```

| language | stream_count |
| -------- | ------------ |
| en       | 66742        |
| ru       | 11847        |
| de       | 9626         |
| fr       | 8325         |
| es       | 8029         |
| pt       | 7380         |
| ja       | 2248         |
| pl       | 1488         |
| it       | 1440         |
| ar       | 829          |
| zh       | 730          |
| uk       | 718          |
| nl       | 566          |
| cs       | 438          |
| tr       | 409          |
| hu       | 408          |
| other    | 355          |
| sv       | 318          |
| th       | 280          |
| fi       | 190          |
| da       | 186          |
| el       | 181          |
| no       | 151          |
| ro       | 141          |
| bg       | 116          |
| sk       | 85           |
| ko       | 58           |
| zh-hk    | 53           |
| tl       | 44           |
| hi       | 24           |
| ca       | 21           |
| id       | 20           |
| asl      | 15           |
| vi       | 11           |
| ms       | 4            |

English is overwhelming. I never planned on having any other language but this gives us a direction as to what
( if ever ) would need to be handled next.

_Do we handle non-ascii parts in search?_

```sql
SELECT
  count(*) FILTER (
    WHERE octet_length(title) > length(title)
  ) AS non_ascii_titles,
  round(
    count(*) FILTER (
      WHERE octet_length(title) > length(title)
    ) * 100.0 / count(*),
    2
  ) AS non_ascii_pct
FROM streams
WHERE btrim(title) <> '';
```

| non_ascii_pct | non_ascii_titles |
| ------------- | ---------------- |
| 36.53         | 44127            |

36% of the titles have non-ascii bits, that seems a bit too large. Maybe all they have
is emojis.
I want to skip non-ascii and instead filter them out as "words". What % os text are we skipping.

```sql
WITH words AS (
  SELECT word
  FROM streams
  CROSS JOIN LATERAL regexp_split_to_table(
    btrim(title),
    '\s+'
  ) AS split_words(word)
  WHERE btrim(title) <> ''
)
SELECT
  count(*) AS total_words,
  count(*) FILTER (
    WHERE octet_length(word) > length(word)
  ) AS skipped_words,
  round(
    count(*) FILTER (
      WHERE octet_length(word) > length(word)
    ) * 100.0 / count(*),
    2
  ) AS skipped_pct
FROM words;
```

| total_words | skipped_words | skipped_pct |
| ----------- | ------------- | ----------- |
| 822463      | 121699        | 14.80       |

That is still 14%, let's continue for now but we'll keep this in mind.

_most common words_

```sql
WITH words AS (
  SELECT
    streams.id,
    lower(word) AS word
  FROM streams
  CROSS JOIN LATERAL regexp_split_to_table(
    btrim(title),
    '[^[:alnum:]]+'
  ) AS split_words(word)
  WHERE btrim(title) <> ''
)
SELECT
  word,
  count(*) AS occurrences,
  count(DISTINCT id) AS titles
FROM words
WHERE word <> ''
GROUP BY word
ORDER BY titles DESC
LIMIT 30;
```

| word    | occurrences | titles |
| ------- | ----------- | ------ |
| the     | 8896        | 8040   |
| to      | 6100        | 5747   |
| discord | 5621        | 5567   |
| a       | 5531        | 5126   |
| 2       | 4699        | 4529   |
| on      | 4754        | 4505   |
| de      | 4866        | 4406   |
| and     | 4670        | 4390   |
| of      | 4408        | 4232   |
| stream  | 4246        | 4162   |
| 18      | 4036        | 4009   |
| live    | 4105        | 3981   |
| in      | 3812        | 3702   |
| with    | 3748        | 3683   |
| i       | 4053        | 3529   |
| s       | 3624        | 3424   |
| day     | 3390        | 3267   |
| 1       | 3476        | 3261   |
| 3       | 3492        | 3241   |
| drops   | 2858        | 2787   |
| for     | 2773        | 2670   |
| sunday  | 2555        | 2520   |
| en      | 2605        | 2509   |
| no      | 2524        | 2310   |
| playing | 2284        | 2269   |
| chill   | 2277        | 2257   |
| time    | 2179        | 2131   |
| new     | 2249        | 2115   |
| 7       | 2114        | 2081   |
| is      | 2106        | 2036   |

Numbers need to be handled in such a way that they do not distort.
Something like "the", "to" should also not be counted in randking, maybe a punctuation dataset
to skip also makes sense. But need to take into account for stop words in titles like
"The Last of Us"; I feel like it's becoming VERY rules based at this point.

_getting samples for typo correction_

```sql
WITH words AS (
  SELECT
    streams.id,
    lower(word) AS word
  FROM streams
  CROSS JOIN LATERAL regexp_split_to_table(
    btrim(title),
    '[^[:alnum:]]+'
  ) AS split_words(word)
  WHERE btrim(title) <> ''
)
SELECT
  word,
  count(DISTINCT id) AS titles
FROM words
WHERE word <> ''
  AND length(word) >= 4
GROUP BY word
HAVING count(DISTINCT id) BETWEEN 50 AND 200
ORDER BY titles DESC
LIMIT 30;
```

Length being more than 4 chars and occuring in 50 to 200 streams.

```sql
|word|titles|
|----|------|
|dota|200|
|battle|200|
|zombies|200|
|there|200|
|plus|199|
|dawnwalker|199|
|fantasy|198|
|https|197|
|daylight|196|
|gamer|195|
|1000|195|
|ghost|194|
|kingdom|194|
|fort|193|
|arena|193|
|hours|192|
|work|191|
|rust|190|
|through|190|
|squad|189|
|make|189|
|tourney|188|
|wird|188|
|directo|188|
|soir|188|
|race|187|
|découverte|187|
|content|185|
|affiliate|185|
|diamond|184|
```

_distribution on very short terms_

```sql

WITH words AS (
  SELECT
    streams.id,
    lower(word) AS word
  FROM streams
  CROSS JOIN LATERAL regexp_split_to_table(
    btrim(title),
    '[^[:alnum:]]+'
  ) AS split_words(word)
  WHERE btrim(title) <> ''
)
SELECT
  word,
  count(DISTINCT id) AS titles
FROM words
WHERE word ~ '^[a-z0-9]{2,3}$'
GROUP BY word
ORDER BY titles DESC
LIMIT 30;
```

| word | titles |
| ---- | ------ |
| the  | 8040   |
| to   | 5747   |
| on   | 4505   |
| de   | 4406   |
| and  | 4390   |
| of   | 4232   |
| 18   | 4009   |
| in   | 3702   |
| day  | 3267   |
| for  | 2670   |
| en   | 2509   |
| no   | 2310   |
| new  | 2115   |
| is   | 2036   |
| my   | 2023   |
| me   | 1947   |
| we   | 1826   |
| la   | 1763   |
| 24   | 1480   |
| dc   | 1477   |
| eng  | 1409   |
| it   | 1387   |
| up   | 1221   |
| 20   | 1193   |
| do   | 1164   |
| rp   | 1138   |
| fr   | 1124   |
| sub  | 1091   |
| you  | 1078   |
| wow  | 1071   |

A trigram search is weak on this as very few trigrams to match.
This should also be part of our test set.

_rare terms_

```sql
WITH words AS (
  SELECT
    streams.id,
    lower(word) AS word
  FROM streams
  CROSS JOIN LATERAL regexp_split_to_table(
    btrim(title),
    '[^[:alnum:]]+'
  ) AS split_words(word)
  WHERE btrim(title) <> ''
),
rare_words AS (
  SELECT
    word,
    count(DISTINCT id) AS titles
  FROM words
  WHERE word ~ '^[a-z]{5,}$'
  GROUP BY word
  HAVING count(DISTINCT id) BETWEEN 2 AND 10
)
SELECT word, titles
FROM rare_words
ORDER BY md5(word)
LIMIT 30;
```

> note the order by md5 for random shuffling

This just becomes garbled mess at low frequencies.

| word        | titles |
| ----------- | ------ |
| newshort    | 2      |
| hotzone     | 7      |
| whodis      | 2      |
| grandmasta  | 3      |
| dusklight   | 6      |
| despite     | 3      |
| enderal     | 2      |
| wantedrp    | 2      |
| oreilles    | 2      |
| lingote     | 3      |
| reversal    | 4      |
| farmin      | 5      |
| londres     | 2      |
| mensch      | 2      |
| brixies     | 4      |
| mogger      | 3      |
| siiii       | 2      |
| lesserafim  | 2      |
| tomato      | 2      |
| pubdcito    | 2      |
| vesna       | 5      |
| mentalidade | 2      |
| blaumeisen  | 2      |
| frente      | 4      |
| serotonin   | 2      |
| descuento   | 3      |
| danch       | 2      |
| trofeo      | 2      |
| majoras     | 4      |
| xanthe      | 2      |

### Finally defining an eval set

From the frequency bands above, this is the fixed set of source terms that the
different search approaches will be tested against.

| frequency class | term       | title count | reason selected                         |
| --------------- | ---------- | ----------: | --------------------------------------- |
| common          | discord    |        5567 | recurring platform boilerplate          |
| common          | fortnite   |        2026 | common game name and genuine subject    |
| medium          | dota       |         200 | recognizable game name                  |
| medium          | dawnwalker |         199 | longer, specific game/entity name       |
| medium          | zombies    |         200 | ordinary word and common gaming subject |
| short           | wow        |        1071 | short alphabetic and ambiguous term     |
| short           | rp         |        1138 | two-letter abbreviation                 |
| short           | r6         |         407 | short alphanumeric game abbreviation    |
| rare            | enderal    |           2 | rare game name                          |
| rare            | hotzone    |           7 | rare compound term                      |
| rare            | serotonin  |           2 | rare ordinary word                      |
| ambiguity       | chatting   |         230 | "chetting" may rank "getting" higher    |
| no match        | zzqvxx     |           0 | negative control                        |

Then the different "matching" cases need to be covered to check if the search itself is
typo-tolerant. The expected won't exactly match as I believe there would be some titles with
actual typos in them.

| source term | query     | case                   | expected relevant titles |
| ----------- | --------- | ---------------------- | -----------------------: |
| fortnite    | fortnite  | exact control          |                     2026 |
| fortnite    | fortite   | deletion               |                     2026 |
| fortnite    | fortnnite | insertion              |                     2026 |
| fortnite    | fortnire  | substitution           |                     2026 |
| fortnite    | fortntie  | adjacent transposition |                     2026 |
| chatting    | chatting  | exact control          |                      230 |
| chatting    | chetting  | ambiguous substitution |                      230 |

## Running some evals

Look a the pg-string-search-benchmars folder. This section is is just like a devlog of sorts.

- substring match should use words I feel. Results for r6 had stuff that were not r6 words.
- where does trigram go bad? Theoretically there should be a case where a long word, having trigrams to match against should come on top even though it's not related.
  - another is "getting" matched highly against "chetting" and ranks higher in results.

Another is this one

```sql
SELECT
  similarity('enderal', 'enderdrachenfight'),        -- 0.238
  word_similarity('enderal', 'enderdrachenfight');   -- 0.625
```

`similarity` would match all trigrams while `word_similarity` is allowed to choose a certain
good stretch inside the 2nd word. Not a problem here but good to know.

Another problem is that trigram search jsut won't work for cases short words.

```sql
SELECT word_similarity('hi', 'ho');  -- 0.333 this is just rejected at the 0.5 threshold
SELECT word_similarity('wow', 'woof meow meow woof');  -- 0.75
```

this causes the tail to be noisy even though exact ones match come first.

There CAN be cases where a non exact match ranks higher as well

```sql
SELECT
  word_similarity('dota', 'easydota') AS exact_substring,
  word_similarity('dota', 'flota do') AS no_exact_substring;
```

So in short, similarity is just bad as strings to long, and word sim can have a rank issue as well.

There's also "strict_word_similarity", specially for cases as above, this does not allow
word sim to cross word boundaries.

If you bake in the assumption that people are definitely searching across words then this
last one seems ideal but see this.

| Query      |                    Word matching | Strict matching |
| ---------- | -------------------------------: | --------------: |
| `chetting` |  1 of top 10 contains `chatting` |     9 of top 10 |
| `fortntie` | 10 of top 10 contains `fortnite` |  0 of 3 results |
| `enderal`  |                    85 candidates |   23 candidates |

```sql
SELECT
  word_similarity('fortntie', 'fortnite')        AS word_score,   -- 0.556
  strict_word_similarity('fortntie', 'fortnite') AS strict_score; -- 0.385
```

Apparently that swap disrupts multiple trigrams.

> a swapped pair is "harder" to solve in general, even with say edit distance which will
> be 2 for this; even though distributions on typos would def have a higher conc of swapped
> pairs

## trigrams as only a first pass candidate filter

For fuzzy/typo-tolerant, using trigrams to filer candidates on some low enough threshold, and
then applying a more complicated/slower algorithm that you could not have applied as a whole
is a hybrid approach of sorts.

```sql
EXPLAIN (ANALYSE, BUFFERS)
SELECT id, title
FROM streams
WHERE 'chetting' <% lower(title)
ORDER BY (
    SELECT min(levenshtein('chetting', word))
    FROM regexp_split_to_table(
        lower(title), '[^[:alnum:]]+'
    ) AS words(word)
    WHERE word <> ''
), word_similarity('chetting', lower(title)) DESC, id
```

That first `WHERE 'chetting' <% lower(title)` does a "is this within threshold"
then on the filtered ones we apply the two way sorting.

## Leaving it to the pros

Pg has solutions for such full text search and does a reasonable complicated transformtion for
allowing efficient searching on text.

> Refer https://www.postgresql.org/docs/18/textsearch-controls.html

At a high level, both document and the query into the same normalized vocabulary, then match those normalized terms. The idea is similar to vector embeddings and similarities we run there but this is not vector embeddings.

```
Document:
"The cats were running on mats"

        ↓ to_tsvector('english', ...)

'cat':2 'mat':6 'run':4
```

Pg drops the non entity bits like "were" and "on" and normalises too for example cats -> cat.
The number that follows is just the position in the sentence.

ChatGPT summarised how it works as this

```text
1. Linguistic processing
   raw text → lexemes
   tokenization, stemming, synonyms, stop words

2. Query language
   user text → Boolean/phrase expression

3. Retrieval
   GIN index finds matching documents

4. Ranking
   ts_rank / ts_rank_cd sorts the matches
```

Now this whole pipeline seems excellent, except this is not at all fuzzy or typo tolerant.
Can we do better? If only it did fuzzy search on the tokens it generated, it could almost
be perfect.

## The bright idea

One pg makes tokens of all stream titles, can I then trigram match my query against the tokens
to "guess" what typo was made and then use FTS using the corrected tokens.

At an initial note, this seems pretty good.

I put all tokens, doc count pairs in a table and then try to find "chet" in them

```sql
SELECT word, ndoc, similarity('chet', word) AS score
FROM search_words
WHERE word % 'chet' AND similarity('chet', word) > 0.5
ORDER BY ndoc DESC
LIMIT 10;
```

"chat" was not there at all and apparently similarity is just 0.25, I can use word_sim but that's
just slightly better.

Note that event "chet" is something that exists in the titles, Iw ant a combination of ndoc,
fuzzy + lev and then fts on that. Though this makes it hard to search for your actual query
as something popular would dominate.

```sql
SELECT word, ndoc,
       levenshtein('fortntie', word) AS edits,
       similarity('fortntie', word) AS trigram
FROM search_words
WHERE word % 'fortntie'
ORDER BY edits, trigram DESC, ndoc DESC
LIMIT 10;
```

| word      | ndoc | edits | trigram    |
| --------- | ---- | ----- | ---------- |
| fortnie   | 2    | 1     | 0.54545456 |
| fortnit   | 3    | 2     | 0.41666666 |
| fortnite  | 2009 | 2     | 0.3846154  |
| fortneit  | 1    | 2     | 0.3846154  |
| fortnlte  | 1    | 2     | 0.3846154  |
| fortniee  | 1    | 2     | 0.3846154  |
| fortnire  | 1    | 2     | 0.3846154  |
| fortnait  | 1    | 2     | 0.3846154  |
| fortnitee | 3    | 2     | 0.35714287 |
| fortite   | 1    | 2     | 0.30769232 |

Goes to show that we should use ndoc, even at the cost of not showing what was searched for exactly. A more popular term is search more anyways, for exact search we can have Google like semantics of quoting the "search term".

Codex made me a "divined score" computed as this

```sql
SELECT word, ndoc,
       levenshtein('fortntie', word) AS edits,
       similarity('fortntie', word) AS trigram,
       ln(ndoc + 1) - 2 * levenshtein('fortntie', word) AS score
FROM search_words
WHERE word % 'fortntie'
ORDER BY score DESC, trigram DESC
LIMIT 10;
```

I think it's just plain bad in the sense that it cannot be justified globally, at best heuristic
that I have no idea when it breaks.

| word      | ndoc | edits | trigram    | score               |
| --------- | ---- | ----- | ---------- | ------------------- |
| fortnite  | 2009 | 2     | 0.3846154  | 3.6058900010531216  |
| fortnie   | 2    | 1     | 0.54545456 | -0.9013877113318902 |
| fortune   | 138  | 3     | 0.30769232 | -1.0655260668693085 |
| for       | 2664 | 5     | 0.3        | -2.1120406634000553 |
| fortnit   | 3    | 2     | 0.41666666 | -2.613705638880109  |
| fortnitee | 3    | 2     | 0.35714287 | -2.613705638880109  |
| fort      | 191  | 4     | 0.4        | -2.7425046279722185 |
| fortnlte  | 1    | 2     | 0.3846154  | -3.3068528194400546 |
| fortnire  | 1    | 2     | 0.3846154  | -3.3068528194400546 |
| fortniee  | 1    | 2     | 0.3846154  | -3.3068528194400546 |

the claim of a high score seems to be due to the disproportionate ndoc for something with a
very low lev enough distance. The weighing too is a bit arbitary.

The 0.38 on the correct one seems too low, I noticed that using word_similarity again is much
better ( 0.55 score, same as fortnie ), so I'll use that but I do need to cover how exactly
that word sim works.

This as the search strategy => filter using trigrams, pick min lev, ndocs to tiebreak and then
send the first one to FTS, breaks for "fortntie" as it matches "fortnie" with 1 lev idst.

Seems like I would really need to do one of these

1. define a heuristic that takes ndoc into account as well always, instead of just for tie break
2. do a union of top k in the ranked corrected vocab.

At this point it's very much a design choice really, if we want the search to oppose and autofix
or still match the typo word if there is one in title exactly. I think later, systems should
not be needlessly smart.

> also a full FTS search would be rank repetitions of the same word higher
> what I got was titles that had fortnite twice or thrice.

What I had to do to fix was instead of "or"ing corrected terms, ensure the ranks are not
done in cross, the results from the first one should be first.

With this, the typo term comes first as we've decided it should, then the double usages rank
next which again is fair.

## perf

| Strategy  | What PostgreSQL did                                                                     | Execution |
| --------- | --------------------------------------------------------------------------------------- | --------: |
| Hybrid    | Found 2,134 titles, then split each title into words to calculate edit distance         | 28\.95 ms |
| Corrected | Found 70 vocabulary candidates, kept five, then used the full text index to find titles |  9\.60 ms |

I'm only comparing the hybrid vs vocab corrected on since those only those two were good enough.
