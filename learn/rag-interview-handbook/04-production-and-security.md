---
title: "RAG interview handbook, part 4: production and security"
description: "Eleven questions on latency, cost, caching, updates, permissions, prompt injection, poisoning, multi-tenancy, self-hosting and monitoring."
date: 2026-11-11
track: rag-interview-handbook
series_order: 4
tags: [rag, interviews, production, security]
draft: false
---
Part 4 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

### D1. Give a latency budget for a chat RAG. Where does the time go?
In chat, users feel the time to the first token, so I budget for that. These are planning figures. I'd replace them with real measurements in the first week.

1. Rewrite the query with a small model: about 150 ms.
2. Embed the query: about 20 ms.
3. Retrieve with BM25 and vector search in parallel, then fuse: about 50 ms.
4. Rerank around 50 candidates with a cross-encoder on a GPU: about 200 ms.
5. The LLM's first token: about 800 ms. This grows with prompt length.

That's about 1.2 seconds to the first token. Then the answer streams. 300 tokens at 50 to 150 tokens a second takes another 2 to 6 seconds, so 3 to 7 seconds end to end. Streaming hides most of that, because the user starts reading after about a second.

Most of the time goes to the LLM, then the reranker. Shorter prompts cut the first-token time. So fewer, better chunks help both speed and quality.

One catch: streaming limits checks after generation. If I need a groundedness or PII check, I can buffer one sentence at a time and check it before showing it. Or I stream and pull back a sentence that fails. In sensitive domains, I buffer.

*If they ask, "What do you drop first under load?":* the query rewrite for queries that don't need it, like a standalone first question. Then I cut reranker depth, say from 50 candidates to 20. If the reranker times out, I fall back to the fused order. I can also route to a smaller LLM. I never drop the permission filter.

### D2. Estimate the cost of 100K queries a day. What are your biggest levers?
Cost is tokens times price, so I start with the tokens. Say a 500-token system prompt, 500 tokens of chat history and five 500-token chunks. That's 3,500 tokens in and about 300 out.

At an example price of $3 per million input tokens and $15 per million output tokens:
- Input: 3,500 × $3 per million = $0.0105.
- Output: 300 × $15 per million = $0.0045.
- Total: $0.015 a query.

At 100K queries a day, that's $1,500 a day, or about $45,000 a month.

Embedding the queries is tiny next to that. If the reranker is a hosted API priced per search, I'd check it, because 100K searches a day adds up.

My biggest levers, in order:
1. Fewer, shorter chunks. Input is 70% of the cost here.
2. Model routing. Easy questions go to a smaller, cheaper model.
3. Prompt caching for the fixed prefix, like the system prompt. Providers charge much less for cached tokens.
4. An answer cache for repeated public FAQs.
5. Shorter answers, because each output token costs five times more here.

*If they ask, "What does doubling top-k cost?":* going from 5 to 10 chunks of 500 tokens takes input from 3,500 to 6,000 tokens. The query goes from $0.015 to $0.0225. That's 50% more, or about $22,500 more a month. First-token latency rises too, and so does the lost-in-the-middle risk. I'd only do it if the eval shows a recall gain worth that.

### D3. What do you cache? What makes semantic caching dangerous?
I cache from the safest layer up.

1. Query embeddings, keyed on the normalised query and the embedding model version.
2. Retrieval results, keyed on the query, the tenant, the user's permission set and the index version. When the index changes, so does the version, and old entries stop matching.
3. The fixed prompt prefix, through the provider's prompt caching.
4. Exact-match answers, for public FAQs only. They get a short expiry and are cleared when the source document changes.

Semantic caching returns a stored answer when a new query is merely similar to an old one. It's dangerous for three reasons.
- Near-duplicates can differ in exactly the part that matters: an entity, a number, a date or a negation. "Can I cancel within 14 days?" and "Can I cancel after 14 days?" embed almost the same.
- Cached answers go stale when documents change.
- It can cross users. If the key ignores permissions, one user gets an answer built from documents they can't see.

*If they ask, "Refund for order 123 vs order 124?":* those embed almost the same, so a semantic cache would serve order 123's answer for order 124. That's a wrong answer and a privacy leak. Anything about a specific account, order or user skips the answer cache and goes to the live API. If I use a semantic cache at all, it's for generic content only. It needs a high similarity threshold, and IDs, numbers and dates must match exactly.

### D4. Documents change daily. How do updates and deletions stay consistent?
I treat ingestion as an ongoing sync, not a one-off load.

1. Detect changes. Use webhooks or change feeds from the source where possible. Otherwise, compare modified times or hashes on a schedule.
2. Hash at two levels. A document hash skips unchanged documents. A chunk hash means I only re-embed chunks whose text changed.
3. Upsert idempotently, with stable chunk IDs, so a retried job never creates duplicates.
4. Propagate deletes as tombstones. A deleted source document is removed from the vector index, the keyword index and every cache. The tombstone also stops a delayed job from adding it back.
5. For big changes, like a new embedding model or chunker, build a new index version in the background. Then switch an alias in one step, so queries never see a half-built index.
6. Track freshness lag: the time from a change at the source to it being searchable.

