# App integration and prompting: open directions

**Status:** Product direction and design questions from the current project discussion. These possibilities are not settled format requirements, operation semantics, or a definition of 1.0. Existing candidate specifications remain authoritative for their implemented behavior.

## Purpose and priorities

Harmonomicon aims to provide an expressive activity language and runtime that lets a host app support many user-authored, composable, adjustable group activities. Authors should be able to combine supported steps and change declared settings without a new complete-activity implementation for each arrangement. In-app composability is the primary goal. Cross-platform portability is a secondary potential benefit whose user demand is uncertain; the existing independent implementations provide evidence about semantic clarity and reproducibility. Earlier portability research remains useful historical context.

## Three related design areas

| Area | Questions to resolve |
|---|---|
| Activity semantics | Who receives a prompt or may respond? What triggers it? When does a window open and close? What happens when someone misses a response? Does a deadline start from a scheduled time, a transition, delivery, acknowledgment, or another explicit event? |
| Host notification capabilities | Which delivery mechanisms can the app provide: SMS, push, or in-app prompts? What can the app observe about attempted delivery, receipt, or display? Which choices can it actually support? |
| Participant permissions and preferences | Has the participant permitted a channel, and which available channel do they prefer? How should denied permission, disabled notifications, or changed preferences affect participation and compatibility? |

These concerns interact, but an available channel does not itself define a response deadline, and a participant preference does not establish a delivery guarantee. The current trusted-clock operation rules are not changed by these questions.

## Possible authoring and integration approaches

Authoring tools could populate prompting choices from the host's supported capabilities so authors can configure an activity for the app in which it will run. Whether choices belong in package declarations, instance settings, host configuration, or some combination remains open. This does not yet prescribe a capability-discovery API, notification token, or authoring interface.

An explicit requirement for a particular channel would constrain compatibility: a host or participant unable to use that channel might not be able to run the activity as authored. A channel preference and a required channel would need distinct meanings. Whether to require a channel, permit alternatives, or reject an incompatible setup is an unresolved design choice.

A prompt shown only when someone next opens the app may suit an asynchronous activity. It cannot silently replace time-sensitive prompting while preserving a claim of equivalent activity semantics. For example, showing a scheduled one-minute prompt hours later raises an explicit decision about whether the original window was missed or a different event starts a new deadline. Any fallback would need to preserve the declared behavior or make a changed activity arrangement explicit. No such fallback or delivery-triggered timer is specified here.

Future investigation can test these choices with concrete activities and host capabilities. It should separate enforced software facts from unverified delivery, attention, or offline actions, and bring unresolved choices to the [pre-1.0 review](../ROADMAP.md#proposed-development-oversight-and-review-checkpoint).
