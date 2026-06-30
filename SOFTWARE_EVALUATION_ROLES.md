# Software Evaluation Roles

Use this checklist to evaluate IDphotoApp from the complete set of roles that would normally review software inside a company.

## Product Manager
- Is the workflow clear?
- Does it solve the actual user goal: compliant ID photo creation?
- Are defaults sensible for non-technical users?
- Are edge cases surfaced clearly?

## UX / UI Designer
- Is manual fine-tuning understandable?
- Are guides visually meaningful?
- Are controls ergonomic?
- Is the interface too cluttered or confusing?

## Computer Vision Engineer
- Are face detection, crop ratios, background removal, and masking technically sound?
- Are guide lines based on actual detected features?
- Are failure modes handled?

## Backend / CLI Engineer
- Is the processing pipeline clean and reusable?
- Do GUI and CLI share the same logic?
- Are file paths, specs, and output generation robust?

## QA Engineer
- What should be tested?
- Which regressions are likely?
- Are there test images for lighting, shadows, skin tones, hair, glasses, and different backgrounds?

## Compliance / ID Photo Requirements Reviewer
- Are head size, eye line, background, photo dimensions, and DPI aligned with country requirements?
- Are guide defaults based on spec data rather than guesses?

## DevOps / Release Engineer
- Are dependencies too heavy?
- Does install/run work reliably on Windows?
- Are model downloads documented?
- Is app startup acceptable?

## Security / Privacy Reviewer
- Are photos processed locally?
- Are any models or APIs uploading user photos?
- Are downloaded models from trusted sources?
- Are temp files handled safely?

## Performance Engineer
- Is BiRefNet too slow for normal use?
- Should there be model selection: best quality vs faster?
- Are large images resized efficiently?

## Documentation / Support
- Are setup steps correct?
- Are defaults explained?
- Are known limitations documented?
- Can a user recover when face detection or background removal fails?

## Review Format

Use this structure for design and implementation reviews:

```text
Role:
Finding:
Risk:
Recommended fix:
Priority:
```