Chunker choice matters here. An October 2026 study used 120 real Wikipedia revision pairs. Fixed-size chunking forced 57 to 68% of embeddings to be recomputed, against 38 to 56% for recursive chunking. With fixed windows, one inserted sentence shifts every boundary after it. Structure-aware chunks keep an edit local.

*If they ask, "How fast must a deleted document vanish?":* that's a policy decision, so I'd agree it with legal and the data owner. For revoked access and legal deletions, I'd aim for minutes, on a fast path, not the nightly batch. It must vanish from indexes, caches and traces. And I'd test it: delete a canary document and check it stops appearing within the target time.

### D5. How do you enforce document permissions? Why is post-generation filtering wrong?
I enforce permissions at retrieval.

Each chunk carries access metadata from the source system: the tenant, the allowed groups or users, and a sensitivity label. I sync it from the source of truth, like SharePoint or Google Drive permissions, together with the content.

At query time, I resolve the user's identity and groups. I pass them as a filter into both the vector search and the keyword search. The search runs as the user, never as a service account that sees everything. And the filter runs inside the search, so the top-k comes only from documents the user may see.

Filtering after generation is too late. The restricted text has already reached the model, and maybe the logs, traces and caches. The model may paraphrase it, so an output filter can't reliably spot it. And a prompt injection could push the model to leak it.

I'd add automated leak tests: test users with known permissions, plus canary documents holding unique strings. An alert fires if a canary string ever reaches the wrong user.

*If they ask, "What happens when group membership changes?":* I store group IDs on chunks and resolve the user's groups at query time, so a membership change applies at once. That's why I prefer groups over long lists of user IDs on each chunk. If a document's permissions change, I update the chunk metadata only, with no re-embedding. Caches keyed on the permission set simply miss. The gap to watch is sync lag, so revocations get a fast path.

### D6. Explain EchoLeak. Which controls would have stopped it?
EchoLeak was a zero-click attack on Microsoft 365 Copilot. Aim Security found it, and it was disclosed in 2025 as CVE-2025-32711. Microsoft fixed it on the server side.

The chain had four steps.
1. The attacker emails the victim. The instructions inside are written as if for the human reader and never mention AI. So Microsoft's cross-prompt injection classifiers, known as XPIA, didn't flag it.
2. Later, the victim asks Copilot a work question. Copilot's retrieval pulls in that email because it looks relevant, and Copilot follows its instructions.
3. The instructions tell Copilot to put sensitive data from its context into a link. Copilot normally removes external links, but reference-style Markdown slipped past that.
4. The link was an image. Clients load images automatically, so no click was needed. The image URL used an allowed Microsoft Teams endpoint that fetches outside URLs, so the content security policy let it through. The data left inside that request.

The lesson: each control was bypassed on its own, so you need layers.
- Treat retrieved content as untrusted data. Mark it clearly in the prompt, and never give it the user's authority.
- Clean the output. Strip or rewrite links and images, including reference-style Markdown.
- Allowlist outbound requests tightly, with no domain that fetches arbitrary URLs.
- Least privilege. The assistant sees only what the task needs.
- Red-team with injections hidden in emails and documents, not just typed into the chat.

*If they ask, "Which layer do you build first?":* output and egress control. It's deterministic, it doesn't depend on spotting clever wording, and it stops the data leaving even when the injection works. Classifiers miss things, as EchoLeak showed. Then least privilege, then injection detection as an extra layer.

### D7. How does knowledge poisoning work, and how do you defend against it?
Knowledge poisoning means an attacker gets text into your corpus that will be retrieved for a target question and will steer the answer.

PoisonedRAG showed how little that takes. Each poisoned text has two parts. One part makes it rank for the target question. In the simplest version, it just contains the question itself. The other part states the attacker's answer convincingly. With five such texts per target question, in a knowledge base of millions of texts, they reported about 90% attack success. That's a research setting, but the mechanism is simple.

It works because retrieval rewards similarity, not truth, and the model trusts its context.

My defences, in layers:
- Control who can write. Authenticate sources, and only ingest from approved ones.
- Review at ingestion. Content from lower-trust sources gets checked for injection patterns and sudden large changes.
- Rank with provenance. Store a trust level per source, and favour authoritative sources over user-generated content.
- Cluster near-duplicates. Several near-identical chunks that all match one query is a warning sign. I also limit how many context chunks come from one source.
- Monitor. Track which documents drive answers, and alert when a new document suddenly dominates a popular query.
- In the prompt, tell the model to flag conflicting sources rather than silently pick one.

*If they ask, "What if the source is your internal wiki?":* then the attacker could be an insider or a hijacked account, and many people can edit a wiki. I'd use its edit history. Weight pages by owner and review status, show the last editor and date in citations, and alert on edits to high-traffic pages. For critical topics like policies, I'd answer only from an official, controlled source, and treat the wiki as secondary.

