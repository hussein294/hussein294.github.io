---
title: "RAG interview handbook, part 5: frontier topics and judgment"
description: "Fourteen questions on GraphRAG, agents, long context, text-to-SQL, page-image retrieval, Arabic, fine-tuning, MCP and agent evaluation."
date: 2026-11-11
track: rag-interview-handbook
series_order: 5
tags: [rag, interviews, graphrag, agents, arabic]
draft: false
---
Part 5 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

### E1. When is GraphRAG worth it, and when is it a mistake?
GraphRAG builds a knowledge graph from the corpus: entities and the relations between them. Microsoft's version also writes summaries for clusters of related entities.

It's worth it in two cases.
- Multi-hop or relationship questions, where the answer is spread across documents and the links matter. For example, "Which suppliers of our top customers had compliance issues?"
- Global questions about the whole corpus, like "What are the main themes in these complaints?" No single chunk holds that answer.

It also needs entities that can be extracted cleanly and matched, so one company doesn't become three nodes.

It's a mistake when most questions are local, a fact that sits in one passage. Then the graph adds expensive LLM extraction, a pipeline to keep fresh, and new kinds of error, for no gain.

Recent evidence says simpler enrichment gets most of the benefit. An AWS and Cisco study on 109 medical queries found that text retrieval plus one-hop relations from a curated knowledge graph scored a Hit@1 of 0.697. Knowledge graph plus text scored 0.642 to 0.661. On 109 queries, the intervals overlap, so the simple version matched the graph stack. It didn't clearly beat it. The graph alone scored only 0.138.

So my default is a strong hybrid baseline first. I add a graph only for the question types where the golden set shows a gap.

*If they ask, "How do you keep a graph fresh?":* incrementally. When a document changes, I re-extract entities and relations from the changed chunks only. Each edge keeps a link to its source chunk, so I can delete edges whose source is gone. New nodes go through entity matching again. The cluster summaries are the expensive part, so I'd regenerate them on a schedule, or only for clusters that changed. That cost is exactly what LazyGraphRAG avoids.

### E2. What does LazyGraphRAG defer, and what does that buy?
Full GraphRAG spends most of its money upfront. At indexing, an LLM reads every chunk to extract entities and relations. Then it writes a summary for every community, meaning every cluster of related entities.

LazyGraphRAG defers all LLM use to query time. At indexing, it uses cheap language processing instead. It extracts noun phrases as concepts, links concepts that appear together, and uses graph statistics to find the communities. No LLM is involved, so indexing costs about the same as vector RAG.

At query time, it ranks chunks and communities by similarity to the query. Then an LLM runs quick relevance tests on them, under a budget, for example 100 tests. It digs deeper into the communities where it finds relevant content. Finally, it extracts the relevant claims and writes the answer.

What that buys: Microsoft reports indexing at 0.1% of full GraphRAG's cost. On global questions, they report quality comparable to GraphRAG's global search at over 700 times lower query cost. And the budget is a single dial that trades cost for quality.

The caveat: that's Microsoft's own test, on 100 synthetic queries. So I'd treat it as a strong option to test, not a settled result.

*If they ask, "When would you still pay for summaries?":* when the same global questions come up again and again over a fairly stable corpus. Then you pay for the summaries once, and every query is cheap. Also when the summaries are useful in themselves, like a topic map analysts can browse. Or when query latency matters more than indexing cost.

### E3. When would you let an agent drive retrieval?
A fixed pipeline retrieves once and answers. An agent decides for itself what to search, whether the results are good enough, whether to search again, and which tool to use.

I'd let an agent drive in three cases.
- The number of steps isn't known upfront. In multi-hop questions, the second search depends on what the first one found.
- It has to combine sources. For example, search the policy documents, then query the orders API, then compare.
- Research-style questions, where it has to explore.

I'd keep a fixed pipeline for FAQ-like traffic, which is usually most of the volume. It's faster, cheaper, more predictable and easier to evaluate. A router can send only the hard queries to the agent.

