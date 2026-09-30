# Writing an activity as a runbook

An activity package has instructions and a runbook. Instructions explain the activity to people. The runbook tells the app exactly what to accept, store, show, and do next. The complete [example files](examples/) include identity, participant bounds, provenance, and required app features. The snippets here show their runbooks.

## A guessing game

In the digital Two Truths example, each participant takes a turn. They publish three statements and privately select the invented statement. Everyone else may submit one private guess. The speaker ends guessing when ready; the app reveals the answer and guesses, then starts the next speaker's turn.

The package supplies that order:

```json
{
  "steps": [
    {
      "id": "turns",
      "op": "for_each@1",
      "over": "participants",
      "steps": [
        {
          "id": "publish",
          "op": "collect@1",
          "actors": "turn",
          "prompt": "Publish three statements and select the invented statement.",
          "fields": {
            "items": {"type": "text_list", "count": 3, "visibility": "group"},
            "answer": {"type": "index", "indexOf": "items", "visibility": "private"}
          },
          "close": "all",
          "afterMs": null
        },
        {
          "id": "guess",
          "op": "collect@1",
          "actors": "others",
          "prompt": "Guess the invented statement.",
          "fields": {
            "guess": {"type": "index", "indexOf": "publish.items", "visibility": "private"}
          },
          "close": "turn",
          "afterMs": null
        },
        {"id": "reveal", "op": "reveal@1", "sources": ["publish", "guess"]}
      ]
    }
  ]
}
```

`collect@1` is used twice with different fields, actors, and close rules. The first collection finishes when its one eligible actor publishes. The second waits for the speaker to advance. `reveal@1` is a separate step whose position determines when information becomes public. `for_each@1` supplies turn repetition. The app implements these operations once; the package combines them into this game.

The [List Game package](examples/list-game.json) changes the visible list length to five and uses a private text category and text guesses. It uses the same sequence and operation names. A package revision can also add a guess timeout by changing that step's `afterMs`, or collect all guesses before revealing by changing its `close` to `all`. Changing package content requires a new package version.

## A poll uses the same collection operation

The [poll package](examples/choice-poll.json) has no speaker rotation. It collects one private `choice` field from each participant, closes when the organizer advances or one minute passes, then reveals the collection and tallies the choices. Those three declared steps are `collect@1`, `reveal@1`, and `tally@1`. The organizer's advance remains an app-enforced action.

The [prompted routine](examples/see-think-wonder.json) uses three collections in sequence, with group-visible text and organizer-controlled progression. The [timed story](examples/timed-story.json) uses participant repetition and `append@1`, which keeps cumulative text and advances when a participant writes or their minute expires.

## Try a new arrangement

The reference check authors an additional package by taking the check-in's collection and reveal, then adding the timed story's participant repetition. It imports and runs the resulting JSON in both app hosts. Neither interpreter has a branch for this combination. This is the test that distinguishes composing package steps from selecting a complete predefined activity.

Begin with a complete example, give it your own package ID, and edit its step sequence and configuration. Declare every used operation in `requires`. The [schema](package.schema.json) checks structure; the [validator](runtime.py) additionally checks references, scope, types, unique IDs, and declared requirements. The [operation reference](operations.md) defines the executable choices supported in this candidate.
