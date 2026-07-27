# Jira Story Template

Use this template (or the equivalent JSON shape in samples/jira_story.json) as the input contract for the documentation sync pipeline.

## Fields

- key: Jira issue key, e.g. PROJ-123
- title: Short story title
- description: As a <role>, I want <capability>, so that <benefit>
- acceptance_criteria: Ordered list of Given/When/Then or bullet criteria
- labels: Optional list of labels used to infer non-functional requirements (e.g. performance, security)
- link: Optional URL back to the Jira issue

## Example (Markdown form)

Key: PROJ-123
Title: Allow users to export their report as PDF
Description: As a registered user, I want to export my report as a PDF, so that I can share it offline.
Acceptance Criteria:
- Given a generated report, when the user clicks Export, then a PDF download starts within 3 seconds.
- Given an export failure, when it occurs, then the user sees an actionable error message.
Labels: performance, usability
