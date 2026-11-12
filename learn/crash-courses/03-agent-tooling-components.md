---
title: "Agent tooling: the components, in 30 minutes"
description: "One-line definitions of every part of MCP, A2A, LangChain, LangGraph, LangSmith and the main alternative frameworks, and how they fit together."
date: 2026-11-11
track: crash-courses
series_order: 3
tags: [agents, mcp, a2a, langchain, langgraph]
draft: false
---
Component definitions only, not usage or code. MCP reflects the 2026-07-28 specification.

Every entry here is a definition, in the spirit of "a PyTorch Module is a layer with learnable weights".

## Module 1 (0:00 to 0:08): MCP, the Model Context Protocol

**What it is:** an open standard for connecting AI applications to tools and data. One protocol replaces a custom integration for every app and tool pair, which is why people call it "USB-C for AI". Anthropic released it in November 2024 and donated it to the Agentic AI Foundation, under the Linux Foundation, in December 2025.

**The three roles.**
- **Host:** the AI application the user works in, like Claude Desktop, an IDE or your own agent. It owns the model, the interface and the security decisions.
- **Client:** a connector inside the host that talks to exactly one server. A host using five servers runs five clients.
- **Server:** a program that exposes capabilities to clients. It runs locally on the user's machine or remotely as a web service, like a GitHub server, a Postgres server or your company's search server.

**How messages travel.**
- **JSON-RPC 2.0:** the message format. Every exchange is a request with a method name, its response, or a one-way notification.
- **Transports:** the channel. stdio is for a local server started as a subprocess. Streamable HTTP is for remote servers. The older HTTP-plus-SSE transport is deprecated.

**What a server offers: the three primitives.**
- **Tools:** actions the model can choose to call. Each has a name, a description, a JSON Schema for its inputs and optionally one for its outputs. Tools can carry hints, like read-only or destructive. The model controls when they're used.
- **Resources:** data the server exposes for reading, each identified by a URI, like a file, a database row or a document. Resource templates describe whole families of URIs. The application controls what goes into context.
- **Prompts:** reusable templates the server offers to the user, often shown as slash commands. The user controls them.

**What goes from server back to the user.**
- **Elicitation:** the server asks the user for missing input, like a confirmation or a form field, through the client.
- **Sampling and roots:** sampling let a server borrow the client's LLM, and roots told a server which folders it could touch. Both are deprecated in the current spec, along with protocol-level logging.

**What changed in the current spec, dated 28 July 2026.**
- **Stateless:** there's no longer an opening handshake or a session. Every request carries its protocol version and the client's capabilities, so any server instance can answer it. That makes remote servers much easier to scale.
- **Discovery:** a server/discover call returns a server's supported versions, capabilities and identity.
- **Multi-round-trip requests:** when a server needs more input mid-call, it returns an "input required" result. The client gathers the input, then retries the original request with it.
- **Subscriptions:** one long-lived stream carries change notifications, like "the tool list changed".
- **Extensions:** optional add-ons, versioned separately from the core. Tasks, for long-running work the client checks on, is now an extension. So is MCP Apps, which lets a server show interactive UI in a sandboxed frame inside the host.

**Security pieces.**
- **Authorization:** remote servers use OAuth-based authorization, with tokens issued for that specific server.
- **The risks to name:** tool poisoning, meaning hidden instructions in a tool description. Also over-broad permissions and untrusted tool output.

*If they ask, "How is MCP different from function calling?":* "Function calling is the model-level mechanism: the model emits a structured call with a name and arguments, and my code runs it. MCP standardises everything around that: how an app discovers tools, how it calls them across a process or network boundary, and how auth works. So any MCP server works with any MCP host, without custom integration."

*If they ask, "Tools, resources or prompts: what's the difference?":* "Who's in control. The model chooses tools, the application chooses resources, and the user chooses prompts."

## Module 2 (0:08 to 0:13): A2A, the Agent2Agent protocol

