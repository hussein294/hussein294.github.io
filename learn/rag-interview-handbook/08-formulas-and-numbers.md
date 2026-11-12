---
title: "RAG interview handbook, part 8: formulas and numbers"
description: "The formulas, quick arithmetic and questions to ask that come up in RAG interviews, on one page."
date: 2026-11-11
track: rag-interview-handbook
series_order: 8
tags: [rag, interviews, cheat-sheet]
draft: false
---
Part 8 of the RAG interview handbook: everything worth writing from memory, plus the arithmetic interviewers like to see done live.

## Formulas

- **BM25:** score(D, Q) = sum over query terms t of IDF(t) × f(t, D) × (k1 + 1) / (f(t, D) + k1 × (1 − b + b × |D| / avgdl)). IDF(t) = ln(1 + (N − n + 0.5) / (n + 0.5)), where n of the N documents contain t. Elastic's defaults: k1 = 1.2, b = 0.75.
- **RRF:** RRF(d) = sum over ranked lists r of 1 / (k + rank_r(d)), with k = 60.
- **MRR:** the average over queries of 1 / rank of the first relevant result.
- **nDCG@k:** DCG@k = sum for i = 1 to k of (2^rel_i − 1) / log2(i + 1), and nDCG@k = DCG@k / IDCG@k.
- **Test-set size for a proportion:** n ≈ z² × p × (1 − p) / e², with z = 1.96 for 95% confidence.
- **A/B sample size per arm** (about 80% power, 5% significance): n ≈ 16 × p × (1 − p) / δ². For a per-query metric randomised by user, multiply by 1 + (m − 1) × ICC, where m is queries per user.

## Arithmetic to do live

- 1M vectors at 1,024 dimensions, float32: 4.1 GB before index overhead.
- The same with scalar quantization (4x): about 1 GB.
- The same with binary quantization (32x): 128 MB of vectors, plus graph links, plus the originals on disk for rescoring.
- 90% precision within ±3 points: 385 queries per slice.
- Margin on 80% accuracy: ±7.8 points with 100 queries, ±3.9 with 400.
- Zero leaks in 300 red-team tests: a 95% one-sided upper bound of about 1% (the rule of three), if the tests were random draws.
- A/B test at a 30% baseline, detecting 2 points: about 8,400 users per arm.
- 3,500 tokens in and 300 out, at an example $3 and $15 per million: $0.015 a query, or $45,000 a month at 100K queries a day.

## Questions to ask your interviewers

1. What does your RAG system look like today, and what is its most common failure?
2. How do you measure answer quality now, and who owns the test set?
3. What are your data and hosting constraints?
4. How much of this role is new pipelines, and how much is improving existing ones?
5. What would make this hire a success at 90 days?
6. Who would I work with day to day?

## Sources

- [Seven Failure Points When Engineering a RAG System](https://arxiv.org/abs/2401.05856), Barnett and colleagues
- [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval), Anthropic
- [When Is Complex Chunking Worth It?](https://arxiv.org/abs/2608.16586), CIKM 2026
- [Does Document Structure Help Dense Retrieval?](https://arxiv.org/abs/2610.10170), Notre Dame, Oct 2026
- [Chunk Recomputation under Real Document Revisions](https://arxiv.org/abs/2610.31019), Oct 2026
- [Optimizing RAG Pipelines for Arabic](https://arxiv.org/abs/2506.06339)
- [Lost in the Middle](https://arxiv.org/abs/2307.03172)
- [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
- [pgvector](https://github.com/pgvector/pgvector), [Qdrant filtering](https://qdrant.tech/articles/vector-search-filtering/) and [Qdrant quantization](https://qdrant.tech/documentation/guides/quantization/)
- Elastic: [BM25 settings](https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity) and [RRF](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion)
- [HyDE](https://arxiv.org/abs/2212.10496), [ColBERTv2](https://arxiv.org/abs/2112.01488) and [BGE-M3](https://huggingface.co/BAAI/bge-m3)
- [EchoLeak case study](https://arxiv.org/abs/2509.10540), [PoisonedRAG](https://arxiv.org/abs/2402.07867) and [OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)
- [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/), Microsoft Research
- [Is GraphRAG Needed?](https://arxiv.org/abs/2606.25656), AWS and Cisco, Jun 2026
- [Is Grep All You Need?](https://arxiv.org/abs/2605.15184), May 2026
