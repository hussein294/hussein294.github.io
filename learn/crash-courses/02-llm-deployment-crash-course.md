---
title: "Deployment: a 30-minute crash course"
description: "Why small open models save money and self-hosting often does not, how LLM serving works, and the deployment practices interviewers ask about."
date: 2026-11-11
track: crash-courses
series_order: 2
tags: [deployment, llm-serving, mlops, open-models, interviews]
draft: false
---
Prices below are as listed in October and November 2026. They change monthly, so check current prices before relying on them.

Read each module, then say the interview answers out loud.

## Module 1 (0:00 to 0:10): do open models really save money?

**Short answer:** often by 10 times or more. But the saving comes from the smaller model, not from owning the GPU. Self-hosting is where the saving often dies.

**Three ways to run an open model.**
1. **Serverless, per token.** A provider runs the model on its GPUs, and you pay per million tokens, like any API. Examples are Together AI, Fireworks AI, DeepInfra, Groq and Cerebras. Groq and Cerebras run on their own chips and are very fast. The big clouds sell the same thing through Amazon Bedrock, Google Vertex AI and Azure AI Foundry. Routers like OpenRouter and Hugging Face Inference Providers put one API in front of many providers.
2. **Dedicated endpoints.** The provider runs a copy of the model just for you, and you pay per GPU-hour. You get steady latency, isolation and your own fine-tunes, without running servers. Examples are Hugging Face Inference Endpoints, Baseten, Modal, and dedicated deployments from Together or Fireworks.
3. **Self-hosting.** You rent or buy GPUs and run the serving stack yourself, usually vLLM or SGLang on Kubernetes. It gives the most control and takes the most work.

**Why self-hosting kills the saving.** A GPU costs the same per hour whether it's busy or idle. Serverless providers pool thousands of customers, so their GPUs stay busy and their cost per token stays low. Your own GPU sits idle at night, at weekends and between requests. Three costs pile up:
- **Utilisation.** A GPU that's busy 20% of the time costs five times as much per token as one that's always busy.
- **Redundancy.** One GPU is a single point of failure. Production needs at least two, plus enough for peak traffic.
- **People.** Someone patches drivers, upgrades the engine, tunes batching and gets paged at 3 a.m.

**A worked example.** Take an 8-billion-parameter model on one rented H100. In October 2026, specialist GPU clouds listed H100s at about $2 to $4.50 an hour, and the big clouds at about $7 to $12. Say $2.50 an hour, or about $1,825 a month.

Assume the GPU produces about 2,500 output tokens a second when fully loaded. That's a planning figure. One published test measured about 3,600 tokens a second for this model size at batch 64. At full load, that's 9 million tokens an hour, or about $0.28 per million tokens. At 20% utilisation, it's about $1.40 per million.

Now compare per-token prices. In November 2026, Together AI listed 8B-class Llama models at about $0.15 to $0.20 per million tokens. The much bigger gpt-oss-120b was listed at $0.15 per million input tokens and $0.60 per million output tokens.

Take a typical RAG workload: 100,000 queries a day, with 3,500 tokens in and 300 out. That's about 11.4 billion tokens a month.
- A frontier API at an example $3 in and $15 out: about $45,000 a month.
- An 8B model on a serverless provider, at $0.18 per million: about $2,050 a month.
- gpt-oss-120b on a serverless provider: about $2,100 a month.
- Self-hosting the 8B model on two H100s for redundancy: about $3,650 a month for the GPUs alone, plus engineering time. That assumes one GPU can carry the peak, which needs a load test.

So switching to a smaller model saved about 95%. Self-hosting it would then cost more than the serverless option. At $0.18 per million, two GPUs only break even at about 20 billion tokens a month, and only with steady traffic.

**Where self-hosting does win.**
- Steady, high volume that keeps the GPUs busy, like large batch jobs running around the clock.
- Data that can't leave your network or country. Banking and payments often have rules like this, and then price isn't the question.
- Air-gapped sites, like a legal team's offline contract archive.
- Custom models: your own fine-tunes, or many LoRA adapters on one base model.
- Very tight latency, where the model has to sit next to your other services.

**The middle path:** start serverless. Move busy, steady workloads to a dedicated endpoint. Self-host only when the numbers or the rules demand it.

**Two things make switching low-risk.**
- Most providers, and vLLM itself, offer an OpenAI-compatible API. Moving from a closed model to an open one, or from a provider to your own server, is mostly a new base URL and model name. A gateway in front, like LiteLLM or your own thin layer, handles routing, fallbacks and cost tracking.
- Your golden set decides whether the small model is good enough. Run it sliced by language and task. Gaps between small and large models are often wider outside English, so test Arabic separately.

**Cost levers beyond hosting.**
- Routing, or cascades: a small model handles the easy queries, and only hard ones go to the big model.
- Fine-tuning a small model for a narrow task, like classification, extraction or routing. There, it can match a large general model.
- Batch APIs for work that can wait. OpenAI, Anthropic and Google discount batch jobs by about 50%.
- Prompt caching, fewer and shorter chunks, and shorter answers.
- Check the licence. Apache 2.0 models, like gpt-oss and most Qwen models, are the simplest. Llama has its own community licence with conditions.

