---
title: "RAG interview handbook, part 6: system design scenarios"
description: "Four end-to-end RAG system design scenarios, worked through the way you would present them in a design interview."
date: 2026-11-11
track: rag-interview-handbook
series_order: 6
tags: [rag, interviews, system-design]
draft: false
---
Part 6 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

Same shape every time: clarify, define success, design, evaluate, break it, roll out. Ask questions before you propose anything.

### S1. Air-gapped contract Q&A: 50,000 scanned Arabic and English contracts, no internet, one GPU server.
*Clarify.* How many lawyers, and how many at once? How many pages per contract? At 20 pages, that's a million pages. Which GPU? Are contracts bilingual, and which language prevails? Who may see which contracts, by client or matter? And which questions matter most: finding a clause, comparing contracts, or lists like expiry dates?

*Success.* Lawyers must trust every citation, so citation precision comes first, judged by lawyers. Then clause recall, correct abstention when unsure, and a latency target, say under 10 seconds an answer. And zero leaks between matters.

*Design.*
- Everything is self-hosted: OCR, embeddings, reranker and LLM. Models arrive as signed offline bundles, with checksums and pinned versions. Nothing leaves the network.
- Ingestion: OCR each page, keeping page numbers and text boxes. Each page gets a confidence score, and low-confidence pages go to human review. That's directly my RDI work on OCR confidence calibration.
- Chunk by clause, using clause numbers and headings, with the contract title and clause heading as a prefix. Metadata: parties, contract type, dates, version and pages.
- Field extraction: an LLM pulls key fields into a database table. Parties, start date, end date, renewal terms, governing law. Rules validate them, like date formats and Hijri versus Gregorian dates.
- Retrieval: BM25 with Arabic and English analyzers, plus a multilingual embedder like BGE-M3. Fuse with RRF, then rerank with a multilingual cross-encoder.
- Generation: an open LLM sized to the GPU, quantized if needed, served with vLLM. It answers only from the retrieved clauses, with a citation per claim.
- Permissions by matter, applied as retrieval filters.

*The GPU trap.* One GPU serves OCR, embedding, reranking and the LLM. Batch OCR must not starve interactive queries. So bulk ingestion runs off-hours or in a low-priority queue, and GPU memory is reserved for the LLM.

*Pressure: "List every contract ending in 2027."* That's not a RAG question. Retrieval returns a top-k, so it can't list everything. It goes to SQL over the extracted end-date field. Dates from scans need their own accuracy check, so I'd measure extraction on a labelled sample. Uncertain dates get flagged, and each row links to its source page. I'd also ask what "ending" means when a contract auto-renews.

*Pressure: "A lawyer must trust each citation."* Each claim cites the contract, page and clause, with an exact quote. A deterministic check then confirms the quote really exists in the source text. A claim whose quote fails is dropped or flagged. The lawyer can open the page image next to the answer. And when the evidence is weak, the system says it couldn't find it.

*Evaluate.* A lawyer-labelled test set with Arabic and English slices. Measure citation precision and recall, answer correctness and abstention. Tracing stays local.

*Break it.* Bad scans. Arabic and English versions of one contract that disagree. Amendments that replace clauses, so versions must be linked. GPU contention.

*Roll out.* One practice group first, with read-only Q&A and citations. Cross-contract analytics come later.

### S2. Support assistant for a payments app: 100K chats a day in Egyptian Arabic, FAQs plus account status, handoff to humans.
*Clarify.* Which channels? Which languages: Egyptian Arabic, Arabizi, English? What may the bot do: read-only status, or actions like refunds? How do users log in? What are the data rules? What does handoff look like today, and what does a human contact cost?

*Success.* Contacts resolved without a human, but also false containment: users the bot "resolved" who come back with the same problem. Plus the wrong-answer rate on an audited sample, satisfaction, first token under 2 seconds, cost per chat, and zero account data leaks.

*Design.*
- The app passes the logged-in user's session. A language detector handles Egyptian Arabic, Arabizi and English.
- A router sorts each message. FAQs and policies go to RAG. Account questions go to authenticated tools. Risky cases go to a human: fraud, disputes, legal threats, angry customers, or anyone asking for a person.
- RAG covers help articles and policies in Arabic and English, with dialect rewriting, hybrid retrieval and reranking. Common FAQ answers are cached, and replies stream.
- Account tools are read-only internal APIs. The user ID comes from the session, never from the model, so the model can't look up someone else's account.
- Handoff gives the agent a summary and the retrieved context, so the customer doesn't repeat themselves.

*The trap.* Account facts must come from the API, never from retrieved text. A help article about failed payments isn't this user's payment.

