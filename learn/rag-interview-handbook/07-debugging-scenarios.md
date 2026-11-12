---
title: "RAG interview handbook, part 7: debugging scenarios"
description: "Eight broken-RAG scenarios, each with the first three checks to make and the likely fix."
date: 2026-11-11
track: rag-interview-handbook
series_order: 7
tags: [rag, interviews, debugging]
draft: false
---
Part 7 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

Say your first three checks in order, then the fix. The interviewer is testing your diagnosis path.

### X1. Answers were right last month and are wrong this month, and nobody changed the code.
"Nobody changed the code" doesn't mean nothing changed. Data, models, dependencies and users all change.

1. Run the frozen golden set on today's stack. If the scores dropped, something in the stack changed. If they didn't, the traffic changed.
2. Diff everything that isn't code. The model version, embedding model, index version, parser and OCR library versions, and any prompts or config stored outside the repo.
3. Compare this month's query mix with last month's. A new product, a new document type or a seasonal topic can shift what people ask.

Also check the corpus: new documents that conflict with old ones, or an ingestion job that quietly stopped.

*Likely fix:* pin versions, schedule golden-set runs, fix the ingestion drift, and add the new query types to the golden set.

### X2. Traces show the right chunk was retrieved, but the answer ignores it.
1. Read the exact prompt the model received. Is the chunk actually in it? A token limit may have cut it, or a dedup or filter step after retrieval may have dropped it.
2. Check its position. Is it buried in the middle of 20 chunks?
3. Check for conflicts. Is there an older or contradicting chunk next to it? And does the chunk make sense on its own, or did it lose its heading?

Also check the question type. A list question often stops after the first item.

*Likely fix:* fewer chunks with the best first, a heading prefix on each chunk, and an explicit extraction step before answering. Resolve conflicts with dates and versions.

### X3. Queries with exact product codes return irrelevant results.
1. Confirm BM25 is actually in the retrieval path. Many systems are dense-only, and embeddings blur codes.
2. Check how the analyzer splits a code. "AB-1234-X" may become "ab", "1234" and "x", which match lots of unrelated text.
3. Try an exact lookup. Is the code in the index at all, or did parsing mangle it?

*Likely fix:* a keyword field with a custom analyzer that keeps codes whole. A regex that spots codes and goes straight to an exact lookup or filter. And hybrid retrieval, so BM25 can carry these queries.

### X4. Recall fell sharply after you added the permission filter.
1. Measure recall with and without the filter, on queries where the test user may see the gold document. That separates "correctly hidden" from "wrongly lost".
2. Check how selective the filter is, and whether it runs before or after the vector search. Filtering after the search drops results from a fixed top-k. pgvector's docs give an example: if a filter matches 10% of rows, HNSW with the default ef_search of 40 returns only about 4 rows.
3. Check the index on the permission field. Does it exist, and was it built before the field was filled in?

*Likely fix:* exact pre-filtering for very selective filters. A filter-aware index, like Qdrant's payload indexes or pgvector's iterative scans from version 0.8. Partitions by tenant or group. Or an index rebuild.

### X5. p95 latency jumped from 1.5 s to 6 s after you added a reranker.
1. Profile the stage. Confirm the reranker is the cause, and look at the distribution. If only the tail is slow, suspect queueing.
2. Check the candidate count and chunk length. Cross-encoder cost grows with both. 200 candidates of 512 tokens is far heavier than 50 of 256.
3. Check the device and batching. Is it running on CPU by mistake? Are candidates scored in one batch or one at a time? Is one GPU queueing requests under load?

*Likely fix:* fewer candidates, say the top 50, and truncated passages. A smaller or distilled reranker, on a GPU with batching. And a timeout that falls back to the fused order.

### X6. Arabic queries score far lower than English on the same documents.
1. Slice recall by language at each stage: retrieval, reranking and the final answer. Find where the gap opens.
2. Inspect the parsed Arabic text and the analyzer output. Look for reversed text from PDFs, presentation-form characters, and a BM25 index with no Arabic normalisation.
3. Check the test set. Were the Arabic queries machine-translated from English? Translated queries can be unnatural and unfair to the system.

*Likely fix:* fix parsing, with NFKC and the correct right-to-left order. Add Arabic normalisation and light stemming. Try a stronger multilingual embedder or reranker. And add a real dialect test slice.

### X7. Users report answers quoting a policy that was replaced months ago.
1. Find the chunk behind the answer. Which document and version did the trace cite?
2. Check the version metadata. Does the index know effective dates? Are the old and new versions both indexed, with nothing marking the old one as replaced?
3. Check deletions and caches. Was the old document removed at the source but not from the index? Is an answer cache serving an old answer?

*Likely fix:* effective dates and "replaced by" links in the metadata, so superseded versions are filtered out or ranked down. Tombstones for deletions. Cache invalidation when a document changes. And a freshness monitor.

### X8. Offline metrics improved, but the thumbs-up rate fell in production.
1. Check latency and answer length. The new version may be slower or wordier, and users dislike that even when answers are more correct.
2. Slice by language and intent. The drop may sit in one slice the golden set barely covers.
3. Read failing sessions, and check the experiment itself. Look for a sample ratio mismatch, a changed feedback button, a logging bug or a novelty effect.

*Likely fix:* refresh the golden set from production traffic, because it has drifted away from what users ask. Add guardrail metrics like latency, length and abstention, then re-test.

## Sources

- [pgvector](https://github.com/pgvector/pgvector)