*If they ask, "Can we save money with open models?":* "Usually a lot, if a smaller model is good enough for the task, and the golden set decides that. In a rough estimate for 100,000 RAG queries a day, moving from a frontier API to a small open model on a serverless provider cut the bill from about $45,000 a month to about $2,000. But self-hosting that model on two GPUs would cost more than the provider, before counting anyone's time. GPUs cost the same idle or busy, and providers keep theirs busy by pooling customers. So I'd self-host only for steady high volume, data that can't leave our network, or custom models."

*If they ask, "When would you self-host?":* "When the numbers or the rules demand it. The numbers: steady traffic that keeps GPUs busy enough to beat the provider's price per token. The rules: data residency, an air-gapped site or strict isolation. In between, a dedicated endpoint from a provider gives isolation without running the stack ourselves."

## Module 2 (0:10 to 0:18): how LLM serving works

**Memory comes first.** The weights take parameters × bytes per parameter.
- At 16 bits (BF16), that's 2 bytes each. An 8B model is 16 GB, and a 70B model is 140 GB.
- FP8 is 1 byte, so half that. 4-bit formats like AWQ and GPTQ take about a quarter, with some quality loss.
- So a 70B model in BF16 needs at least two 80 GB H100s. In FP8 it fits on one H100 but leaves little room for anything else, so an H200 with 141 GB is more comfortable.

Then there's the KV cache: the attention keys and values kept for every token of every active request. For Llama 3.1 8B in BF16, that's about 128 KB per token. 32 users with 8,000-token contexts need about 32 GB. Many users with long contexts eat memory faster than the weights do.

Mixture-of-experts models change the maths. gpt-oss-120b has 117 billion parameters but uses only about 5 billion per token, so it's fast. But all the weights must still sit in memory. OpenAI ships it in 4-bit so it fits on one 80 GB GPU.

**Two phases, two bottlenecks.**
- **Prefill** reads the whole prompt in parallel. It's limited by compute, and it sets the time to first token.
- **Decode** generates one token at a time per request. It's limited by memory bandwidth, because every step reads all the weights.

That's why batching matters so much. One read of the weights serves every request in the batch, so throughput rises sharply. The cost is that each user waits a little longer for each token.

**The metrics.**
- **TTFT, time to first token:** queueing plus prefill. It's what chat users feel.
- **ITL or TPOT, the time between output tokens:** the decode speed.
- **Throughput:** tokens per second across all users. It's what the bill depends on.
- Always report p95 and p99 at a stated concurrency, never just averages.

**What serving engines do for you.**
- **Continuous batching:** requests join and leave the batch at every step, instead of waiting for the whole batch to finish.
- **PagedAttention**, from vLLM: the KV cache is stored in small pages, like virtual memory, so little is wasted and batches can be bigger.
- **Prefix caching:** the KV cache for a shared prompt start, like the system prompt, is reused across requests.
- **Quantization:** FP8 on H100-class GPUs usually costs very little quality. 4-bit saves more memory, but test it.
- **Speculative decoding:** a small draft model guesses several tokens, and the big model checks them in one step. It speeds up decode when the guesses are often right.
- **Tensor parallelism:** each layer is split across GPUs, for models too big for one.
- Newer stacks, like NVIDIA Dynamo and llm-d, run prefill and decode on separate GPU pools.

**The engines.**
- **vLLM and SGLang:** the open-source defaults, both with an OpenAI-compatible API. Hugging Face has put its own engine, TGI, into maintenance mode and recommends these two.
- **TensorRT-LLM:** NVIDIA's engine. It's often the fastest on NVIDIA GPUs, but takes more setup.
- **llama.cpp and Ollama:** for laptops and single machines, not for serving many users at once.

*If they ask, "How much GPU memory does a 70B model need?":* "140 GB for the weights in BF16, so at least two 80 GB GPUs with tensor parallelism. In FP8 it's 70 GB, which fits on one H100 but leaves little room for the KV cache. That cache grows with users times context length. For a 70B Llama, it's about 320 KB per token. So I'd size from the expected concurrency and context, then load-test."

*If they ask, "How do you trade latency against throughput?":* "Batch size is the dial. Bigger batches raise throughput and cut the cost per token, but each user waits longer. I'd set a target, like a p95 time to first token under one second, then raise concurrency until we reach it."

## Module 3 (0:18 to 0:25): deployment in general

**Four serving patterns.**
- **Online:** a REST or gRPC service that answers each request in real time.
- **Batch:** a scheduled job that scores many records at once. It's cheaper, because the hardware stays busy.
- **Streaming:** a consumer reads events from a queue like Kafka and scores each one as it arrives.
- **Edge:** the model runs on the device, for privacy, offline use or zero network delay.

The document-extraction platform I architected at Linnaea combined real-time and batch paths.