When I do use an agent, I add guardrails:
- Budgets: a maximum number of steps, tokens and seconds, with a graceful answer when one runs out.
- Tracing of every step: the query, the tool call, the result and the decision.
- Context management. Search results fill the context fast, so I summarise or drop old tool outputs. Context overflow is a classic agent failure.
- Least privilege on tools, since retrieved text can try to hijack the agent.

*If they ask, "How do you evaluate an agent?":* on two levels. The outcome: was the final answer correct and grounded? And the path: the right tools with the right arguments, and how many steps, tokens and seconds it took. I replay a fixed set of scenarios several times, because agent runs vary.

### E4. "RAG is dead, coding agents just use grep." Respond.
There's a real point in it. Coding agents like Claude Code mostly search with grep and file reads, not embeddings, and it works well. Code is full of exact identifiers, and the agent can iterate: grep, read, refine, grep again.

There's research behind it too. A 2026 paper, "Is Grep All You Need?", tested agents on 116 questions from LongMemEval, where the answer is buried in long conversation histories. When tool results came back inline in the context, grep scored 83.6 to 93.1%, against 62.9 to 83.6% for vector search.

But the details matter. When results were written to files for the agent to read, vectors won 5 of 10 pairings. And the harness alone moved one model, with the same inline grep, from 93.1% to 76.7%. That's about 16 points. So the agent setup mattered as much as the retrieval method.

So "RAG is dead" confuses retrieval with one specific pipeline. Retrieval is still there. The agent just calls it as a tool. And enterprises need things grep doesn't give you:
- Permissions per document and per user.
- Paraphrase and cross-language matching. An Egyptian Arabic question and an English policy share no keywords.
- Scale. Grepping millions of documents at every step is slow and costly.
- Predictable latency and cost at high volume.

Retrieval stays. What changes is how it's called: as tools an agent chooses between, including exact search, BM25 and vector search.

*If they ask, "Would you drop the vector database?":* not by default. I'd measure. If queries are mostly exact lookups in a small corpus, BM25 or grep may be enough, and that's a simpler system. If there's paraphrase, more than one language, or a big corpus, the vector index earns its place. It's an empirical question for our golden set.

### E5. Why not paste the whole corpus into a long-context model?
For a small corpus, sometimes you should. For one contract or a 50-page manual, long context is simpler and avoids retrieval errors altogether. At scale, it breaks for five reasons.

1. Cost. You pay for every input token on every query. A million tokens at $3 per million is $3 a query, against about 1.5 cents for the RAG query costed in D2, in part 4. Prompt caching cuts that, but nowhere near RAG levels.
2. Latency. Time to the first token grows with input length.
3. Position. Models use information at the start and end of a long context better than the middle. That's the "Lost in the Middle" finding. More context can mean worse answers.
4. Permissions. Users see different documents, so each would need a different context.
5. Size and freshness. Enterprise corpora are far bigger than any context window, and they change daily.

Long context is great for small, single-document tasks. It also combines well with RAG: retrieve the right documents, then give the model whole documents instead of tiny chunks.

*If they ask, "Where is the crossover?":* when the corpus fits comfortably in the context, query volume is low, and every user can see everything. Then I'd compute both: tokens per query times price times volume, against the cost of building and running retrieval. And I'd test quality on our own questions, because some models lose accuracy well before their advertised context limit.

### E6. How do you route between RAG and text-to-SQL?
I route by intent, because each answers a different kind of question.

Structured questions go to SQL or an API: exact facts, counts, sums, balances and statuses. "How many orders failed last week?" "What's my balance?" RAG is bad at these. It retrieves text about orders. It can't count them.

Unstructured questions go to RAG: policies, procedures and explanations. "How do I...?" "What does the contract say about...?"

Some need both. "Why did my payment fail?" needs the transaction status from the API, say "declined, insufficient funds". Then it needs the policy text from RAG to explain what that means and what to do.

