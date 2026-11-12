---
title: "Multi-agent systems: a one-hour crash course"
description: "When several agents help and when they hurt, the eight architectures, context and protocols, reliability, security and evaluation, with interview-ready answers."
date: 2026-11-11
track: crash-courses
series_order: 1
tags: [agents, multi-agent, a2a, mcp, interviews]
draft: false
---

Read each module, then say the interview answers out loud. The timings are a guide.

## Module 1 (0:00 to 0:07): the vocabulary

**Agent.** An LLM in a loop. It looks at the situation, picks a tool, reads the result, and repeats until it decides it's done. Anthropic's definition: the model directs its own process and tool use.

**Workflow.** LLM calls wired together by your code, on a fixed path. It's predictable and cheap. Many production "agents" are really workflows, and that's fine.

**Multi-agent system.** Several agents, each with its own prompt, tools and context window, working on one task. Usually an orchestrator hands parts of the work to specialist workers.

There are four real reasons to split one agent into several:
1. Parallelism. Independent subtasks run at the same time, so the job finishes sooner.
2. Context isolation. Each worker explores in its own context window and returns a short summary, so the main agent's context stays clean.
3. Specialisation. Each role gets its own prompt, tools or model, like a cheap model for extraction and a strong one for planning.
4. Separate permissions. A worker that reads email doesn't need the payments tool.

And three real costs:
1. Tokens. Anthropic measured agents at about 4 times the tokens of a chat, and multi-agent systems at about 15 times.
2. Coordination errors. Agents misread each other, repeat work or make conflicting choices.
3. Debugging. A failure can start in one agent and show up in another.

*If they ask, "What is a multi-agent system?":* "Several LLM agents, each with its own instructions, tools and context, working on one task. Usually an orchestrator splits the work and specialist agents do the parts. There are three good reasons for it: parallel work, keeping each context small and focused, and giving each agent only the tools it needs. But it costs many more tokens and adds coordination failures. So I start with one agent and split only when I can measure a gain."

## Module 2 (0:07 to 0:15): when it helps, with evidence

This is the most important module. Interviewers want judgment, not enthusiasm.

**For: Anthropic's research system (June 2025).** A lead agent running Claude Opus 4 planned the research and sent parallel subagents running Claude Sonnet 4 to search. It outperformed a single Opus 4 agent by 90.2% on Anthropic's internal research eval. On the BrowseComp benchmark, three factors explained 95% of the performance differences. Token usage alone explained 80%. The other two were the number of tool calls and the choice of model. So much of the gain comes from spending more tokens, in parallel. The caveat: it's a vendor's internal eval.

They were also clear about where it fits badly: tasks where every agent needs the same context, or where agents depend heavily on each other. They said most coding tasks are like that.

**Against: Cognition, the makers of Devin (June 2025).** Their post is called "Don't Build Multi-Agents". It has two principles:
1. Share context, and share full agent traces, not just individual messages.
2. Actions carry implicit decisions, and conflicting decisions carry bad results.

Their example: split "build a Flappy Bird clone" between two subagents. One builds a background in Super Mario style. The other builds a bird that doesn't match it. The final agent can't reconcile the two. Their default is one agent working in a single thread. For long tasks, they add a separate model that compresses the history.

**The data: Google Research (December 2025 paper, January 2026 blog).** They tested 180 configurations: one single-agent setup and four multi-agent designs, called independent, centralized, decentralized and hybrid. They used four benchmarks and models from OpenAI, Google and Anthropic.
- On work that splits into parallel parts, financial analysis, centralized coordination improved results by about 81%.
- On sequential planning, every multi-agent design made things worse, by 39 to 70%.
- Errors spread. Independent agents amplified errors 17.2 times. A central coordinator kept that to 4.4 times.
- Once a single agent already scored above about 45%, adding agents gave little or negative return.
- Tasks needing many tools suffered, because each agent gets a smaller share of the token budget.
- A model built on task properties picked the best design for 87% of held-out configurations. So the choice is predictable, not a matter of taste.

**My decision rule.** Use several agents when the task splits into parts that are independent, can run in parallel, and need more context than one window holds. Research across many sources is the classic case. Keep one agent, or a fixed workflow, when steps depend on each other, share a lot of context, or need many tools in one tight loop. And always compare against a single agent with the same token budget, because extra tokens alone explain much of the gain.

*If they ask, "When would you not use multiple agents?":* "When the steps depend on each other. Google's scaling study found that every multi-agent design made sequential planning worse, by 39 to 70%. Cognition's point is that parallel agents make hidden decisions that conflict, like two subagents building parts of a game in different styles. So for tightly coupled work, like most coding, I keep one agent. I use subagents only for side questions that come back as a short answer."

