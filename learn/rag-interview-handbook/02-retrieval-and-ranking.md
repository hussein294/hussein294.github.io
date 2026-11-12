---
title: "RAG interview handbook, part 2: retrieval and ranking"
description: "Fourteen questions on BM25, vector indexes, filtering, quantization, fusion, rerankers and query rewriting, answered in full."
date: 2026-11-11
track: rag-interview-handbook
series_order: 2
tags: [rag, interviews, retrieval, bm25, vector-search, reranking]
draft: false
---
Part 2 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

### B1. Write BM25. What do k1 and b do?
BM25 scores a document D for a query Q by summing over the query terms t:

score(D, Q) = sum over t of IDF(t) × f(t, D) × (k1 + 1) / (f(t, D) + k1 × (1 − b + b × |D| / avgdl))

Here f(t, D) is how often t appears in D, |D| is the document's length, and avgdl is the average document length. IDF(t) = ln(1 + (N − n + 0.5) / (n + 0.5)), where n of the N documents contain t. Rare terms count more.

k1 controls saturation: how quickly repeats stop adding score. The tenth "refund" in a document adds much less than the first. Elastic's default is 1.2. At k1 = 0, only presence counts.

b controls length normalisation, from 0 to 1. Elastic's default is 0.75. At b = 1, long documents are fully penalised for their length. At b = 0, length is ignored.

*If they ask, "What happens on Arabic without stemming?":* recall drops. Arabic attaches prefixes and suffixes to words, like "and", "the", "with" and pronouns. So والكتاب and كتاب are different tokens, and BM25 can't match them. Normalisation plus light stemming fixes most of this.

### B2. Give three cases where BM25 beats dense retrieval.
1. Exact codes and IDs: error codes, product SKUs, invoice numbers and article numbers. An embedding blurs "E-4012" into "some error code", while BM25 matches it exactly.
2. Rare names and acronyms: a supplier's name, an internal project name, or a term the embedding model never saw in training.
3. Exact phrases: quoted text, legal terms of art, or a clause someone pasted in.

Short keyword queries, like "VAT invoice template", often favour BM25 too. That's why I run hybrid retrieval: BM25 catches the exact matches, and dense search catches the paraphrases.

*If they ask, "How do you tokenise a product code?":* keep it whole, in a keyword field, so "AB-1234-X" stays one token. I'd also index normalised variants, like without dashes and in lowercase, and add character n-grams if users type partial codes. And when a regex detects a code in the query, the system goes straight to an exact lookup.

### B3. Explain HNSW. What do M, efConstruction and efSearch trade off?
HNSW stands for hierarchical navigable small world. It's a graph in which each vector is a node linked to its near neighbours, arranged in layers. The bottom layer holds every vector. Each higher layer holds a random, shrinking subset. A node's top layer is drawn at random with a normalisation factor mL = 1 / ln(M), so each layer up has about M times fewer nodes.

Search starts at the sparse top layer. It walks greedily toward the query, then drops a layer and repeats. At the bottom layer it runs a wider search, keeping a list of candidates, and returns the nearest k.

The three parameters:
- M is the number of links per node, with 2M allowed on the bottom layer. Higher M gives better recall, but uses more memory and builds more slowly.
- efConstruction is the candidate list size while inserting. Higher gives a better graph, but a slower build.
- efSearch is the candidate list size at query time. It's the live dial between latency and recall, and it must be at least k.

pgvector's defaults are M = 16, efConstruction = 64 and efSearch = 40.

*If they ask, "What do deletes do to the graph?":* most engines only mark deleted nodes. They stay in the graph and still help navigation, but they're skipped in results. Heavy churn slowly degrades the graph's connectivity and recall, so you need periodic clean-up or a rebuild. In pgvector, that means vacuuming, and a reindex after heavy changes.

### B4. HNSW, IVF-PQ or DiskANN: when would you pick each?
- **HNSW** when the vectors fit in RAM and I want the best speed for a given recall. It's the default in most vector databases, and inserts are easy.
- **IVF-PQ** when memory is tight at large scale. IVF clusters the vectors into nlist groups with k-means, and a query only searches the nprobe nearest groups. PQ, product quantization, splits each vector into subvectors and replaces each with a one-byte code, so a 4 KB vector can shrink to 64 bytes. The costs: it needs training on sample data, and it loses recall, so you usually rescore the top results with the full vectors.
- **DiskANN** when the data is too big for RAM but you still want graph-quality search. It keeps the graph and the full vectors on SSD, with compressed vectors in RAM to guide the search. That makes billion-scale search possible on one machine.
- **Exact search** when the set is small. There's no index, and recall is perfect.

*If they ask, "At what size do you stop needing ANN?":* it depends on the latency budget and the hardware, so I'd measure. As a rough guide, exact search is usually fast enough up to about a hundred thousand vectors. It's also the right choice when a strict filter leaves only a few thousand rows.

