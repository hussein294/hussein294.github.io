---
title: "RAG interview handbook, part 1: foundations"
description: "Ten foundational RAG interview questions, from pipeline design and parsing to chunking and embeddings, each with a full answer and the likely follow-up."
date: 2026-11-11
track: rag-interview-handbook
series_order: 1
tags: [rag, interviews, chunking, embeddings]
draft: false
---
Part 1 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

### A1. Walk me through a production RAG system in 90 seconds.
A production RAG system has two halves.

The offline half builds the index. Connectors pull documents from each source, together with their permissions. A parser turns them into clean text: OCR for scans, with layout, tables and page numbers kept. Then I chunk the text along its structure, attach metadata like title, section, dates, version and access groups, and embed each chunk. Everything goes into two indexes: a vector index and a BM25 keyword index.

The online half answers questions.
1. Rewrite the question into a standalone query, using the chat history.
2. Retrieve with BM25 and vector search in parallel, both filtered by the user's permissions.
3. Fuse the two lists with reciprocal rank fusion.
4. Rerank the top candidates with a cross-encoder.
5. Decide whether to answer at all. If the evidence is weak, say so or hand off to a human.
6. Generate the answer from the top chunks, with a citation for each claim.
7. Validate before showing it: the citations point to real passages, and nothing leaks.

Around both halves sit tracing of every stage and an evaluation loop: a golden set, offline gates before each release, and online metrics after it.

*If they ask, "Which stage would you build last?":* the clever query tricks, like HyDE, decomposition and agentic loops. I'd build tracing, evaluation, parsing, hybrid retrieval, reranking and citations first. Then I'd add query tricks only where the golden set shows a gap they fix.

### A2. Why can RAG fail with an excellent LLM? Name the failure points in order.
Because the LLM only sees what the pipeline gives it. Barnett and colleagues listed seven failure points, in pipeline order:
1. Missing content. The answer isn't in the corpus, and the model makes one up instead of saying so.
2. Missed the top-ranked documents. The answer exists, but retrieval ranked it below the cut.
3. Not in context. It was retrieved, but dropped when the context was assembled, for example by a token limit.
4. Not extracted. It reached the prompt, but the model didn't use it, because noise or conflicting chunks distracted it.
5. Wrong format. The model ignored the requested format, like a table or a list.
6. Incorrect specificity. The answer is too general or too detailed for the question.
7. Incomplete. Part of the answer is missing, even though the context held all of it.

I'd add two upstream failures the list doesn't name. Parsing errors, like a table flattened into nonsense. And stale data, where the index still holds an old version.

*If they ask, "Which is hardest to detect?":* missing content. The system still produces a fluent, confident answer from the model's own knowledge. You only catch it if the golden set includes questions the corpus can't answer, and you measure whether the system abstains.

### A3. How would you parse a 300-page scanned Arabic contract with tables?
1. Route the pages first. Check each page for a real text layer. Digital pages give text directly. Scanned pages, or pages with a bad hidden OCR layer, go to OCR.
2. Run OCR with layout. Use an Arabic-capable OCR engine, or a vision-language model that returns layout. Reading order matters: right to left, columns, and headers and footers removed.
3. Keep tables as tables. Extract them as HTML or Markdown, with rows and columns intact. HTML handles merged cells better. A table flattened into prose is useless for a question like "What's the penalty in year 3?"
4. Keep provenance. Store the page number and bounding box of every block, so each citation can point to the exact spot and show the image.
5. Score each page. Low-confidence pages go to human review before indexing. That's the confidence calibration and routing I built for OCR at RDI.
6. Keep the raw output: page images and OCR results. When a better model arrives, I can reprocess without rescanning.

Then the text goes through Arabic normalisation for the BM25 index. The original text is kept for embeddings, display and citations.

*If they ask, "How do you know the OCR is good enough?":* I label a sample of pages, spread across scan quality and page types. I measure the character error rate on text and cell accuracy on tables. Then I measure what matters downstream: retrieval recall and answer accuracy on questions about those pages. "Good enough" is the error level below which answers stop getting worse.