*If they ask, "But Anthropic got a 90% gain from multi-agent?":* "For research that splits into independent searches, yes. But token usage alone explained 80% of the variance on BrowseComp. So before crediting the architecture, I'd compare against a single agent given the same budget."

## Module 3 (0:15 to 0:27): the eight architectures

For each one, know how it works, when to use it and how it fails.

**1. Orchestrator and workers, also called a supervisor.** A lead agent breaks the task down, sends parts to workers and combines the results. The workers don't talk to each other.
- Use it for research and for analysis across many sources: anything that splits cleanly.
- It fails when task briefs are vague, so work gets duplicated or missed. The orchestrator can become a bottleneck, and one slow worker holds up the round.
- This is the "centralized" design in Google's study, the one that contained errors best, at 4.4 times.

**2. Hierarchical.** Supervisors of supervisors: a top planner, then team leads, then workers.
- Use it for very large tasks with natural sub-teams.
- It fails because every layer loses detail and adds latency and cost. It's rarely needed.

**3. Sequential pipeline.** Agent A's output becomes agent B's input: plan, then write, then review.
- Use it for fixed stages, like extract, validate, then summarise. Each stage is easy to test alone.
- It fails because an early error flows through every later stage. Often this is really a workflow, and that's fine.

**4. Parallel fan-out, then merge.** Several agents work at once. Either each takes a different section, or all do the same task and vote. Anthropic calls these sectioning and voting.
- Use it for independent sub-questions, or for voting to raise confidence.
- It fails at the merge. Conflicting partial answers need a clear rule for resolving them.

**5. Router and handoff.** A triage agent passes the conversation to one specialist, which takes over. The OpenAI Agents SDK calls this a handoff. Swarm-style systems are built from handoffs.
- Use it for customer support, with billing, technical and account specialists.
- It fails through wrong routing, or ping-pong, where agents pass the user back and forth. Context can also get lost at each handoff.

**6. Evaluator and optimizer, or generator and critic.** One agent produces work. Another checks it against criteria and sends feedback, in a loop.
- Use it when the criteria are clear, like tests that must pass or a groundedness check.
- It fails through endless loops, or a critic that approves everything. Cap the rounds.

**7. Debate and voting.** Several agents answer and critique each other until they converge, or a judge picks the best answer.
- Use it for hard reasoning, where varied attempts help.
- It fails because it's costly, and agents can talk each other into the same wrong answer. Several studies found debate often doesn't beat simple majority voting at the same compute.

**8. Shared state, or blackboard.** Agents don't message each other directly. They read and write a shared store, like a task board, a state object or files. LangGraph's shared state graph works this way.
- Use it for long-running work, where agents pick up tasks as they appear.
- It fails through conflicting writes and stale reads. Each field needs a clear owner.

Google's study also tested two looser designs. Independent means agents work in parallel with no coordination, and a final step merges their answers. That one amplified errors the most, 17.2 times. Decentralized means peers talk to each other directly, with no boss.

**My default:** an orchestrator with a few workers, structured outputs, and one place where results are merged. Anything more complex needs a measured reason.

*If they ask, "Supervisor or swarm?":* "Supervisor by default. A central coordinator checks and merges the work, which contains errors. In Google's study, independent agents amplified errors 17.2 times, against 4.4 for a centralized design. Handoffs fit conversations that move between specialists, like support, where only one agent is active at a time."

*If they ask, "How do you pick a pattern?":* "From the task's shape. Independent parts that can run in parallel point to orchestrator and workers. Fixed stages point to a pipeline. Clear pass-or-fail criteria point to a generator and critic. Conversations that move between specialists point to handoffs. And if the steps are tightly coupled, one agent."

## Module 4 (0:27 to 0:37): context, communication, protocols and frameworks

**Context engineering is the real job.** Each agent sees only its own context window. So the design question is: what does each agent see, and what does it send back?

*The brief going down.* Anthropic found that each subagent needs four things: an objective, an output format, guidance on tools and sources, and clear task boundaries. Without them, subagents duplicated each other's work. One early version spawned 50 subagents for a simple query. So they now scale effort to complexity:
- a simple fact: one agent with 3 to 10 tool calls
- a comparison: 2 to 4 subagents
- complex research: more than 10 subagents

*The summary coming back.* Workers return a condensed summary, not their whole trace. Anthropic's context-engineering guidance says a subagent may use tens of thousands of tokens exploring, but returns only about 1,000 to 2,000. That's where the context-isolation benefit comes from.

