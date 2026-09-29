# BeReal daily post

## Identity and context

- **Description:** People in a time zone receive a common daily photo prompt; friends' posts become viewable after a person posts their own.
- **Group and mode:** Connected friends in a digital service; distributed and asynchronous after a simultaneous notification.
- **Facilitator:** The service sends notifications, marks timing, and controls feed access.
- **Experience:** A shared daily moment and reciprocal viewing.

## Preparation

Participants need accounts, connections to friends, an app and a device with front and back cameras. These are conditions of the documented product, not proposed requirements for every portable activity.

## Procedure

1. At an unpredictable time each day, the service sends a notification simultaneously to people in the same time zone.
2. A recipient has two minutes to open the app, take a front/back-camera post, and publish it on time. They may retake it before publishing.
3. After the window, they may still post; the product marks the post late.
4. After a person posts, the service permits that person to view friends' posts. Before posting, the friends feed is gated.
5. The next day's notification starts another occurrence. The cited page does not specify an end to this recurring activity.

## Rules and choices

- **Schedule:** One common prompt per time zone each day; exact time is not disclosed in advance by the source.
- **Per-person state:** Not notified → notified → posted on time or late. No-post is possible.
- **Visibility:** Friends' posts are hidden from the participant until their own post; location and wider sharing are participant choices before posting.
- **Completion:** Posting completes an individual's occurrence, while the service continues daily.

## Variants

The cited help page describes optional location display and sharing to a broader feed. These alter publication visibility, not the daily prompt sequence. The [RealGroup notification page](https://help.bereal.com/hc/en-us/articles/15753219937821-RealGroup-It-s-Time-to-BeReal-notification) separately documents a group notification setting and a maximum of one such notification per group per day; it does not define a full custom-prompt activity here.

## Exceptions and open questions

The page documents late posting but does not specify offline delivery, account removal, missed entire days, or reconciliation across time-zone travel. It says the two-minute window applies to opening the app and taking the post; a portable model should not infer an exact deadline for all upload completion stages without more evidence.

## Access and participation

The documented product requires camera hardware and ability to receive and respond to notifications. The source does not describe alternate media or a non-camera participation route. If abstracted into a different activity, media and access rules must be explicit rather than assumed from this product.

## Mechanisms and possible software role

**Mechanisms:** Recurring schedule, broadcast prompt, deadline with late branch, participant submission, post-to-view gate, optional wider visibility. This activity is implemented by software; a portable package would need host capabilities for scheduling, identity, media storage, visibility enforcement, and late-state tracking.

## Sources and evidence

| Source | What it supports |
|---|---|
| [BeReal Help Center, *Time to BeReal*](https://help.bereal.com/hc/en-us/articles/7350386715165--Time-to-BeReal) | Daily notification, two-minute window, retakes, late posting, view gate, visibility choices |
| [BeReal Help Center, *RealGroup notification*](https://help.bereal.com/hc/en-us/articles/15753219937821-RealGroup-It-s-Time-to-BeReal-notification) | Group notification setting and daily maximum only |

This card describes current help-center behavior, which may change. Mechanism and package requirements are analysis.