### A4. What chunk size do you start with, and how do you choose the final one?
I start around 300 to 512 tokens, with little or no overlap, and always within the embedding model's input limit. I split along the document's structure, at headings, paragraphs or clauses, rather than cutting mid-sentence.

I also separate two things people often mix up. The retrieval unit is what gets embedded and matched. The context unit is what the LLM reads. They don't have to be the same: I can match on a small chunk and pass its whole section to the model.

Then I tune per document type, on a dev set. I try a few sizes, say 256, 512 and 1,024 tokens. I measure recall at the k I actually use, answer quality, and index size and cost. Contracts, FAQs and manuals often end up with different settings.

*If they ask, "Why not 100 tokens?":* too little context per chunk. Pronouns and references lose what they point to, like "the Party" or "this fee". The embedding captures a fragment, not an idea, and the number of chunks multiplies. Small units can work for matching, but only if I expand to the parent section before generation.

### A5. Does semantic chunking beat fixed windows? What does recent evidence say?
Rarely by enough to justify its cost.

Semantic chunking splits where the similarity between neighbouring sentences drops, so each chunk holds one topic. It sounds better, but the evidence is weak.
- A CIKM 2026 study, "When Is Complex Chunking Worth It?", found that contextual, semantic and late chunking rarely won significantly over simple baselines. Adding the title to each chunk was a cheap, strong option. That's two corpora with fixed settings, so it isn't the last word.
- An October 2026 Notre Dame study found that structure-aligned chunks with real headings beat contextualised fixed windows, and beat a placebo with shuffled headings. But the effects were small: +0.022 and +0.012 on a coverage-aware nDCG@10.
- On Arabic, one pipeline study found sentence-aware chunking beat semantic chunking, 74.78 to 66.92 on average across six datasets. It won three of the six outright, so it isn't universal either.

So my default is structure-aware chunks with a title or heading prefix. I'd test semantic chunking on our own corpus, and count its indexing cost, because it embeds every sentence.

*If they ask, "When would you still use it?":* for text with no structure at all, like call transcripts, chat logs or long OCR output without headings, where topic changes aren't marked. And only if it wins on our dev set.

### A6. What is contextual retrieval, what does it cost, and would you use it?
Contextual retrieval is Anthropic's technique for chunks that lose their meaning on their own. Before indexing, an LLM reads the whole document and writes a short context for each chunk, usually 50 to 100 tokens. That context is prepended to the chunk before both embedding and BM25 indexing.

Anthropic's example: a chunk says "The company's revenue grew by 3% over the previous quarter." Alone, you can't tell which company or which quarter. The added context names both.

Their results: top-20 retrieval failures fell from 5.7% to 2.9% with contextual embeddings plus contextual BM25, and to 1.9% with reranking added. The cost was about $1.02 per million document tokens, paid once at indexing. That figure assumes prompt caching, 800-token chunks and 8,000-token documents.

Would I use it? Maybe, but not first. It's a vendor's test, and independent results are weaker: the CIKM 2026 study found contextual chunking rarely won significantly. So I'd compare it against a simple title or heading prefix, which costs almost nothing.

*If they ask, "How would you run that comparison?":* same golden set, same chunks, three arms: plain chunks, a heading prefix, and contextual retrieval. I'd measure recall at 5, 10 and 20, and answer accuracy, with a paired bootstrap for the differences. I'd add indexing cost and time, and slice by document type and language. If the prefix gets most of the gain, I ship the prefix.

### A7. What is small-to-big retrieval, and why does it help?
You match on small units, then hand the model something bigger.

I index small pieces, like sentences or chunks of 100 to 200 tokens. A small piece has a focused embedding, so it matches precisely. But when one is retrieved, I pass its parent to the LLM: the whole section, or a window of text around the hit. The model needs that surrounding context, because definitions, conditions and exceptions usually sit next to the matching sentence, not inside it.