*References, not content.* Big outputs go into a shared store, like files or a database, and agents pass IDs or paths. This keeps contexts small and avoids the "telephone game", where information degrades each time it passes through an agent.

*Structured messages.* Agents talk in JSON that follows a schema, not free text, so the receiver can validate it. Include the task ID, status, result, sources and confidence.

**Memory comes in three kinds.**
- Working memory: the current context window.
- Session state: the plan, progress and intermediate results, saved outside the model. Anthropic's lead agent saves its plan to memory, so the plan survives if the context grows too long.
- Long-term memory: facts kept across sessions, usually in a database or vector store. That's retrieval again, with RAG's usual problems: freshness, permissions and poisoning.

**Protocols: MCP and A2A.**
- MCP connects an agent to tools and data. It's agent to tool.
- A2A, short for Agent2Agent, connects agents to other agents, even ones built by other teams on other frameworks. It's agent to agent.

Both now sit in the Agentic AI Foundation, under the Linux Foundation. Anthropic donated MCP in December 2025. Google launched A2A in April 2025 and gave it to the Linux Foundation, and it joined this foundation in August 2026. A2A 1.0, the first stable version, shipped in March 2026.

A2A in five points:
1. **Discovery.** Each agent publishes an Agent Card, a JSON file at /.well-known/agent-card.json. It lists the agent's skills, its endpoint, capabilities like streaming, and the authentication it accepts. Version 1.0 added signed cards, so a caller can verify the agent's identity.
2. **Tasks.** Work is a task with a lifecycle. It starts as submitted, then working. It can pause at input-required or auth-required. It ends as completed, failed, canceled or rejected.
3. **Messages and artifacts.** A message has a role, user or agent, and parts: text, files or structured data. The outputs a task produces are called artifacts.
4. **Transport.** JSON-RPC 2.0, gRPC, or plain HTTP with JSON. Long tasks can stream updates, or send push notifications to a webhook.
5. **Security.** Standard schemes, declared in the card: API keys, OAuth 2.0, OpenID Connect or mutual TLS.

The key difference: with MCP, the caller sees exactly what goes into a tool and what comes out. With A2A, the remote agent is opaque. You send it a task and get results back, without seeing its prompts, tools or memory. That suits agents owned by different teams or companies.

*If they ask, "MCP or A2A?":* "Both, at different layers. MCP is how an agent uses tools and data. A2A is how agents built by different teams find each other and delegate work, with Agent Cards for discovery and a task lifecycle for long jobs. My AutoScript Engine project uses A2A between its agents. Inside one codebase, plain function calls between agents are simpler. A2A pays off across team or vendor boundaries."

**Frameworks, one line each.** Name a shortlist with reasons, never a single winner.
- **LangGraph:** agents as a graph with shared state, checkpoints and human approval steps. It gives the most control.
- **CrewAI:** role-based crews, where each agent has a role, a goal and a backstory. It's fast to prototype with.
- **Microsoft Agent Framework:** the merger of AutoGen and Semantic Kernel. It reached 1.0 in April 2026 and supports MCP and A2A, in Python and .NET.
- **OpenAI Agents SDK:** agents, handoffs, guardrails and tracing. It's minimal.
- **Google ADK:** sequential, parallel and loop workflow agents, plus delegation driven by the LLM, with A2A support.
- **Claude Agent SDK:** the agent harness behind Claude Code, including subagents.

*If they ask, "Which framework would you use?":* "It depends on how much control we need. For production with checkpoints and human approval, LangGraph or Microsoft Agent Framework. For a quick prototype, CrewAI. Often plain code with good tracing is enough. Frameworks can hide the prompts, and the prompts are where most bugs live. Anthropic makes the same point in its agent-building guide."

## Module 5 (0:37 to 0:47): reliability, cost and security

**Why multi-agent systems fail.** The MAST study, from UC Berkeley and published at NeurIPS 2025, annotated 1,642 execution traces from seven open-source multi-agent frameworks, including MetaGPT, ChatDev and AG2. It found 14 failure modes in three groups:
1. **System design issues, 44.2%.** Agents disobey the task or their role, repeat steps, lose the conversation history, or don't know when to stop.
2. **Inter-agent misalignment, 32.3%.** Agents reset the conversation, fail to ask for clarification, drift off the task, withhold information, ignore another agent's input, or reason one way and act another.
3. **Task verification, 23.5%.** Agents stop too early, skip or rush verification, or verify wrongly.

The fixes they tried helped but didn't solve it. Clearer roles, with the CEO agent getting the final say, raised ChatDev's task success by 9.4%. Adding a high-level verification step raised it by 15.6%. Their conclusion: better base models alone won't fix this. It's a system design problem, like organising a team.