The router can be a small classifier, or an LLM returning structured output: the intent plus any extracted parameters. Simple rules catch the obvious cases first, like an order-number pattern.

For text-to-SQL, safety is critical:
- A read-only database user.
- Parametrised queries, or better, predefined query templates the model fills in, rather than free-form SQL.
- Row-level security, so a user can only reach their own rows. The database enforces it, not the prompt.

*If they ask, "How do you evaluate the router?":* as a classifier. I label a few hundred real queries with the right route, then measure accuracy and the confusion matrix. The errors aren't equal. Sending an account question to RAG can produce a confident wrong number, so that error counts more. Then I evaluate end to end, because a routing mistake shows up as a wrong answer.

### E7. When would you retrieve page images instead of text?
When turning the page into text loses the meaning. Forms, where the layout says which value belongs to which field. Charts and diagrams. Complex tables, slides and infographics. And poor scans, where OCR is unreliable.

The leading approach is ColPali. It embeds the page image directly with a vision-language model. It produces one vector per image patch, and matches query tokens against the patches with late interaction, like ColBERT. There's no OCR or layout parsing at indexing.

The trade-offs:
- Storage grows a lot, because each page has many vectors instead of one per chunk.
- To answer, you need a vision-language model to read the retrieved pages. That's slower and costlier than text generation.
- Citations point to a page, not a sentence.

So for clean digital text, text retrieval stays cheaper and better. I'd use page images for the visually rich subset, or route by document type. I could also run both indexes and fuse the results.

*If they ask, "How does this fit Arabic scans?":* it's attractive, because OCR on poor Arabic scans makes many errors. Connected script, diacritics, and mixed right-to-left and left-to-right text all cause trouble. Page images avoid OCR errors at the retrieval step. But these vision models were mostly trained on English documents, so I'd test them on our own Arabic pages. I'd compare OCR plus text retrieval against page-image retrieval, on recall and on final answers. My Linnaea work fits here. I benchmarked open vision-language models on real documents against the commercial API, so I know to test on your own pages and not trust the model card.

### E8. What would you refuse to build in your first 90 days?
I'd put it this way: I'd defer anything whose value I can't measure yet.
- GraphRAG, until I see relationship or global questions failing.
- Agentic retrieval, until there are multi-step questions a fixed pipeline can't handle.
- Fine-tuned embeddings, until I have real query pairs and the retriever is the measured bottleneck.
- Semantic answer caching, because of the wrong-entity and permission risks.
- Exotic chunkers. Recent studies show simple baselines, like structure-aware chunks with title prefixes, are hard to beat.

Each adds cost and new ways to fail. Complexity has to be earned by a measured gap.

The first 90 days go to the foundations. A golden set from real queries, a failure audit of the current system, and a strong baseline of hybrid retrieval plus a reranker. Plus tracing, and an evaluation gate before every release. Then the data tells us which advanced technique to try.

*If they ask, "What do you build first?":* the golden set and tracing, in the first two weeks. Without them, I can't tell whether anything I build helps. In week one, I'd read a few hundred real queries and failures with the team. Then I'd fix things in order of the biggest failure buckets.

### E9. What is the retrieval-generation gap? How do you close it?
It's when retrieval did its job but the answer didn't use it. The right evidence is in the prompt, and the model still misses it.

The AWS and Cisco study shows it clearly. On questions with several correct answers, retrieval brought in 83.5% of the needed evidence. But the answers only recalled 45 to 48%.

Causes:
1. Position. Models use the start of the context best. In the same study, the entities the model used sat on average 10.5% of the way into the context. The ones it missed sat at 36.8%. That fits "Lost in the Middle".
2. Prior knowledge. Models favour well-known entities and their own beliefs over unfamiliar evidence.
3. Phrasing. "Which drug treats X?" implies one answer, so the model stops after one, even when the context lists five.
4. Noise. Duplicates and half-relevant chunks dilute the signal.

