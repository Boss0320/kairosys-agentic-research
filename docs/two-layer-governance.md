# Two-layer governance: correctness cannot be averaged

A research system has two different quality questions:

1. **May this artifact travel?** The integrity gate checks hard validity conditions.
2. **Is this artifact useful enough?** The utility score measures completed research dimensions.

Kairosys keeps those questions separate. The runnable mechanism lives in [`quality_governance.py`](../demo/kairosys_case/quality_governance.py), its adversarial contract lives in [`test_quality_governance.py`](../tests/test_quality_governance.py), and the [offline dossier](../web/index.html) renders the supplied decision without recalculating it.

## The contract

The synthetic dossier assigns transparent weights across fundamentals, industry and supply chain, market context, valuation and scenarios, catalysts and falsifiers, and analyst next steps. A clean draft needs a utility score of at least `0.75` before it can become editable.

The integrity gate fails on a blocking final-report finding or an insufficient financial state. When it fails, the uncapped utility score remains visible, while the effective score cannot exceed `0.40`. This makes the policy legible: breadth is useful only after the factual foundation survives.

These weights are part of this public demonstration contract; they are not presented as a hidden runtime recipe.
The mechanism receives the completed-dimension set as typed upstream input. It demonstrates admission semantics; it does not pretend this small package independently performs or verifies every research domain.

## Complete + clean

`ready_report` completes all six dimensions. Its integrity gate passes, utility score is `1.00`, effective score remains `1.00`, and delivery is an editable draft.

This is the ordinary success path: enough research, supported evidence, an authorized valuation context, and consistent rendered math.

## Complete + blocked

`rendered_math_conflict` also completes all six dimensions, so its raw utility score is `1.00`. But the displayed target, forward EPS, and multiple contradict one another. The rendered-report audit emits a blocking finding, the integrity gate fails, and effective score becomes `0.40`.

The full breadth remains visible for diagnosis, but it cannot cancel the fatal error. Delivery stays review-required.

## Shallow + clean

`shallow_but_sound` has supported evidence and no audit finding. The integrity gate passes. Yet it completes only fundamentals and industry/supply-chain work, producing utility and effective scores of `0.35`.

That draft is not mislabeled as complete research. It remains review-required for insufficient utility, with a different confidence cap from an integrity failure.

## The engineering judgment

A blended score would obscure the difference between these last two cases. One is broad but invalid; the other is valid but incomplete. Separate layers preserve both meanings and make the delivery state explainable to the analyst who owns the final judgment.
