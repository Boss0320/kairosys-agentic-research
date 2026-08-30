# Security Boundary

This local clean-room candidate accepts only synthetic material and the approved
public behavior contract. The boundary scanner is default-deny: unexpected file
types, runtime residue, symlinks, non-UTF-8 text, private paths, credentials,
and prohibited claims produce findings that require removal or review.

The scanner is a deterministic local guardrail, not a substitute for the
separate factual, attribution, legal, or publication review gates. It performs
no network activity and does not make this candidate public.
