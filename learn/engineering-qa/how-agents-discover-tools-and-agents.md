---
title: "How agents discover MCP tools and A2A agents"
description: "Discovery is done by code and use is a tool call, with one exception at scale. Plus how sure we can be in an area this new."
date: 2026-11-11
track: engineering-qa
tags: [mcp, a2a, tool-calling, agents]
draft: false
---
If you have used tool calling, a natural question is whether exploring an MCP server, or finding A2A agents, also happens through tool calls. Mostly not: discovery is usually done by code, and only the use is a tool call. The model never speaks MCP or A2A; the only thing it can produce is a tool call. MCP and A2A are the plumbing behind that call, run by the host program.

## MCP, step by step
1. **Discovery is done by the host, not the model.** When the host connects, its MCP client calls `tools/list` on the server. That returns each tool's name, description and input schema. It's ordinary code, with no LLM involved.
2. **The host translates.** It converts those definitions into the model's own tool format, like the `tools` list you send to any chat API. To the model, an MCP tool looks exactly like a local function you defined by hand.
3. **Use is a normal tool call.** The model emits a tool call. The host sees which server owns that tool and sends `tools/call` through the right client. The result goes back to the model as an ordinary tool result.

Resources and prompts usually aren't tool calls at all. The application picks resources to put into context, and the user picks prompts, often as slash commands.

## A2A, step by step
1. **Discovery is code again.** The client agent fetches the remote agent's Agent Card from `/.well-known/agent-card.json`, or looks it up in a registry or a configured list.
2. **The remote agent gets wrapped as a tool.** The framework turns each remote agent, or each of its skills, into a tool for the model. The tool's description comes from the card, something like "Billing agent: answers questions about invoices and refunds".
3. **Delegation is a tool call.** The model calls that tool. The framework turns the call into an A2A message, follows the task through its lifecycle, and returns the resulting artifacts as the tool result.

Frameworks do this wrapping for you:
- **Google ADK** can treat a remote A2A agent as a sub-agent. Its LLM-driven delegation is itself a special function call, `transfer_to_agent`.
- **OpenAI's Agents SDK** presents handoffs to the model as tools.

## One difference worth saying out loud
An MCP tool is usually a deterministic function that answers straight away. An A2A task can run for minutes, stream partial results, or come back as "input-required", asking a follow-up question. So "agent as a tool" is a simplification. The wrapper has to handle polling or streaming, and it has to answer that follow-up, either by itself or by asking your user, within the same task.

## The exception: discovery as a tool call
With hundreds of tools across many servers, putting every definition into the prompt wastes context and confuses the model. So hosts give the model a "search tools" tool, and it loads definitions only when it needs them. Anthropic's API, for example, offers a tool-search tool for exactly this. The agent-level version is a "find an agent" tool that searches a registry of Agent Cards by skill. That's the one case where discovery itself is a tool call.

*In an interview:* "Tool calling is the model's only verb. Discovery is done by code: the MCP client lists the tools, and the A2A client reads Agent Cards. The framework then presents both MCP tools and remote agents to the model as tool definitions. When the model calls one, the host translates it into an MCP tool call or an A2A task. The exception is scale: with hundreds of tools or agents, you give the model a search tool, so it can discover what it needs on demand."

## How sure can we be?

This area is new, so it's worth separating what is documented from what is only convention.

- **Documented in the MCP docs:** the client discovers tools with `tools/list`. The application combines the tools from every connected server into one registry the model can use. When the model picks a tool, the application routes the call to the right server. For MCP, "discovery by code, use as a tool call" is the design itself.
- **Documented by the major SDKs:** OpenAI's Agents SDK says "Handoffs are represented as tools to the LLM", so a handoff to a "Refund Agent" becomes a tool called `transfer_to_refund_agent`. Google's ADK builds a remote agent from its Agent Card URL and adds it as a sub-agent that the root agent's model delegates to.
- **Documented for the scale exception:** Anthropic's tool-search docs say tool definitions from several MCP servers can take around 55,000 tokens before any work starts, and that tool selection gets worse beyond 30 to 50 tools.
- **An argument, not a survey:** chat model APIs give the model essentially one structured way to request an action: the tool call. So any framework that lets the model decide to use an outside capability ends up presenting it as a tool.
- **Still young:** the A2A spec defines how agents talk on the wire, not how a client's model decides to delegate. "Wrap the remote agent as a tool or sub-agent" is today's convention in the major frameworks, not part of the protocol. Frameworks also differ in how they handle an A2A task that comes back asking a follow-up question.

A useful habit with fresh tech: read the spec, then the official quickstart (what most people copy), then two or three independent frameworks, and say how confident you are.

## Sources

- [MCP architecture overview](https://modelcontextprotocol.io/docs/learn/architecture)
- [OpenAI Agents SDK: Handoffs](https://openai.github.io/openai-agents-python/handoffs)
- [Google ADK: consuming a remote A2A agent](https://adk.dev/a2a/quickstart-consuming/)
- [Claude tool search tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool)