**What it is:** an open standard for agents to find each other and delegate work, even across companies and frameworks. Google launched it in April 2025. Version 1.0, the first stable release, shipped in March 2026. In August 2026 it joined MCP in the Agentic AI Foundation. MCP is agent to tool. A2A is agent to agent.

**The roles.**
- **User:** the person or system with the goal.
- **Client agent:** the agent that delegates a task.
- **Remote agent:** the agent that does the work, running as an A2A server. It's opaque: the client never sees its prompts, tools or memory.

**The components.**
- **Agent Card:** a JSON document the remote agent publishes at /.well-known/agent-card.json. It's the agent's business card: name, description, version, endpoint, skills, capabilities and the authentication it accepts. Version 1.0 cards can be signed, so callers can verify who published them.
- **Skill:** one thing the agent can do. The card lists each skill with an ID, a description, examples and the input and output formats it accepts.
- **Capabilities:** optional features the agent supports, like streaming, push notifications, or a fuller card for authenticated callers.
- **Task:** the unit of work, with an ID and a lifecycle. It starts as submitted, then working. It can pause at input-required or auth-required. It ends as completed, failed, canceled or rejected.
- **Context:** an ID that groups related tasks and messages into one conversation.
- **Message:** one turn of communication, with a role of user or agent.
- **Part:** the smallest piece of content inside a message or artifact: text, a file, or structured JSON data.
- **Artifact:** an output the task produces, like a report or a file, made of parts.
- **Streaming:** a live feed of status and artifact updates while the task runs.
- **Push notifications:** for long tasks, the remote agent calls the client's webhook when something changes, so the client doesn't have to stay connected.
- **Protocol bindings:** the same operations over JSON-RPC 2.0, gRPC, or plain HTTP with JSON.
- **Security schemes:** standard authentication declared in the card: API keys, OAuth 2.0, OpenID Connect or mutual TLS.
- **Extensions:** optional add-ons beyond the core protocol, declared in the card.

*If they ask, "Why not just call the other agent's API?":* "Inside one team, you could. A2A standardises discovery, long-running tasks, streaming and authentication, so agents from different teams or vendors work together without custom glue. And the remote agent stays opaque, which protects each side's internals."

## Module 3 (0:13 to 0:23): LangChain, LangGraph and LangSmith

These are three products from one company, at three layers. LangChain gives you the parts. LangGraph runs them as a stateful graph. LangSmith observes, evaluates and deploys them. LangChain 1.0 and LangGraph 1.0 both shipped in October 2025.

**LangChain: the parts.**
- **Chat model:** one common interface to any provider's LLM. Messages go in and a message comes out, with support for streaming, tool calling and structured output.
- **Message:** one turn of a conversation, typed by role: system, human, AI or tool. Its content is made of blocks, like text, images, reasoning or tool calls.
- **Prompt template:** a message list with blanks, filled in at run time.
- **Tool:** a function the model may call, defined by a name, a description and an input schema.
- **Structured output:** a schema the model's answer must fit. It comes back as a validated object instead of free text.
- **Document:** a piece of text plus metadata, like its source and page number.
- **Document loader:** reads a source, like a PDF, a web page or a database, into documents.
- **Text splitter:** cuts documents into chunks.
- **Embedding model:** one interface that turns text into vectors.
- **Vector store:** one interface over any vector database, for storing chunks and searching them by similarity.
- **Retriever:** anything that takes a query and returns relevant documents. A vector store can act as one, and so can BM25 or a hybrid of both.
- **Runnable:** the common interface every component shares, with invoke, batch and stream. LCEL, the LangChain Expression Language, chains runnables into pipelines.
- **Agent:** in 1.0, one standard agent. It's a model, tools and a system prompt, running the loop of calling a tool and reading the result until it's done. It's built on LangGraph.
- **Middleware:** hooks that run before and after each model call and around each tool call. They're used to summarise long histories, get human approval for risky tool calls, redact personal data, retry and cap calls.
- **Packages:** langchain-core holds the base interfaces, and langchain holds the agent and middleware. Integration packages connect each provider, and langchain-classic keeps the older chains.

