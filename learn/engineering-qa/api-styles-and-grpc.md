---
title: "REST, WebSockets, GraphQL and gRPC: what they are, and why gRPC is faster"
description: "Where each one sits in the network stack, what kind of thing each one is, and the four reasons gRPC beats REST for internal services."
date: 2026-11-11
track: engineering-qa
tags: [apis, grpc, networking, backend]
draft: false
---
These four names come up together all the time, but they are not the same kind of thing. Here is where each one sits, and why gRPC is the usual choice between internal services.

## What kind of thing are REST, WebSockets and GraphQL?

They aren't all the same kind of thing, which is why they're hard to place. In network terms, all of them live at the application layer (layer 7), on top of TCP. Inside that layer, though, they sit at different levels:

- **Wire protocols:** HTTP and WebSocket. These define the actual bytes on a connection.
  - WebSocket (RFC 6455) starts as an HTTP request with an "Upgrade" header. It then turns that TCP connection into a persistent, full-duplex channel, where either side can send a message at any time.
  - HTTP/1.1 and HTTP/2 run over TCP. HTTP/3 runs over QUIC, which runs over UDP.
- **API styles, built on those protocols:**
  - **REST** is an architectural style, not a protocol. It means resources named by URLs, acted on with HTTP methods (GET, POST, PUT, DELETE), stateless requests, standard status codes and cacheable responses. Roy Fielding defined it in his 2000 dissertation. A "REST API" is just HTTP used in that style, usually with JSON.
  - **GraphQL** is a query language and a spec. The client sends one query to a single endpoint, usually as an HTTP POST, and names exactly the fields it wants, checked against a typed schema. That fixes over-fetching and under-fetching, but caching gets harder. Its live-update "subscriptions" usually run over WebSockets.
  - **RPC** is the third style: call a remote function as if it were local. gRPC is RPC, and so is JSON-RPC, the format MCP and A2A use.
- **Data formats:** JSON, XML and Protocol Buffers. OSI would call this the presentation layer, but the TCP/IP model lumps it into "application".

Two more you'll hear:
- **SSE (Server-Sent Events):** a one-way stream from server to client over an ordinary HTTP response. Most LLM APIs use it to stream tokens.
- **Webhooks:** plain HTTP calls the server makes to your URL when something happens.

If you need one umbrella term for REST, GraphQL and gRPC, say "API styles".

*In an interview:* "They're all application-layer, but at different levels. HTTP and WebSocket are wire protocols. REST, GraphQL and RPC are API styles built on top of them. JSON and Protobuf are the data formats inside."

## Why gRPC beats REST for internal services

1. **Binary serialisation.** gRPC uses Protocol Buffers, a compact binary format.
   - Fields are identified by number, not name, and integers use variable-length encoding.
   - JSON is text: every message repeats the field names, numbers are written out as characters, and parsing text costs CPU.
   - Protobuf messages are often several times smaller, and much faster to encode and decode.
2. **HTTP/2.** Many calls share one long-lived connection, each in its own stream.
   - There's no new connection or TLS handshake per call, and no waiting for the previous response.
   - HPACK compresses headers, so repeated headers cost almost nothing.
   - Typical REST over HTTP/1.1 handles one request at a time per connection, so clients have to keep pools of connections open.
3. **Streaming.** Server, client and two-way streaming all run on the same connection, so there's no need for polling.
4. **A typed contract.** The .proto file generates the client and server code. There's no hand-written parsing, and both sides agree on types at build time.

Two points of nuance will make the answer stand out:
- **The gap matters most for many small, frequent calls.** For model inference that takes hundreds of milliseconds, the transport overhead is small, with one exception: big payloads. JSON has to base64-encode audio or images, which makes them 33% bigger, while Protobuf carries raw bytes.
- **REST is still the default for public APIs.** Browsers, curl and every tool speak it, and it's easy to debug. Browsers can't call gRPC directly; they need gRPC-Web and a proxy.

Plain REST between a gateway and its inference services is a defensible choice when inference time dominates each call, and it's simpler to build and debug. gRPC pays off for streaming audio, or for many small calls per request.

*In an interview:* "Binary Protobuf instead of JSON text, HTTP/2 multiplexing and header compression on one persistent connection, and native streaming. It matters most for chatty internal calls. For heavy inference, the model's time dominates."

## Further reading

- [RFC 6455: The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455)
- [Introduction to gRPC](https://grpc.io/docs/what-is-grpc/introduction/)
- [Protocol Buffers encoding](https://protobuf.dev/programming-guides/encoding/)
- [Learn GraphQL](https://graphql.org/learn/)