### B5. Your permission filter matches 1% of chunks. What happens to ANN search, and what do you do?
If the filter runs after the ANN search, it starves the results. The index finds its usual candidates, and then the filter throws away 99% of them. pgvector's docs give an example: with a filter matching 10% of rows and the default efSearch of 40, you get about 4 rows back on average. At 1%, you'd get fewer than one.

What I do depends on how many rows match:
- When few rows match, pre-filter and score exactly. 1% of a million chunks is 10,000 vectors, which exact search handles in milliseconds, with perfect recall.
- Otherwise, use a filter-aware index. Qdrant adds extra graph links for filtered fields, and pgvector 0.8 added iterative scans, which keep searching until enough rows pass the filter.
- If the filter is something stable, like the tenant or the department, partition the index by it.

And I test recall under realistic filters, not just unfiltered recall, because that's where it breaks.

*If they ask, "What about two strict filters at once?":* the selectivities multiply. 1% and 10% together leave 0.1% of rows, if they're independent. That's firmly exact-scan territory. A good engine estimates the combined cardinality and picks its plan, and I'd check that ours does.

### B6. How much memory do 10 million 1024-dimension vectors need? What does binary quantization save?
Raw float32: 10 million × 1,024 dimensions × 4 bytes = 40.96 GB, before any index overhead.

Scalar quantization, one byte per dimension, cuts that by 4 times, to about 10 GB.

Binary quantization keeps one bit per dimension. That's 128 bytes per vector, or 1.28 GB in total: a 32 times saving on the vectors.

But the vectors aren't the whole index. HNSW links at M = 16 add roughly 1.3 to 1.6 GB, because the bottom layer stores up to 32 neighbour IDs per vector. So the real RAM total is around 2.6 to 2.9 GB. That's about 15 times smaller than raw, not 32. And you keep the full 41 GB of original vectors on disk, to rescore the top candidates, because binary codes alone lose accuracy.

*If they ask, "How does oversampling change this?":* oversampling means fetching more candidates with the binary codes, say 2 to 3 times k, and rescoring them with the full vectors from disk. RAM stays the same. You pay with more disk reads and some latency, and you get back most of the recall that binary codes lose.

### B7. Write RRF. Why k = 60? When would weighted fusion beat it?
Reciprocal rank fusion scores each document by summing over the ranked lists it appears in:

RRF(d) = sum over lists r of 1 / (k + rank_r(d))

It uses only ranks, never scores. That's its strength: BM25 scores and cosine similarities live on different scales, and RRF never has to normalise them.

k = 60 comes from the original 2009 paper by Cormack and colleagues, and it's Elastic's default. A large k flattens the curve. Rank 1 is worth 1/61, about 0.0164, and rank 10 is worth 1/70, about 0.0143. So no single list's top hit dominates. A document ranked 5th in both lists scores 2/65, about 0.031, and beats one ranked 1st in only one list.

Weighted fusion, like a tuned blend of normalised scores, can beat RRF when I have labelled data to tune the weight and the scores are reasonably comparable. Research on hybrid fusion has found that a tuned linear combination can outperform RRF, with only a small labelled set.

*If they ask, "What if one retriever returns junk?":* RRF still gives the junk credit for its ranks, because it ignores scores. A weak list can dilute a strong one. Fixes: weight the lists, drop results below a minimum score before fusion, route queries so the weak retriever is skipped where it's useless, and let the reranker clean up the final order.

### B8. Compare bi-encoders, cross-encoders and ColBERT.
- A **bi-encoder** embeds the query and each document separately, each into one vector. Document vectors are computed once, at indexing, so searching millions takes milliseconds. The catch: the query and the document never see each other, so fine distinctions get lost.
- A **cross-encoder** reads the query and one document together, as a single input, with full attention between them, and outputs a relevance score. It's the most accurate, but it runs once per query and document pair, at query time. So it only works on a shortlist, typically 50 to 200 candidates.
- **ColBERT** is the middle ground, called late interaction. It stores a vector for every token of every document. At query time, each query token finds its most similar document token, and those similarities are summed. That's called MaxSim. It's more precise than a bi-encoder and much cheaper than a cross-encoder, but the index is far larger, with one vector per token. ColBERTv2 compresses those vectors to shrink it.

*If they ask, "Where does each sit in your pipeline?":* bi-encoders, alongside BM25, do the first-stage retrieval over the whole corpus. A cross-encoder reranks the fused top 50 or so. ColBERT can replace the bi-encoder, or act as a cheaper reranker when latency is tight.

### B9. How many candidates do you send to a reranker, and how do you decide?
I decide empirically. I sweep the candidate depth, say 20, 50, 100 and 150, and plot two curves. One is final quality, like recall at 5 after reranking, or answer accuracy. The other is p95 latency. Quality usually climbs and then flattens. I pick the point where it flattens, as long as it fits the latency budget.

For reference, Anthropic's contextual retrieval experiments retrieved 150 candidates and reranked down to the top 20. A common range is 50 to 100, because cross-encoder cost grows linearly with the number of candidates.

