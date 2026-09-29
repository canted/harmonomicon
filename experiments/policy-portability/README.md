# Assignment-policy portability experiment

This experiment isolates the [composed Cover and Response slice's](../composition/definitions/cover-response.json) offer-assignment decision. The surrounding activity plan remains unchanged. A separate [versioned policy contract](contract.md) gives the ID range, exact score arithmetic, exposure ordering, tie-breaker, replay behavior, and required capability token. [Policy metadata](policy.json) points to the original plan.

Run from the repository root:

```sh
python3 experiments/policy-portability/check.py
```

The checker compares [JavaScript](run.mjs), [Python](run.py), and [Ruby](run.rb) on small-ID forward and reverse request orders, a large-ID score tie, duplicate delivery, and an unsupported policy version. For every checkpoint fixture it restarts each producer snapshot in each consumer runtime and compares the final output with uninterrupted execution. The [findings](findings.md) state what this establishes and what remains outside the test.