**Errors compound.** If each step succeeds 95% of the time, ten steps in a row succeed only 60% of the time, and twenty steps only 36%. So keep chains short, verify between steps, and make failures recoverable.

**Reliability controls.**
- Budgets on everything: turns per agent, total tokens, wall-clock time and money. When a budget runs out, return the best partial answer and say so.
- Explicit stop conditions. "Unaware of termination conditions" is a named MAST failure. Define "done" in every brief, and check it.
- Loop detection. Stop an agent that repeats the same tool call with the same arguments.
- Checkpoints, so a long run resumes from where it failed instead of restarting. Anthropic does this, with retries.
- Timeouts per worker, so one slow worker can't hold up the round.
- Idempotent tools, so a retry doesn't send the email twice.
- Human approval before anything irreversible: payments, deletions, sending messages.
- Gradual deploys. Anthropic uses rainbow deployments, shifting traffic slowly from old to new versions so agents mid-task aren't cut off.

**Cost controls.**
- A strong model for the orchestrator and cheaper models for workers. Anthropic's system did this, with Opus 4 leading Sonnet 4 workers.
- Effort scaled to the query. A simple question gets one agent, not a team.
- Tool results cached and shared across workers.
- Cost tracked per task and per agent, in the traces.

**Observability.** One trace per user request, with a child span for each agent and each tool call. Log each agent's brief, output, tokens and latency. OpenTelemetry now has conventions for tracing generative AI calls like these. Without traces, multi-agent bugs are nearly impossible to find.

**Security.** OWASP published a Top 10 for Agentic Applications in December 2025. These five matter most for multi-agent systems:
- **ASI01, agent goal hijack:** injected text changes what an agent is trying to do.
- **ASI03, identity and privilege abuse:** agents act with more access than the user has.
- **ASI06, memory and context poisoning:** bad data planted in shared memory.
- **ASI07, insecure inter-agent communication:** forged or tampered messages between agents.
- **ASI08, cascading failures:** one agent's error spreading through the rest.

The core risk is that an injection in one agent's input can travel to the others. A 2024 paper called Prompt Infection showed an injection that copies itself from agent to agent.

The controls:
- Treat other agents' outputs as untrusted data, just like retrieved documents.
- Least privilege per agent. The research agent can read, but it can't move money.
- Pass the user's identity down the chain, so every agent acts with the user's permissions, never through a shared admin account.
- Authenticate agents to each other. A2A 1.0 supports signed Agent Cards and standard authentication.
- Validate every message against its schema, and keep an audit log of every handoff.

*If they ask, "How do you stop agents looping forever?":* "Hard budgets on turns, tokens and time. A clear definition of done in each brief. And loop detection when an agent repeats the same call. When a budget runs out, the system returns its best partial answer and says what's missing, instead of failing silently."

*If they ask, "What's the biggest security risk?":* "Injection spreading between agents. One agent reads a poisoned document, and its output carries the attack to an agent with more power. So I treat every agent's output as untrusted, give each agent only the tools it needs, and make every agent act with the user's own permissions."

## Module 6 (0:47 to 0:55): evaluation, and multi-agent RAG

**Evaluate at three levels.**
1. **The outcome.** Is the final answer correct, complete and grounded? These are the same metrics as RAG.
2. **The trajectory.** Did the right agents use the right tools, in a sensible number of steps, without loops? Tag each failure with its MAST group, so you know whether it's a spec problem, a coordination problem or a verification problem. The MAST authors built an LLM judge for this that agreed with human experts at a kappa of 0.77.
3. **Each agent alone.** Unit-test each worker on its own sub-task, with fixed inputs. Most bugs are easier to find there.

**Anthropic's evaluation lessons.**
- Start small. About 20 real queries is enough early on, because early changes have big effects.
- A single LLM judge call with a rubric worked best. It covered factual accuracy, citation accuracy, completeness, source quality and tool efficiency, scored from 0.0 to 1.0, plus a pass or fail.
- Keep humans involved. Testers noticed early agents choosing SEO content farms over authoritative sources, which the automated eval missed.

**Three rules worth stating in an interview.**
1. Always compare against a single agent with the same token budget. Otherwise you can't tell whether the architecture helped, or just the extra tokens.
2. Run each scenario several times. Report pass rates, plus pass^k for reliability: the chance that all k runs succeed.
3. Ablate. Remove one agent and re-run. If quality doesn't drop, that agent is cost without value.

And track cost, latency and tokens per task and per agent.