**LangGraph: the runtime.** It models an agent or workflow as a graph that passes shared state from step to step.
- **State:** the shared data object the whole graph reads and writes, like messages, documents or a plan. Its shape is declared up front.
- **Reducer:** the rule for merging an update into one state field. For example, new messages get appended rather than overwriting old ones.
- **Node:** one step, a function that reads state and returns updates. It might call an LLM, run a tool, or be plain code.
- **Edge:** a fixed path from one node to the next.
- **Conditional edge:** a routing function that picks the next node from the current state. This is how branches and loops happen.
- **START and END:** the graph's entry and exit points.
- **Compiled graph:** the runnable built from the definition. It runs in super-steps, and nodes in the same step can run in parallel.
- **Checkpointer:** saves the state to a database after every step. That one component gives you memory across turns, recovery after a crash, pauses for human input, and "time travel" to replay or branch from an earlier step.
- **Thread:** the ID of one conversation or run, which groups its checkpoints.
- **Interrupt:** a pause that waits for a human, for example to approve an action, then resumes from the same point.
- **Command:** a node result that updates state and chooses the next node in one go.
- **Send:** dynamic fan-out. It runs one node many times in parallel, each with a different input, as in map-reduce.
- **Subgraph:** a whole graph used as a single node inside another graph.
- **Store:** long-term memory shared across threads, like user preferences, organised by namespace.
- **Streaming modes:** what to stream during a run: the full state, state updates, LLM tokens or custom events.

**LangSmith: observability, evaluation and deployment.**
- **Trace:** the record of one request from start to finish, made of nested runs. Each model call, tool call and retrieval shows its inputs, outputs, tokens, latency and cost.
- **Project:** a container for the traces from one app or environment.
- **Dataset:** saved example inputs, with reference outputs where you have them. A golden set lives here.
- **Evaluator:** a function or LLM judge that scores an output.
- **Experiment:** one run of an app version over a dataset, scored by evaluators, so versions can be compared.
- **Annotation queue:** a workflow for humans to review and label traces.
- **Prompt hub:** versioned prompts stored outside the code.
- **LangSmith Deployment:** the new name, since October 2025, for LangGraph Platform. It hosts LangGraph agents with persistence, task queues, scheduled runs, Studio for visual debugging, and MCP and A2A endpoints.

*If they ask, "LangChain or LangGraph?":* "They're different layers. LangChain gives standard parts and a ready-made agent loop. LangGraph is the runtime underneath, for when I need control: explicit steps, branches, loops, parallel work, checkpoints and human approval. A simple tool-using agent fits LangChain. A multi-step workflow with approvals and recovery fits LangGraph."

*If they ask, "Why use a checkpointer?":* "It saves state after every step. From one component, that gives conversation memory, crash recovery, pauses for human approval, and replay for debugging."

## Module 4 (0:23 to 0:30): the other options, and how it all fits

