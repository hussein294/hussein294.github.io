---
title: "RAG interview handbook, part 3: evaluation and statistics"
description: "Fourteen questions on retrieval metrics, RAG metrics, golden sets, sample sizes, LLM judges, A/B tests and paired testing."
date: 2026-11-11
track: rag-interview-handbook
series_order: 3
tags: [rag, interviews, evaluation, statistics]
draft: false
---
Part 3 of the RAG interview handbook. Each question has a full answer, written to be said out loud, followed in italics by the follow-up an interviewer is likely to ask next. Facts and figures were checked in November 2026.

### C1. Define recall@k, MRR and nDCG@k. When does each mislead?
- **Recall@k** is the share of all relevant items that appear in the top k. It ignores the order within the top k. It misleads when k is bigger than what the model actually reads: recall at 20 means little if only 5 chunks reach the prompt. It also counts unlabelled relevant documents as misses, so incomplete labels make retrieval look worse than it is.
- **MRR**, mean reciprocal rank, averages 1 / rank of the first relevant result. It sees only that first hit. So it's weak for questions whose answer spans several documents, like list or comparison questions.
- **nDCG@k**, normalised discounted cumulative gain, uses graded relevance, discounts lower positions on a log scale, and compares against the ideal ranking. It's the most complete, but only as good as its relevance judgments, which are expensive and often inconsistent. It's also hard to explain to non-specialists.

*If they ask, "Which do you report to leadership?":* none of them directly. Leadership gets answer accuracy and the business outcome, like questions resolved without escalation, with an interval. Retrieval metrics are for the team. If leadership wants one retrieval number, it's recall at the k we actually pass to the model.

### C2. Recall@10 is 0.95, but users complain. What could be happening?
Retrieval can be fine while the product isn't. The candidates:
1. The retrieval-generation gap. The right chunk reaches the prompt and the model ignores it, because of its position, too many chunks, or a conflicting chunk next to it.
2. The metric doesn't match the prompt. Recall at 10 is high, but maybe only the top 5 reach the model.
3. The golden set isn't representative. Engineers wrote it in clean MSA or English, while users write in dialect, with typos and follow-ups.
4. Bad gold labels that mark the wrong passages as relevant.
5. Unanswerable questions. Users ask about things the corpus doesn't cover, and the system makes something up.
6. Stale documents. Retrieval found the old version.
7. The answer itself: too long, in the wrong language or register, or too slow.

The way to find out is to read real failing conversations and tag each failure by the stage where it went wrong.

*If they ask, "What do you change first?":* nothing, until I've read 50 to 100 failing traces and tagged them. Then I fix the biggest bucket. Very often the first fix is refreshing the golden set with real production queries, because the 0.95 was measured on the wrong questions.

### C3. Define faithfulness, response relevancy, context precision and context recall.
These are the standard Ragas metrics.
- **Faithfulness:** the share of claims in the answer that the retrieved context supports. An LLM splits the answer into claims and checks each one against the context. It needs no reference answer.
- **Response relevancy:** does the answer address the question? An LLM generates questions from the answer, and those are compared with the original question by embedding similarity. It ignores whether the answer is correct.
- **Context precision:** are the relevant chunks ranked near the top of the retrieved context? It's usually judged against a reference answer.
- **Context recall:** the share of claims in the reference answer that the retrieved context supports. In other words, did retrieval bring everything needed? It always needs a reference answer.

*If they ask, "Which can you run without labels?":* faithfulness and response relevancy. They need only the question, the context and the answer, so they work on samples of live traffic. Context recall can't, because it needs a reference.

### C4. How can an answer score 100% faithfulness and still be wrong?
Because faithfulness measures support by the context, not truth. If the context is wrong, a perfectly faithful answer is wrong too.
- The context is stale: the answer faithfully quotes last year's fee.
- Retrieval fetched the wrong document: a similar product, or another country's policy.
- The answer is supported but off the question: true statements that don't answer what was asked.
- The answer is supported but incomplete: it leaves out the exception that applies to this user.

So I never report faithfulness alone. I pair it with answer correctness against a reference, with relevancy, and with checks on document freshness and version.

*If they ask, "Which metric catches this?":* answer correctness against a reference answer, which needs labels. Context precision and recall show that retrieval brought the wrong documents. Version checks catch staleness. In production, user feedback and escalations catch what the metrics miss.