*Pressure: "Why did my payment fail?"* The bot calls the transactions API for the user's recent payments. If it's unclear which one, it asks. It gets the decline reason, then uses RAG to explain what that reason means and what to do. Facts come from the API, explanations from the documents.

*Pressure: a pasted prompt injection.* User text is untrusted. The defence is mostly design. Tools are read-only and scoped to that user, so even a successful injection only reaches the user's own data. Any action that changes something needs deterministic checks or a human. Output rules strip links and block other people's data. I'd log and flag injection attempts, and keep a red-team set in the eval.

*Evaluate.* Golden sets per intent, with Egyptian dialect and Arabizi slices, plus router accuracy. Then an A/B test on resolved contacts, false containment and satisfaction.

*Break it.* The account API goes down, so the bot says it can't check right now and hands off. Outdated fee information. Peaks like salary days and Ramadan. Fraudsters using social engineering.

*Roll out.* FAQ answers first, on a small share of traffic. Then read-only account status. A human is always one tap away.

### S3. Multi-tenant RAG product: 500 companies, strict isolation, per-tenant costs.
*Clarify.* How big are the tenants, and how uneven? Do any regulated clients need dedicated infrastructure or their own keys? Are there permissions inside each tenant too? Which costs get billed: tokens, storage, ingestion?

*Design.*
- Isolation by tier. Small tenants share an index, with a mandatory tenant filter enforced in one data-access layer. Large or regulated tenants get dedicated collections, and optionally their own encryption keys.
- Everything is scoped to the tenant: index entries, storage prefixes, cache keys, traces and logs. Cache keys start with the tenant ID.
- Ingestion is asynchronous, with a queue per tenant and fair scheduling. One tenant's bulk upload can't block everyone else.
- Metering per tenant: input and output tokens, embedding tokens at ingestion, reranker calls and storage. That feeds billing, with quotas, budgets and alerts.
- Document permissions inside each tenant still apply.

*The traps.* Noisy neighbours, handled with per-tenant rate limits and queues. And shared caches: a cache key without the tenant ID is a cross-tenant leak.

*Evaluate.* Automated leak tests with canary documents per tenant, which other tenants must never retrieve. Per-tenant latency and cost dashboards. Quality checks for tenants who provide test sets.

*Pressure: "One tenant holds 80% of the data."* They get their own collection or shard, sized and tuned for them, with their own ingestion queue. That also protects the small tenants' filtered search, and I can scale and bill the big one separately.

*Pressure: "A client asks you to delete everything."* Delete by tenant, everywhere: vectors, keyword index, raw files, caches, traces and logs, plus any tenant-specific models. For backups, I'd use crypto-shredding: delete the tenant's encryption key, so backup copies become unreadable. Then I verify it. The count of the tenant's items is zero, canary queries return nothing, and the client gets a deletion report.

*Roll out.* Start with the shared tier and a few pilot tenants. Add the dedicated tier when the first big or regulated client arrives.

### S4. You inherit an assistant at 62% correct. Leadership wants 85% in six weeks, with no rebuild.
The trap is promising 85% before the failure audit. So I'd say: "I'll give you a forecast at the end of week one, based on a failure audit."

First, is 62% solid? On 100 queries, the margin is about plus or minus 9.5 points. On 400, it's about 4.8.

*Pressure: "How do you define correct?"* With the stakeholders, in a written rubric. Correct means accurate, complete enough to act on, and supported by an approved source with a citation. We also agree how to score partial answers and abstentions. Saying "I don't know" when the documents truly don't cover it should count as correct. Two people label a sample, and I check that they agree.

*Pressure: "What do you do in week one?"* I pull about 400 real production queries, spread across intents and languages, and label them with the rubric. Each failure is assigned to one stage. The content doesn't exist, parsing broke it, chunking split it, retrieval missed it, ranking buried it, generation ignored it, or the question was ambiguous or out of scope. That gives a ranked list of failure buckets, and that's my forecast.

*Weeks two to five.* Fix the biggest bucket first. Typical wins without a rebuild:
- Missing content goes to the content owners.
- Parsing fixes, often for tables.
- BM25 plus RRF, if it's dense-only.
- A reranker, if there isn't one.
- Rewriting follow-up questions using the chat history.
- Fewer, better chunks, and prompt fixes for abstention and citations.

Each fix passes the golden set with a paired bootstrap interval, then shadow mode, then an A/B test or canary.

*Week six.* Report each gain with its interval, and the remaining buckets with honest estimates. If 15% of failures are questions the documents don't answer, that's a content gap, not a model problem. The fix is new content, or a clean "I don't know" with a handoff.
