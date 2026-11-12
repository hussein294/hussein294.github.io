---
title: "Why A2A agents don't overwrite each other's Agent Cards"
description: "The well-known path is relative to each agent's domain, and there are three ways to host many agents on one domain."
date: 2026-11-11
track: engineering-qa
tags: [a2a, agents, protocols]
draft: false
---
A common confusion with A2A: every agent publishes its Agent Card at the same path. So why don't agents overwrite each other's cards? The answer is in what the path is relative to. `/.well-known/agent-card.json` isn't one shared location. It's a fixed path on each agent's own server, so it's relative to that agent's domain.

- `https://billing.example.com/.well-known/agent-card.json`
- `https://search.example.com/.well-known/agent-card.json`

Those are two different files on two different servers, so nothing gets overwritten. It works like `robots.txt` or `/favicon.ico`: every website has one at the same path, and they never clash because the domain tells them apart. Think of it as every house having its front door in the same spot. The street address is what makes it a different house.

**The client side can't clash either.** Client agents only read the card, with a plain HTTP GET, and never write to it. A thousand clients can read the same card, like a thousand browsers loading the same page. Each client's work is kept apart by its own task and context IDs.

**Where your intuition is right: one domain hosting many agents.** The root well-known path gives one card per domain, so this case needs a decision. There are three common answers:

1. **Give each agent its own base path or subdomain.** Frameworks put the same file name under each agent's base URL. The Google ADK quickstart does exactly this: its agent lives at `http://localhost:8001/a2a/check_prime_agent`, and its card sits under that path. Strictly, the web standard for well-known paths puts them at the root of a domain. So the root card acts as the domain's "front door" agent, and frameworks reuse the same name under each agent's own path.
2. **Make one agent with many skills.** In A2A, an "agent" is a server endpoint, and its card can list many skills. So "five agents on one server" can just as well be one agent card listing five skills, with internal routing behind it.
3. **Use a registry.** The well-known path is only one discovery method. A card can live at any URL, and the A2A docs also describe finding cards through curated registries or direct configuration. Inside a company, a registry that lists every agent's card is the usual answer at scale.

One more detail clears up a related confusion. The card's location and the agent's working endpoint are separate. The card says where to send tasks, so the well-known path is just where you find the agent's description, not where it runs.

*In an interview:* "The well-known path is relative to each agent's domain, like `robots.txt`, so cards never collide. When one domain hosts several agents, you give each its own base path or subdomain, expose one agent with several skills, or list the cards in a registry."

## Sources
- [A2A specification](https://a2a-protocol.org/latest/specification/)
- [Google ADK: consuming a remote A2A agent](https://adk.dev/a2a/quickstart-consuming/)