### C5. How do you build a golden set from nothing? What must it contain?
1. Seed it from reality: search logs, support tickets, chat transcripts and questions from subject-matter experts. Synthetic questions only fill gaps, and they get reviewed.
2. Stratify it by intent, by language (MSA, Egyptian dialect, English and mixed), by difficulty and by document type, so each slice can be reported.
3. Include the hard cases on purpose: unanswerable questions to test abstention, ambiguous ones to test clarification, adversarial ones like prompt injection, multi-hop questions, permission cases where the user must not see the answer, and questions about documents with several versions.
4. For each item, store the question, a reference answer, the gold source passages, its slice labels and the user's role.
5. Label carefully: a written rubric, two annotators on at least a sample, measured agreement like Cohen's kappa, and a process for resolving disagreements.
6. Keep dev and test apart. Tune on dev, report on test, and never tune on test.
7. Grow it from production. Every confirmed failure becomes a new item, and the set is versioned so scores stay comparable.

*If they ask, "Who labels it, and how long does it take?":* domain experts, like support leads or lawyers, write the reference answers. Engineers can label retrieval, with expert review. A useful first version of a few hundred items takes roughly one to two weeks, with a couple of experts part-time. Then it grows with every production failure.

### C6. How many queries do you need to measure 90% precision within ±3 points?
I use the sample-size formula for a proportion: n = z² × p × (1 − p) / e².

With z = 1.96 for 95% confidence, p = 0.9 and e = 0.03:
n = 1.96² × 0.9 × 0.1 / 0.03² = 3.8416 × 0.09 / 0.0009 = 384.16.

Round up to 385 queries. And that's per slice I plan to report, not for the whole set.

*If they ask, "What about Arabic and English separately?":* then it's 385 each, 770 in total, and more for a dialect slice. If that's too expensive, I report the wider margin honestly. With 100 queries per slice, the margin at 90% is about ±5.9 points.

### C7. System B beats A by 2 points on 200 queries. Is it real? How do you test that?
I can't tell without a paired test. Both systems ran on the same 200 queries, so I compare them query by query.

Two points on 200 queries is a net difference of just 4 queries. What matters is the discordant pairs: queries where one system was right and the other wrong. Even in the best case, where B wins 4 and loses none, the exact McNemar test gives p = 0.125. That's not significant. If B won 14 and lost 10, also a net 4, p would be around 0.54. So 2 points on 200 queries is very likely noise.

The tests I'd use:
- McNemar's test, for right-or-wrong outcomes.
- A paired bootstrap: resample the queries with replacement many times, computing the difference each time. If the 95% interval includes zero, the gain isn't established.
- A randomisation test, which randomly swaps the two systems' results per query.

And if I tried many configurations before finding this one, I correct for multiple comparisons, or confirm the winner on a fresh held-out set. Try 20 setups, and one will "win" by luck.

*If they ask, "Why paired?":* because query difficulty varies far more than the systems do. Pairing compares the systems on the same query, which removes that variation. The test becomes much more sensitive than comparing two separate accuracy numbers.

### C8. Why must an LLM judge be calibrated? How would you check one?
An LLM judge is a model with its own biases. It tends to prefer longer answers, answers in its own style, and whichever answer comes first in a side-by-side comparison. It can share blind spots with the model it's judging, especially one from the same family. And its scores shift when the judge model or prompt changes. If I gate releases on an unchecked judge, I'm optimising for the judge, not the user.

To check it, humans label a random sample with the same rubric, and I measure how often they agree with the judge, as accuracy or Cohen's kappa. I check each slice separately, because judges can be weaker in Arabic. I fix the rubric until agreement is good enough, and pin the judge model version. In side-by-side tests I swap the answer order, to cancel position bias. And I recheck agreement whenever the judge or its prompt changes.

*If they ask, "How big is that sample?":* big enough to estimate agreement within a few points. By the same formula as C6, that's a few hundred items, spread so each important slice has enough.

### C9. Design an A/B test for a RAG change: unit, primary metric, guardrails, duration.
**Unit:** randomise by user, or by session for anonymous users, not by query. A user who gets different systems on consecutive questions sees inconsistent behaviour, and their queries aren't independent.

**Primary metric:** a task outcome, like resolution without escalation to a human, thumbs-up rate, or fewer rephrased questions.

**Guardrails** that must not get worse: p95 latency, cost per query, abstention rate, and the rate of unsupported claims, judged offline on a sample.

