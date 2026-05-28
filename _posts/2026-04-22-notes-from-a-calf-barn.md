---
layout: post
title: "Notes from a Calf Barn"
subtitle: "What field work teaches you that a dataset can't"
date: 2026-04-22
tags: [machine learning, fieldwork, IoT]
description: "Building IoT sensors to catch respiratory illness in calves early. The model was the easy part. The barn was not."
---

Part of my work at Fraunhofer involves a sensor system that tries to spot respiratory illness in calves before a human would notice it. I spend a fair amount of time thinking about model architectures. I spend far more time thinking about dust, humidity, and where a curious animal can reach.

## The barn does not care about your pipeline

In a notebook, the data is clean and the labels are correct. In a barn, a sensor gets knocked loose, a cable gets chewed, the lighting changes every hour, and a calf decides your carefully positioned camera is the most interesting thing it has ever seen. None of that shows up when you train on a tidy dataset, and all of it shows up the moment you deploy.

The lesson I keep relearning is simple. The hard part of applied machine learning is usually not the learning. It's everything around it.

## A short list of things that broke

- A temperature reading that drifted all day because the sensor sat in direct sun for two hours.
- Annotations that disagreed because two people had slightly different ideas of where a "cough event" starts.
- A model that looked excellent on paper because it had quietly learned to recognise the time of day.

## Why I still like it

It would be easy to find this frustrating. Mostly I find it grounding. The work has a clear point, the people on the farm are generous with their time, and the feedback loop is honest. Either the system helps catch something early or it doesn't.

That kind of honesty is rarer in software than it should be.