*If they ask, "What happens on a timeout?":* the reranker gets a hard timeout. If it fires, I fall back to the fused order from RRF, which is still decent. I log it, and alert if timeouts rise. A slow reranker should never block an answer.

### B10. Can you use a reranker score as a confidence threshold?
Not the raw score. Reranker scores are specific to each model, they aren't calibrated probabilities, and their distribution shifts with query type and length. A score of 0.7 can mean "relevant" for one model and "maybe" for another.

What I'd do:
1. Calibrate on labelled data. Map the raw top score to the probability that the top result is truly relevant, using Platt scaling or isotonic regression.
2. Add features beyond the top score: the margin over the second result, and whether BM25 and dense retrieval agree.
3. Set the threshold on a dev set, and confirm it on a held-out test set.
4. Redo it after any model change, because the scores shift.

This is the same pattern as my OCR work at RDI. I calibrated confidence scores against character-level accuracy, so high-confidence cases could be automated and low-confidence ones routed to human review.

*If they ask, "How do you measure calibration?":* with a reliability diagram. Bin the predicted confidences, and compare each bin's average confidence with its actual accuracy. A well-calibrated model sits on the diagonal. Expected calibration error sums up the gap in one number, and the Brier score covers calibration and sharpness together.

### B11. Explain HyDE. When does it hurt?
HyDE stands for hypothetical document embeddings. Instead of embedding the user's short question, an LLM first writes a fake answer, a hypothetical document, and you embed that. A fake answer looks more like real documents than a question does, so it lands closer to them in embedding space.

It helps short queries with a vocabulary gap, where users phrase things very differently from the documents.

It hurts in three ways:
- The fake answer can drift. If the LLM invents wrong specifics, the search follows them.
- It adds an LLM call before retrieval: hundreds of milliseconds and extra cost on every query.
- It's useless or harmful for exact lookups, because the fake answer invents codes and names.

So I'd use it only for the query types where the golden set shows it helps, and keep the original query in the mix.

*If they ask, "Would you use it for account numbers?":* no. The LLM would invent a fake account number and pull the search toward it. Account lookups go to exact search, or straight to the account API.

### B12. A user asks, "What about the second one?" What must happen before retrieval?
The query has to be made standalone, because "the second one" means nothing to a search index. So before retrieval, an LLM condenses the chat history and the new message into a self-contained query. If my last answer listed three plans, "What about the second one?" becomes "What is the cancellation fee for the Premium plan?" It resolves the reference and carries over constraints from earlier turns.

Three details matter:
- Keep the user's raw text in the logs next to the rewrite, so bad rewrites can be debugged.
- Put multi-turn conversations in the golden set, because single-turn tests never catch this.
- Detect topic changes, so old context doesn't leak into a new question.

*If they ask, "What if the rewrite fails?":* if the reference is ambiguous, ask a short clarifying question, like "Do you mean the Premium plan or the Business plan?" If the rewrite step itself errors, fall back to searching with the new message plus the previous user turn. And I'd track rewrite failures as their own metric.

### B13. When do you decompose a query, and what does that cost?
I decompose when one query really holds several questions: multi-part questions, comparisons and multi-hop questions. For example, "Compare the refund rules for Egypt and Saudi Arabia" becomes two sub-questions, one per country. I retrieve for each, then merge the results before generating.

The costs: an extra LLM call to split the query, more retrieval calls, more context tokens and more latency. So I cap the fan-out, say at three or four sub-questions, run the retrievals in parallel, and only decompose when a classifier says the query is multi-part.

*If they ask, "How do you merge the results?":* each sub-question gets a quota of chunks, so one can't crowd out the others. I deduplicate, and label each chunk with its sub-question in the prompt, so the model knows which evidence answers which part. Then I rerank against the original question, keeping the quotas.

### B14. How do you make sure the newest valid document wins?
Upload date isn't enough. Documents get re-uploaded, backdated, or published before they take effect. So every chunk carries real version metadata: effective date, expiry date, version number, a status like draft, active or retired, and links saying which document replaces which.

Then:
- Retrieval filters out retired and superseded versions by default.
- For intents that need the current rule, like "What's the fee now?", I filter by effective date or boost recency.
- Citations show the document's date and version, so users can see what they're reading.
- If two valid documents genuinely conflict, the answer says so, rather than silently picking one.

*If they ask, "What if two valid documents disagree?":* first I check the scope. Often both are valid for different cases: different products, regions or customer types. Then the answer explains which applies when. If it's a real conflict, I show both with their dates and sources, flag it to the content owner, and for regulated answers, hand off to a human rather than guess.

## Sources

- [Elastic BM25 settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity)
- [Elastic reciprocal rank fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- [pgvector](https://github.com/pgvector/pgvector)
- [Qdrant: vector search filtering](https://qdrant.tech/articles/vector-search-filtering/)
- [Qdrant: quantization](https://qdrant.tech/documentation/guides/quantization/)
- [ColBERTv2](https://arxiv.org/abs/2112.01488)
- [HyDE](https://arxiv.org/abs/2212.10496)
- [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval), Anthropic