**Other frameworks, defined by their parts.**
- **LlamaIndex**, built around data and RAG: Documents are split into Nodes, and nodes go into an Index. A Retriever fetches nodes, and a Query Engine retrieves and writes an answer. A Chat Engine adds conversation. Workflows are its event-driven steps for agents and pipelines.
- **Haystack**, by deepset: a Component is a single-purpose unit with typed inputs and outputs, like a retriever or a generator. A Pipeline wires components into a graph. A Document Store holds the documents.
- **DSPy**, from Stanford: a Signature declares inputs and outputs, like "question -> answer". A Module is a strategy that runs a signature, like chain of thought or ReAct. An Optimizer tunes the prompts and examples against your metric. You program the behaviour, and DSPy writes the prompts.
- **CrewAI:** an Agent is a role with a goal and a backstory. A Task is a job with an expected output. A Crew is a team of agents working through tasks. The Process sets the order: sequential, or hierarchical with a manager. Flows add event-driven control with state.
- **OpenAI Agents SDK:** an Agent is instructions, a model and tools. A Handoff passes control to another agent. Guardrails check inputs and outputs. Sessions keep conversation memory. The Runner executes the loop, and tracing records it.
- **Google ADK**, the Agent Development Kit: LLM agents do the reasoning. Workflow agents (sequential, parallel and loop) control the order without an LLM. Tools include functions, other agents and MCP servers. A Session holds one conversation's events and state. Memory holds knowledge across sessions. The Runner executes it all.
- **Microsoft Agent Framework:** agents, with threads holding their conversations. Workflows are graphs of executors joined by edges, with events, checkpoints and requests for human input. Ready-made orchestrations cover sequential, concurrent, handoff, group-chat and Magentic patterns.
- **Pydantic AI:** an Agent with typed dependencies, tools and a validated output type, in the spirit of FastAPI.
- **Claude Agent SDK:** the agent loop behind Claude Code, with built-in tools, subagents, hooks, permissions and MCP support.

**The supporting cast.**
- **Observability and evaluation:** Langfuse is an open-source alternative to LangSmith, built from traces, observations, sessions and scores. Arize Phoenix is another. Ragas provides RAG metrics and test-set generation.
- **Gateways:** LiteLLM and OpenRouter put one OpenAI-style API in front of many providers, with routing, fallbacks and spending limits.
- **Vector databases:** a collection holds points. A point is an ID, a vector and a payload of metadata. An ANN index, usually HNSW, searches the vectors, and a payload index makes filtering fast. Namespaces or partitions separate tenants.
- **Model serving:** vLLM and SGLang serve open models at scale. Ollama runs models on a single machine.

**How it all fits, as layers.**
1. **Models:** provider APIs, gateways, or self-hosted engines.
2. **Building blocks:** LangChain, LlamaIndex, Haystack, DSPy.
3. **Orchestration:** LangGraph, CrewAI, OpenAI Agents SDK, Google ADK, Microsoft Agent Framework.
4. **Protocols:** MCP connects agents to tools and data. A2A connects agents to other agents.
5. **Data:** vector databases, graph databases like Neo4j, and document stores.
6. **Observability and evaluation:** LangSmith, Langfuse, Phoenix, Ragas.

My own projects touch most of these layers: AutoScript Engine runs on Ollama, LangChain and A2A, Web-RAG is traced in LangSmith, and GraphRAG stores its knowledge graph in Neo4j.

*If they ask, "Which framework would you choose?":* "Whichever gives the control the problem needs, with the least abstraction. For a stateful agent with approvals and recovery, LangGraph. For data-heavy RAG, LlamaIndex or plain code. For tuning prompts against a metric, DSPy. And I'd keep tools behind MCP and remote agents behind A2A, so the framework choice stays reversible."

*If they ask, "Isn't LangChain too much abstraction?":* "That was a fair criticism of the early versions. Version 1.0 cut it down to a standard agent with middleware, on top of LangGraph. I use the parts that save time, like the provider interfaces, and write plain code wherever an abstraction would hide the prompts."

## Sources

- [MCP specification changelog, 2026-07-28](https://modelcontextprotocol.io/specification/latest/changelog), the official list of changes since 2025-11-25
- [A2A specification](https://a2a-protocol.org/latest/specification/) and [A2A joins the Agentic AI Foundation](https://aaif.io/blog/a2a-joins-aaif)
- [LangSmith Deployment](https://www.langchain.com/langsmith/deployment), for the rename from LangGraph Platform
- [LangChain and LangGraph 1.0](https://www.langchain.com/blog/langchain-langgraph-1dot0), LangChain, Oct 2025
- [Microsoft Agent Framework workflows](https://learn.microsoft.com/en-us/agent-framework/user-guide/workflows/core-concepts/overview)
