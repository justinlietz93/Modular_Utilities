# Explain Card Review Checklist

Use this checklist whenever explain cards are generated. It captures the human-in-the-loop review notes required by Phase 2 Task 9.

1. **Open the run directory** – locate `cards/index.json` and the Markdown/metadata pairs for each card.
2. **Read the Markdown** – verify sections `Summary`, `Rationale`, `Edge Cases`, and `Traceability` exist and are accurate.
3. **Validate cross-links** – ensure the listed graph nodes, bundles, and metrics entries reference the expected artifacts.
4. **Update metadata** – edit the corresponding JSON file:
   - Set `status` to `approved` or `needs_revision`.
   - Update `requires_review` if additional follow-up is necessary.
   - Append an entry to `review_history` including your name/handle, timestamp, and decision notes.
5. **Commit outcomes** – store the updated metadata alongside any Markdown edits so the manifest captures provenance for future runs.

Signed-off cards should always include a fresh `review_history` entry demonstrating manual approval.
