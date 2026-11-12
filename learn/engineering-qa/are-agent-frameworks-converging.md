---
title: "Are agent frameworks converging? (November 2026)"
description: "The protocols have converged and the frameworks haven't. What the early data and forecasts suggest."
date: 2026-11-11
track: engineering-qa
tags: [agents, frameworks, industry]
draft: false
---
Short answer: not at the framework level. The convergence so far is one layer below the frameworks, in the protocols, and one layer above, in the overall architecture. The frameworks themselves are splitting, mostly along vendor lines, and most teams still don't use one at all.

## What has converged: the protocols
- MCP (agent to tool) and A2A (agent to agent) now both sit in the Agentic AI Foundation under the Linux Foundation. MCP was donated in December 2025, and A2A joined in August 2026.
- The founding top-tier members include AWS, Anthropic, Google, Microsoft and OpenAI, so the main competitors all back the same two standards. That's the strongest convergence signal there is.

## What hasn't converged: the frameworks
- **Most teams use none.** Datadog's 2026 report found only about 18% of organisations in its data used an agent framework by early 2026, up from about 9% a year earlier. It checks for roughly 35 of them. My reading is that most teams still build directly on the model providers' SDKs.
- **Vendors are building their own.** Each major model or cloud vendor now ships an agent SDK: OpenAI's Agents SDK, Google's ADK, Anthropic's Claude Agent SDK, AWS's Strands and Microsoft's Agent Framework. Consolidation happens inside a vendor, as when Microsoft merged AutoGen and Semantic Kernel, not across vendors.
- **Momentum is shifting.** Temporal surveyed 554 US and UK engineers in mid-2026:
  - OpenAI's products were the most commonly selected.
  - Microsoft's framework, AWS Strands and CrewAI gained ground.
  - Interest in LangGraph declined.
  - The top blocker was tracking state, at 35.7%.
  
  Temporal sells workflow infrastructure, so treat that survey as useful but not neutral.

## What seems to be converging: the architecture
This part is my reading of the evidence, not a survey result. The pattern that keeps winning looks like this:
- one orchestrating agent running in a loop with tools
- subagents for isolated side tasks
- files or a store for memory

It's the shape behind coding agents. And coding agents are where people actually use agents today: in Stack Overflow's 2026 survey, 66% of developers who use AI work with coding agents. Recent research points the same way. Google's scaling study, MAST and Cognition's post all favour central coordination over free-form crews of role-playing agents.

## Forecasts
- **Gartner, June 2025:** over 40% of agentic AI projects will be cancelled by the end of 2027, because of "escalating costs and unclear business value". Gartner also warned about "agent washing": it estimated only about 130 of thousands of "agentic" vendors are genuine. By 2028, it expects 33% of enterprise software to include agentic AI, and at least 15% of day-to-day work decisions to be made autonomously.
- **My forecast from the evidence:**
  1. The protocols are settled enough to bet on.
  2. Teams will increasingly pick a framework by their cloud and model vendor.
  3. The hard problems are moving below the framework: state, durable execution, identity, cost and observability. That favours the clouds' managed agent platforms and workflow engines.
  4. Multi-agent setups will stay narrow, used mainly where the work splits into parallel parts.

*In an interview:* "There's no winner at the framework layer yet. The convergence is in the protocols, MCP and A2A, now both under the Linux Foundation. So I keep the framework thin and replaceable: tools behind MCP, remote agents behind A2A. I choose the framework by how much control we need and which cloud we're on."

## Sources
- [Datadog: State of AI Engineering 2026](https://www.datadoghq.com/state-of-ai-engineering/)
- [Temporal: State of Development 2026](https://temporal.io/reports/state-of-development-2026)
- [Stack Overflow: 2026 Developer Survey results](https://stackoverflow.blog/2026/10/06/the-results-of-the-2026-developer-survey-are-here/)
- [Gartner forecast, reported by Reuters via The Star](https://www.thestar.com.my/tech/tech-news/2025/06/25/over-40-of-agentic-ai-projects-will-be-scrapped-by-2027-gartner-says), Jun 2025
- [A2A joins the Agentic AI Foundation](https://aaif.io/blog/a2a-joins-aaif)
- [Donating the Model Context Protocol and establishing the Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation), Anthropic, Dec 2025