### D8. One index or many for multi-tenant RAG?
It depends on three things: how many tenants there are, how uneven their sizes are, and how strict the isolation must be.

Option one is a shared index, with a tenant ID on every chunk and a mandatory filter. It's the most efficient for many small tenants, and vector databases like Qdrant support it with an indexed tenant field. The risk is that one missing filter leaks data. So the filter lives in one place, a single data-access layer, and is never left to each caller.

Option two is a partition or collection per tenant. It gives stronger isolation and easy per-tenant deletion and tuning. But each collection has overhead, and thousands of them get painful to run.

Option three is a hybrid. Small tenants share an index, and large or regulated tenants get their own. That's usually where I land.

Whatever I choose, I test cross-tenant leakage automatically, with canary documents per tenant. And I add per-tenant quotas and rate limits, so one tenant can't starve the others.

*If they ask, "What if one tenant holds 80% of the data?":* I'd give that tenant its own collection or shard, sized and tuned for it. In a shared index, a small tenant's filter matches a tiny fraction of the points. That's the hard case for filtered vector search: the engine either loses recall or falls back to slow scanning. Splitting the big tenant out also lets me scale and bill it separately.

### D9. When do you self-host the LLM and embeddings? What do you measure?
Four things push me to self-host.
- Data rules: data can't leave the country or the network. That's common in banking and government.
- Volume: at steady, high volume, owned GPUs can beat per-token prices.
- Latency: a dedicated model nearby is faster and more predictable.
- Customisation: fine-tuned embedders or rerankers.

Embeddings and rerankers are the easy first step. They're small and cheap to run, and running them locally keeps the corpus local too. I'd serve them with Hugging Face's Text Embeddings Inference, TEI. The LLM is the bigger decision. I'd serve it with vLLM, for batching and throughput.

What I measure:
- Quality on our own golden set, not a public leaderboard. Retrieval recall for embedders, and correctness and faithfulness for the LLM, per language slice.
- Cost at realistic GPU utilisation. A GPU that's busy 30% of the time costs three times as much per token as one that's busy 90% of the time.
- Latency: time to first token and p95, under real concurrency.
- The ops load: on-call, upgrades, security patches and capacity planning.

At Linnaea, I did exactly this for vision-language models. I benchmarked open models locally as replacements for the commercial API, with accuracy and latency promotion criteria. A model would only replace the API if it met both.

*If they ask, "Where is the break-even?":* I'd compute it, not guess. Self-hosting costs GPUs plus engineering time. The API costs monthly tokens times the price. Break-even is where those cross, and it moves a lot with utilisation. Steady, high traffic favours self-hosting. Spiky or low traffic favours the API, because idle GPUs still cost money. And if data rules forbid the API, there's no break-even question.

### D10. What do you log per request, and what must you never log?
I log enough to replay and debug any answer:
- a request ID, the tenant and a pseudonymous user ID
- the raw query and the rewritten query
- the retrieved chunk IDs, with their retrieval and rerank scores and ranks
- the final prompt, or enough to rebuild it
- the model, prompt, embedding and index versions
- the answer and its citations
- token counts, latency per stage and cost
- any user feedback

With that, when an answer is wrong, I can see which stage failed. Retrieval missed it, the reranker dropped it, or the model ignored it. And each bad trace can become a golden-set item.

What I never log: secrets like API keys and tokens, passwords, card numbers, or unredacted personal data. I redact personal data before it reaches the logs. Traces also contain document text, so access to them follows the same permissions as the documents. Otherwise the tracing system becomes the leak.

*If they ask, "How long do you keep traces?":* only as long as the purpose needs, agreed with legal. For example, full traces for 30 days for debugging. After that, only aggregate metrics and reviewed, redacted samples. Deletion requests must reach the traces too.

### D11. A vendor silently updates a model. How do you catch the regression?
First, prevent it. I pin dated model versions where the vendor offers them, rather than floating aliases like "latest". And I log the model version returned with every response.

Second, detect it. I run the golden set on a schedule, say nightly, against the production setup. I compare it with the last baseline using a paired test. The same run gates every change I control: model, prompt, parser or index.

Third, watch production signals that need no labels. Answer length, abstention and refusal rates, citation rate, reranker score distributions, and judge scores on a sample. A sudden shift on a day with no deploy points to the vendor.

When an alert fires, I compare outputs before and after on the same queries. Then I roll back to a pinned version, adjust the prompt, or switch providers.

*If they ask, "What if the vendor won't pin?":* then I treat the model as a moving dependency. I run a small canary set more often, maybe hourly. I keep a second provider or an open model behind the same interface as a fallback. And I'd ask for advance notice of model changes in the contract.

## Sources

- [Chunk Recomputation under Real Document Revisions](https://arxiv.org/abs/2610.31019), Oct 2026
- [EchoLeak case study](https://arxiv.org/abs/2509.10540)
- [PoisonedRAG](https://arxiv.org/abs/2402.07867)
- [OWASP LLM08:2025, vector and embedding weaknesses](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/)
- [Qdrant: vector search filtering](https://qdrant.tech/articles/vector-search-filtering/)