**Multi-agent RAG: when and how.** Most RAG doesn't need multiple agents. A good pipeline, or one agent with a search tool, handles FAQ-style questions faster and cheaper. Multiple agents earn their place in three situations:
- **Deep research across many sources.** An orchestrator plans sub-questions, and parallel workers each search one source or sub-question and return short, cited summaries.
- **Mixed sources.** A policy-documents agent, a SQL agent and a tickets agent, each with its own tools and permissions, under one coordinator.
- **Verification.** A separate checker tests each claim against its cited source before the answer goes out.

A design to draw on the whiteboard:
1. **Router.** Simple questions go to the normal RAG pipeline. Complex ones go to the orchestrator.
2. **Orchestrator.** It writes the plan to session state and creates 2 to 5 sub-questions. Each gets an objective, sources, an output schema and a budget.
3. **Workers, in parallel.** Each runs hybrid retrieval plus reranking on its source. It returns claims with citations, in about 1,000 to 2,000 tokens.
4. **Verifier.** It checks each claim against its cited chunk, and drops or flags unsupported ones.
5. **Synthesizer.** It writes the final answer with citations, or says it couldn't find the answer.

Permission filters apply inside every worker's retrieval, and the whole run is traced as one tree.

*If they ask, "Would you use multiple agents in our RAG system?":* "Only where it measurably helps. For most questions, a strong pipeline with hybrid retrieval and a reranker is faster, cheaper and easier to evaluate. I'd route only complex, multi-part questions to an orchestrator with parallel workers. And I'd prove the gain against a single agent with the same budget before rolling it out."

*If they ask, "How is agentic RAG different from multi-agent RAG?":* "Agentic RAG means one agent decides when and what to retrieve, and can search again. Multi-agent RAG splits that work across several agents, usually parallel workers under an orchestrator. Agentic is the smaller step, and I'd try it first."

## Module 7 (0:55 to 1:00): rapid-fire drill

Answer each one out loud in under 30 seconds.

1. *"Agent or workflow?"* A workflow follows a path written in code. An agent chooses its own next step. Use workflows where the path is known, and agents where it isn't.
2. *"Why use subagents at all?"* Parallel work, separate clean contexts that return short summaries, and narrower tools and permissions for each role.
3. *"What's the biggest risk?"* Coordination failures. In MAST, system design issues and misalignment between agents caused over three quarters of all failures.
4. *"How do agents share information?"* A short, structured brief going down, a condensed, structured summary coming back, and large outputs kept in a shared store and passed by reference.
5. *"How do you control cost?"* A strong orchestrator with cheaper workers, effort scaled to the query, caching, budgets, and cost tracked per agent.
6. *"How do you secure it?"* Treat messages between agents as untrusted, give each agent least privilege, pass the user's identity down the chain, authenticate agents, and log every handoff.
7. *"How do you evaluate it?"* Outcome, trajectory and per-agent tests, repeated runs, and a comparison with a single agent at the same budget.
8. *"What's an A2A Agent Card?"* A JSON file at /.well-known/agent-card.json. It tells other agents what this agent can do, where to reach it, and how to authenticate.
9. *"When do more agents make things worse?"* On sequential tasks, like planning in Google's study, which dropped 39 to 70%. And when a single agent already scores above about 45%.
10. *"How do you debug a multi-agent failure?"* Open the trace tree and find the first agent whose output was wrong. Then check its brief. Was the objective, format or boundary unclear? Most failures start as specification problems.

## Sources

All checked on 10 Nov 2026.

- [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system), Anthropic, Jun 2025
- [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents), Cognition, Jun 2025
- [Towards a science of scaling agent systems](https://research.google/blog/towards-a-science-of-scaling-agent-systems-when-and-why-agent-systems-work/), Google Research blog, Jan 2026, and [the paper](https://arxiv.org/html/2512.08296v2)
- [Why Do Multi-Agent LLM Systems Fail?](https://arxiv.org/pdf/2503.13657), the MAST study, NeurIPS 2025
- [A2A specification](https://a2a-protocol.org/latest/specification/) and [A2A joins the Agentic AI Foundation](https://aaif.io/blog/a2a-joins-aaif), Aug 2026
- [Donating the Model Context Protocol and establishing the Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation), Anthropic, Dec 2025
- [OWASP Top 10 for Agentic Applications](https://genai.owasp.org/2025/12/09/owasp-top-10-for-agentic-applications-the-benchmark-for-agent), Dec 2025
- [Microsoft Agent Framework 1.0](https://devblogs.microsoft.com/agent-framework/?p=5212), Microsoft, Apr 2026
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), Anthropic, for the 1,000 to 2,000 token subagent summaries