Fixes:
- Fewer, deduplicated chunks, with the best ones first.
- For list questions, extract then answer. First the model extracts every relevant item from each chunk. Then it writes the answer from that list.
- Prompts that say the answer may have several items.
- Per-claim citations, so I can check what was used.

*If they ask, "How do you measure it?":* I measure retrieval and generation separately, on the same queries. Context recall says whether the evidence reached the prompt. Answer recall says whether it reached the answer. The difference between the two, per query type, is the gap. Put simply: when the gold evidence was retrieved, how often was the answer correct and complete?

### E10. Which Arabic normalisation do you apply, and when do you skip it?
For the keyword index, BM25, I normalise, because Arabic has many ways to write the same word.

1. NFKC Unicode normalisation, especially for text from PDFs. PDFs often store special letter-shape codes, called presentation forms, instead of normal letters.
2. Remove the diacritics, the tashkeel, and the tatweel, the stretching character. Most text has no diacritics, so queries and documents must match without them.
3. Unify the alef forms: أ, إ and آ become ا.
4. Map alef maqsura ى to ya ي, and often ta marbuta ة to ha ه. People type these inconsistently, especially in Egypt.
5. Unify digits. Arabic-Indic ٠ to ٩ become 0 to 9, so prices and IDs match.
6. Stem lightly. Strip common prefixes like ال, و and ب, and suffixes like ات and ون. A full root stemmer merges too many words.

Normalisation creates collisions. على, the word "on", and علي, the name Ali, become the same token. So do كتابة, "writing", and كتابه, "his book". That's acceptable for recall, because the reranker reads the original text and sorts it out.

Where I skip it:
- Dense embeddings get the original text, because multilingual models were trained on raw text.
- Display and citations always use the original, because you must quote the source exactly.
- In Quranic or classical text, diacritics carry meaning. I'd index two fields: a normalised one for recall and an exact one for precise matching.

*If they ask, "What does over-normalising break?":* precision. More words collide, so BM25 returns more irrelevant matches. Aggressive root stemming is the worst, because words from one root with different meanings merge. It also breaks exact search for names and quotes. So I'd measure each step on the golden set, turning it on and off.

### E11. A user asks in Egyptian Arabic, and the documents are in MSA and English. Walk through each stage.
1. Detect the language and script. The query might be Arabic script, or Arabizi, which is Arabic in Latin letters and digits, like "3ayez a3raf el refund". It's often mixed with English words.
2. Rewrite the query. A small LLM turns the dialect into MSA and adds English keywords. "عايز أرجع فلوسي" becomes something like "استرداد المبلغ" in MSA, plus "refund" in English. That bridges the vocabulary gap for BM25. Arabizi gets converted to Arabic script first.
3. Retrieve. I run BM25 per language with the right analyzer: Arabic normalisation for the MSA query, English stemming for the English keywords. I run dense search with a multilingual embedder like BGE-M3, which matches across languages. Then I fuse everything with RRF.
4. Rerank with a multilingual cross-encoder, like bge-reranker-v2-m3, against the original query. That way the dialect meaning isn't lost in the rewrite.
5. Answer in the user's register. If they wrote in Egyptian Arabic, I answer in clear, simple Arabic that suits them. Citations point to the source in its original language.
6. Evaluate a dialect slice separately in the golden set, with real Egyptian queries, not machine-translated ones. Scores on MSA hide dialect failures.

*If they ask, "How do you cite an English source in an Arabic answer?":* the citation points to the exact English passage, so it can be checked. In the answer, I paraphrase it in Arabic and name the source, like "according to the refund policy, section 3". I can show the original English quote on tap or in a footnote. I never present a translation as if it were a direct quote.

### E12. When is fine-tuning an embedding model or reranker worth it?
When three things hold:
- The vocabulary is specialised enough that general models struggle: internal product names, legal or medical terms, or Egyptian dialect.
- I have real training data: queries paired with relevant passages, plus hard negatives. Hard negatives are passages that look relevant but aren't.
- The failure audit shows ranking is the bottleneck, not parsing or chunking.