**Packaging.**
- A container image with pinned dependencies, the same from laptop to production. Environment parity removes a whole class of "works on my machine" bugs. I standardised exactly this at RDI, with Docker and Kubernetes.
- Models live in a registry, like MLflow, with a version number, a reference to the training data and the evaluation results. The service loads a pinned version, never "latest".
- Save weights as safetensors, not pickle files. Loading a pickle can run arbitrary code.

**Release strategies, from safest to riskiest.**
- **Shadow:** the new model gets a copy of live traffic, but its answers aren't shown. You compare quietly.
- **Canary:** send 1 to 5% of traffic to the new version, watch the guardrails, then ramp up.
- **Blue-green:** run the old and new versions side by side and switch all traffic at once. Rollback means switching back.
- **A/B test:** a controlled experiment that measures business impact.
- **Feature flags** turn a model on for chosen user groups without a redeploy.

Always keep the previous version warm, and roll back automatically when an SLO or guardrail breaks.

**Scaling.**
- Scale GPU services on queue depth or concurrency, not CPU usage. CPU usage says little about a GPU-bound service.
- Cold starts are slow. Loading a 16 GB model can take a minute or more. Scale-to-zero saves money but makes the first request wait, so keep a warm minimum for anything interactive.
- Reserve GPU capacity for steady load, and use on-demand capacity for peaks.

**Reliability.**
- Timeouts on every call, retries with backoff, and a circuit breaker that stops hammering a failing dependency.
- Fallbacks: a smaller model, a cached answer, or "I can't answer right now" with a handoff.
- Rate limits per client, and idempotent requests, so a retry never duplicates work.
- In batch jobs and queues, a dead-letter queue catches the items that keep failing.

**Monitoring, in three layers.**
- **System:** p50, p95 and p99 latency, error rate, throughput, GPU utilisation and memory, queue depth.
- **Model:** input drift, the distribution of outputs, and sampled quality checks.
- **Business:** the outcome the model exists for, plus cost per request.

Define SLOs, like "99.5% of requests in under 2 seconds", and alert on the SLI that measures each one.

**Data drift versus concept drift.** Data drift means the inputs change: a new dialect, a new document type, a new product. You can see it without labels. Concept drift means the right answer for the same input changes, like after a policy update. You need labels or feedback to see it.

**A classic gotcha.** Running model inference directly inside an async handler, in FastAPI for example, blocks the event loop, so one slow request freezes all the others. The fix is to run inference in a worker pool or a separate service, so the event loop only handles I/O.

*If they ask, "How do you roll out a new model safely?":* "Offline evaluation first, on the golden set. Then shadow mode on live traffic. Then a canary at a few percent, with automatic rollback on latency, error and quality guardrails, and then a gradual ramp. The old version stays warm until the new one has run through a full business cycle."

*If they ask, "What's the difference between data drift and concept drift?":* "Data drift is a change in the inputs, like users switching to dialect. I can detect it without labels, by comparing input distributions. Concept drift is a change in what the right answer is, like a new refund policy. That needs labels, feedback or a refreshed golden set to catch."

## Module 4 (0:25 to 0:30): rapid-fire drill

Answer each one out loud in under 30 seconds.

1. *"Batch or real-time?"* Real-time when a user is waiting, batch for everything else. Batch is cheaper: the hardware stays full, and batch APIs cost about half.
2. *"Our service is slow under load. What do you check?"* Queue depth and GPU utilisation first. Then whether the KV cache is full, which makes requests wait or get preempted. Then prompt lengths, batch settings, cold starts, and anything blocking the event loop.
3. *"How do you avoid vendor lock-in?"* An OpenAI-compatible interface behind our own gateway, prompts and evals that run against any model, and at least one tested fallback provider.
4. *"Why is self-hosting GPUs so expensive?"* You pay per hour, not per token, so idle time is the real cost. Utilisation, redundancy and people decide the bill.
5. *"Many customers each want their own fine-tune. How do you serve that cheaply?"* One base model with many LoRA adapters, chosen per request. vLLM and several providers can serve many adapters on one base model.
6. *"What goes in a model registry?"* The weights, the version, a reference to the training data, the evaluation results, the licence and the container it runs in.
7. *"How do you know a cheaper model is good enough?"* Run the golden set, sliced by language and task, with a paired test against the current model. And agree the bar before the results come in.
8. *"What's TTFT?"* Time to first token: queueing plus prefill. Long prompts and full queues make it worse.

**The one line to remember:** smaller models save the money, serverless providers keep the saving, and self-hosting pays off only with steady volume, data rules or custom models.

## Sources

- [H100 rental prices compared across cloud providers](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison), IntuitionLabs, prices checked 10 Oct 2026
- [Together AI pricing](https://www.together.ai/pricing), checked through a third-party tracker on 10 Nov 2026
- [Llama 3.1 8B throughput on one H100](https://docs.valdi.ai/llms/performance/gpu/H100/llama3.1-inference-testing/), VALDI
- [Text Generation Inference README](https://github.com/huggingface/text-generation-inference), for the maintenance-mode notice