**Size and duration:** with a 30% baseline and a 2-point minimum effect, I need about 8,400 users per arm. It runs at least one full business cycle, usually one to two weeks, fixed in advance, with no peeking and stopping early. Before the A/B test, the change passes the offline gate on the golden set, then shadow mode, then a small canary.

*If they ask, "What's your decision rule?":* it's set before launch. Ship if the primary metric's 95% interval is above zero and no guardrail degrades beyond its agreed tolerance. If the result is flat, keep whichever version is cheaper or simpler.

### C10. What is interleaving? Why does it fit RAG less well than search?
Interleaving merges two rankers' result lists into one list for the same user. One method, team-draft interleaving, alternates picks from each ranker. Whichever ranker supplied the results the user clicks gets the credit. Every user sees both systems at once, so it needs far less traffic than an A/B test to detect a ranking difference.

In RAG, the user doesn't see a ranked list. They see one generated answer built from the chunks, so there's nothing to interleave and few clicks to credit. Citation clicks are a weak and rare signal.

*If they ask, "What would you use instead?":* A/B tests on outcomes, plus offline side-by-side comparisons of answers by humans or a calibrated LLM judge.

### C11. How do you set an abstention threshold? What is a risk-coverage curve?
First I need a confidence signal for each query. That's a calibrated score built from the reranker's top score, its margin over the second result, and maybe a groundedness check.

Coverage is the share of queries the system answers. Risk is the error rate among the ones it answers. If I sort queries by confidence and lower the threshold step by step, coverage rises, and risk usually rises with it. Plotting risk against coverage gives the risk-coverage curve.

I pick the point on that curve using business costs: the cost of a wrong answer against the cost of a handoff, or of saying "I couldn't find that". I choose the threshold on a dev set and confirm it on a held-out test set, with a confidence bound. For example, a Clopper-Pearson lower bound on the precision of answers above the threshold. That turns "over 90% precision" into a claim I can defend.

*If they ask, "Does the threshold hold for Arabic?":* not automatically. Score distributions differ by language and query type, so I'd check the curve per slice and set separate thresholds if needed.

### C12. What do you monitor in production when you have no labels?
Three layers. First, user behaviour: people rephrasing the same question, escalations to a human, thumbs up and down, citation clicks, and abandoned sessions.

Second, system signals: the share of queries with no confident result, the abstention rate, and drift in retrieval scores. Also the language and intent mix, latency percentiles, cost per query, and citation coverage, meaning the share of answer sentences with a citation.

Third, quality sampling: a reference-free LLM judge scores a sample for faithfulness and relevancy, and humans review a small sample every week. Every confirmed failure goes into the golden set.

*If they ask, "What should page someone at night?":* hard failures. Error rates, latency beyond the target, a stalled ingestion pipeline, and any sign of a permission leak. Quality drift goes on a daytime dashboard.

### C13. What do SRM, CUPED, novelty effects and sequential testing mean?
1. **SRM, sample ratio mismatch:** the traffic split doesn't match the design, like 52/48 on a planned 50/50, at large numbers. A chi-squared test flags it. It means assignment or logging is broken, so the result can't be trusted.
2. **CUPED:** it uses each user's behaviour before the experiment to remove noise, so you need less traffic for the same sensitivity.
3. **Novelty effect:** users react to something just because it's new, and the reaction fades. Short tests overstate the gain, so run long enough and watch the effect over time.
4. **Sequential testing:** methods that let you check results repeatedly and stop early while keeping the false-positive rate valid. Naive peeking inflates that rate.

*If they ask, "Which do you check first?":* SRM. It's a quick check, and if it fails, nothing else in the analysis matters.

### C14. A per-query metric is randomised by user. How does that change sizing and analysis?
Queries from one user are correlated. So 10,000 queries from 2,000 users carry less information than 10,000 independent queries.

For sizing, multiply by the design effect: 1 + (m − 1) × ICC. Here m is queries per user, and ICC, the intra-class correlation, measures how alike one user's queries are. With 5 queries per user and an ICC of 0.1, that's 1.4, so 8,400 becomes 11,760 queries.

For analysis, either average the metric per user and compare users, or keep it per query and use the delta method or a cluster bootstrap that resamples users, not queries.

*If they ask, "What goes wrong if you treat queries as independent?":* the standard errors come out too small, so you declare wins that are really noise from a few heavy users.

## Sources

- [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