Two things to watch. First, deduplicate: several small hits often share one parent, and I shouldn't send that parent twice. Second, the token budget: parents are big, so I cap how many go into the prompt, ranking parents by their best child's score.

*If they ask, "What is your retrieval unit for contracts?":* the clause, or the sub-clause for long ones. The context unit is the full clause with its heading and article. And I'd link the definitions section, because contracts define terms like "Confidential Information" pages away from where they're used.

### A8. How do you choose an embedding model for mixed Arabic and English?
I shortlist on hard constraints first:
- Language: strong Arabic and English, plus matching across the two.
- Licence and hosting: can the data go to an API, or must it be self-hosted?
- Maximum input length, vector size, latency and cost.

A typical shortlist has open models like BGE-M3 and Qwen3-Embedding-8B, and hosted ones like Cohere Embed v4, voyage-4-large or Gemini Embedding 2.

Then I test on our own labelled queries, sliced by Arabic, English and mixed queries, and by dialect if users write in Egyptian Arabic. I measure recall at the k we actually use. Public results only seed the shortlist. In one 2025 Arabic RAG study, BGE-M3 narrowly led the embedders, with an average score of 70.99 across six datasets. "Narrowly" is the key word: on our data, the order could change.

*If they ask, "How do mixed-language queries behave?":* worse than you'd hope. A query that mixes Arabic and English, or uses Arabizi, can land between the two languages in embedding space. So I test it as its own slice. Fixes include transliterating Arabizi, rewriting the query into MSA plus English keywords, and fusing retrieval per language.

### A9. How do you change embedding models on a live index?
Vectors from two models live in different spaces. You can't mix them in one index or compare their scores, so the switch is a migration.
1. Build the new index in parallel, by re-embedding the whole corpus.
2. Dual-write. During the migration, new and changed documents go to both indexes.
3. Evaluate offline on the golden set, then in shadow mode on live traffic: run the new retrieval silently and compare.
4. Switch an alias, so all queries move at once.
5. Keep the old index for a while, so rollback is instant.

Then I recalibrate everything that was tuned on scores: abstention thresholds, similarity cutoffs and fusion weights. Score distributions shift with the model.

*If they ask, "What happens to your caches?":* the query-embedding and retrieval caches are keyed on the model and index version, so they simply miss after the switch. Answer caches built on the old retrieval get cleared, or expire.

### A10. What is query and passage asymmetry in embedding models?
Many embedding models are trained asymmetrically, because queries and passages look different: queries are short questions, and passages are long text. So the model expects to be told which is which.
- E5 models expect "query: " and "passage: " prefixes.
- Older BGE English models put an instruction before each query.
- APIs like Cohere and Voyage take an input type: query or document.
- BGE-M3 needs no prefix, which is exactly why you read each model card.

If you skip the prefix, nothing breaks. Recall just quietly drops. The same goes for the similarity metric: use the one the model was trained with, and check whether its vectors come normalised. With normalised vectors, cosine and dot product agree. Without normalisation, they can rank differently.

*If they ask, "How would you detect this bug?":* it never throws an error, so only evaluation catches it. I'd run the golden set with and without the prefixes, and compare against the scores the model card reports on a public benchmark. I'd also add a unit test that the query path and the document path each apply the right prefix.

## Sources

- [Seven Failure Points When Engineering a RAG System](https://arxiv.org/abs/2401.05856), Barnett and colleagues
- [Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval), Anthropic
- [When Is Complex Chunking Worth It?](https://arxiv.org/abs/2608.16586), CIKM 2026
- [Does Document Structure Help Dense Retrieval?](https://arxiv.org/abs/2610.10170), Oct 2026
- [Optimizing RAG Pipelines for Arabic](https://arxiv.org/abs/2506.06339)
- [BGE-M3](https://huggingface.co/BAAI/bge-m3)
