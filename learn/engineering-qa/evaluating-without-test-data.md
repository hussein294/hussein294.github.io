---
title: "How to evaluate a model when you have no test data"
description: "End the no-data state fast, evaluate without reference answers in the meantime, and design the product so labels arrive by themselves."
date: 2026-11-11
track: engineering-qa
tags: [evaluation, llm-evaluation, mlops]
draft: false
---
Start by framing it right: having no test data is a temporary state. The first job is to end it, and meanwhile you use signals that don't need labels.

## End it quickly
- **Real inputs first:** logs, tickets, search queries and real documents. Fifty to a hundred examples labelled in a day already tell you a lot. Anthropic started its research-agent evaluations with about 20 real queries.
- **Synthetic questions to fill gaps:** an LLM writes questions from your documents, so each question comes with a known source passage. Review a sample of them. Synthetic questions are cleaner and easier than real ones.
- **Hand-written edge cases:** unanswerable, ambiguous and adversarial questions.

## Meanwhile, evaluate without reference answers
- **Reference-free metrics:** in RAG, faithfulness and answer relevancy need only the question, the context and the answer.
- **An LLM judge with a rubric,** checked against a small human-labelled sample.
- **Pairwise comparison:** picking the better of two outputs is easier and more consistent than scoring one alone.
- **Label only the disagreements:** run the current system and the candidate side by side, and label only the cases where they disagree. Those are exactly the pairs McNemar's test uses, so a small labelling budget goes a long way.
- **Invariance tests:** paraphrase the question, reorder the context, or add an irrelevant document. The answer shouldn't change.
- **Hard checks:** valid schema, totals that add up, citations that point to real passages.

## After launch, production supplies signals and labels
- **Implicit feedback:** rephrased questions, escalations, thumbs, abandoned sessions, and the business outcome itself. A/B tests run on these.
- **Human review queues:** low-confidence outputs go to people, and their corrections feed the test set. That's how my OCR work at RDI was set up: calibrated confidence sent uncertain cases to human review.
- **Active learning:** label the examples the model is least sure about first.

For classic unsupervised models, like clustering or anomaly detection, there are internal metrics such as the silhouette score, and stability checks across resamples. The real test is still whether the output helps the downstream task.

*In an interview:* "First I'd end the no-data state quickly: a few hundred real queries labelled by experts, plus reviewed synthetic questions. Until then, I'd use reference-free metrics with a calibrated judge, pairwise comparisons and invariance tests, and I'd spend labelling effort only where two systems disagree. Then I'd design the product so labels arrive by themselves, through human review of low-confidence cases, like my OCR work at RDI, and through user feedback."

## Sources

- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), Anthropic, for starting evaluations with about 20 real queries
- [Ragas metrics](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/)
