---
layout: post
title: "Teaching an Agent to Read Code"
subtitle: "Notes from the AI4SoftwareEngineering project"
date: 2026-05-12
tags: [AI, agents, software engineering]
description: "An LLM agent that reads a repository and draws the UML diagram a human would have drawn. What worked, what didn't, and why class diagrams are a surprisingly good test."
---

For the past few months I've been building a semi-autonomous agent that reads a codebase and produces a UML class diagram from it. The short version is that it works more often than I expected, and fails in ways that taught me a lot about both LLMs and my own assumptions.

## Why class diagrams

A class diagram is a good target because it sits at an awkward middle distance. It isn't a single function you can summarise in a sentence, and it isn't the whole system either. To draw a good one, the model has to decide what counts as important, which classes belong together, and which relationships are worth showing. That is exactly the kind of judgement that's hard to fake.

> The interesting failures were never syntax. They were taste.

## The loop

The agent runs on a fairly standard ReAct setup: think, pick a tool, read the result, think again. The tools are deliberately small. It can list files, open one, search for a symbol, and write to the diagram. Keeping the tools small made the traces much easier to read when something went wrong.

A few things that helped:

- Giving the model a way to say "I don't have enough context yet" instead of guessing.
- Logging every tool call so I could replay a run and see where it lost the thread.
- Building the evaluation dataset from real repositories with hand-drawn diagrams, rather than synthetic ones.

## What's next

The current weak spot is large repositories, where the model runs out of attention before it has seen enough of the system. I'm working on a way to let it build up a rough map first and then zoom in, which is roughly how a person reads unfamiliar code anyway.

More on that once it actually works.