I'd fine-tune the reranker first. It needs no re-embedding of the corpus, training is cheaper, and it often gives the bigger lift, because it reads the query and passage together. Fine-tuning the embedder means re-indexing everything, and running old and new indexes side by side during the switch.

I measure the lift against a strong baseline: the best off-the-shelf models with hybrid retrieval, not a weak one. I check that general queries didn't get worse. That's the catastrophic-forgetting risk I handled when adapting speech models to niche domains at RDI. And I budget for upkeep: retraining when the domain shifts, and re-indexing when the embedder changes.

*If they ask, "Where do the labels come from?":* from production first. Queries with cited or clicked passages, answers that got a thumbs up, and escalations an agent resolved with a specific document. Then experts labelling a sample. Synthetic data helps to start: an LLM writes questions for passages, but I filter and spot-check them. Hard negatives come from the current retriever's top results that experts marked wrong.

### E13. How does MCP change retrieval, and what risks does it add?
MCP, the Model Context Protocol, is an open standard for connecting models to tools and data. A server exposes tools, like search_policies or get_order, each with a name, a description and an input schema. Any MCP client can use them.

For retrieval, search becomes a tool rather than a fixed pipeline step. The agent decides when to search, with what query and in which source. One retrieval service can serve many agents and apps. And the focus shifts to context engineering: what each tool returns, how much and in what format, because all of it lands in the context window.

New risks:
- Tool poisoning. A malicious server hides instructions in a tool description, which the model reads and may follow. A server can also change its descriptions after you approved it.
- Over-broad permissions. A tool running on a service account that sees everything breaks per-user permissions.
- Untrusted tool output. Search results are retrieved content, so they carry the same indirect injection risk as EchoLeak.

Controls:
- Only approved, reviewed servers, with pinned versions.
- Tools scoped per user, with the user's identity passed through so permissions apply.
- Tool output treated as data, never as instructions.
- Every tool call logged, with its arguments and results.

*If they ask, "Would you expose vector search as an MCP tool?":* yes, but as a narrow, well-designed tool, not raw vector access. Something like search_knowledge_base, with a query and filters. Behind it runs the full hybrid pipeline with reranking. It applies the user's permissions inside and returns a few chunks with source IDs for citations. That keeps the quality and security logic in one place.

### E14. How do you evaluate an agentic RAG system?
On two levels: the outcome and the path.

The outcome: did the agent reach the goal? Answer correctness, faithfulness to the evidence and citation quality. These are the same metrics as plain RAG.

The path: did it get there sensibly?
- Tool-call accuracy: the right tool with the right arguments.
- Steps, compared with a reasonable reference path.
- Tokens, latency and cost per task.
- Failure patterns: loops that repeat the same search, giving up too early, and context overflow, where tool outputs push the instructions out of the window.

The method: a fixed set of scenarios with expected outcomes, and reference tool sequences where useful. Tools that change things get mocks or a sandbox, so runs are repeatable. A calibrated LLM judge scores the trajectories, and full traces help me debug failures.

Agent runs vary, so I replay each scenario several times. I report a success rate, like 8 out of 10, not a single pass or fail.

*If they ask, "How do you handle non-determinism?":* repeated runs, reported as pass rates with intervals. Low temperature where possible, but I don't rely on it. Pinned model versions, and paired comparisons on the same scenarios. For a release gate, critical scenarios must pass on every run, not once. tau-bench calls this pass^k: the chance that all k runs succeed.

## Sources

- [Is GraphRAG Needed?](https://arxiv.org/abs/2606.25656), AWS and Cisco, Jun 2026
- [LazyGraphRAG](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/), Microsoft Research
- [Is Grep All You Need?](https://arxiv.org/abs/2605.15184), May 2026
- [Lost in the Middle](https://arxiv.org/abs/2307.03172)
- [ColPali](https://arxiv.org/abs/2407.01449)
- [BGE-M3](https://huggingface.co/BAAI/bge-m3)
