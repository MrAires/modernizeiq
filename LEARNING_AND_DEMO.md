# ModernizeIQ — learn it, demonstrate it, explain it

## Why this project exists

Teams considering modernization first need a defensible view of the current application: languages, dependencies, configuration, state, delivery practices, and risks. Manual inspection can be repetitive, and recommendations can lose their connection to source evidence. This project turns selected static indicators into a reviewable assessment and phased action plan.

That is a rationale you can adopt **if it matches your motivation**. Do not invent an employer incident or claim you personally built components you have not studied.

## Walk through the complete workflow

1. **Explore:** open the demo and describe the input. Why: a known example makes the analysis boundary visible.
2. **Inspect:** click a finding and trace it to observations or file evidence. Why: a recommendation should be explainable.
3. **Decide:** record “Investigate” with a specific rationale. Why: an automated indicator still needs human judgment.
4. **Change:** perform the exercise in START_HERE.md. Write the expected effect before running it.
5. **Compare:** choose the original and changed snapshots. Why: controls and settings matter when attributing differences.
6. **Communicate:** open the printable report and export JSON. Why: another person should be able to inspect the claim and its parameters.

## Hands-on contribution checklist

Keep a short experiment log containing:

- The problem and your hypothesis.
- The exact input/configuration/code change you made.
- Before/after results and the test you added.
- A case where the rule should not fire.
- What the result does not prove.

For a visual contribution, change the accent tokens in workspace_ui/styles.css, adjust a heading scale, and edit workspace_ui/logo.svg. Explain contrast, hierarchy, and usability rather than only saying “I changed the colour.”

For an engineering contribution, add support for a dependency manifest format or a carefully scoped source pattern, with positive and negative fixtures. Inspect backend/app/analyzers and backend/app/scoring before changing a rule.

## A truthful résumé template

After doing and verifying your own work, adapt this statement:

> Developed and extended a local application modernization assessment workspace using Python, FastAPI, and SQLite, with repository ingestion, evidence-linked findings, transparent scoring, snapshot comparison, human review, and report exports.

Only keep “developed and extended” when you can explain and demonstrate your contribution. Mention AI assistance when asked. Add measured accuracy, timing, or user impact only after you collect that evidence; passing unit tests is not a percentage improvement in business outcomes.

For an Accenture referral application, this can demonstrate API development, data validation, persistence, testing, application assessment and cloud-modernization reasoning, and clear technical communication. It does not guarantee a referral or selection. Connect your demonstration to the actual role's requirements.

## Interview questions you should be able to answer

1. What user problem does this solve?
2. What is accepted as input, and what gets rejected?
3. Which parts are deterministic, and which require a person?
4. How do you prevent demo data from being confused with real imports?
5. Why can changed settings make a comparison misleading?
6. What did you change yourself, and how did you test it?
7. What would need to change before exposing this on the public internet?

## Design rationale

The ivory/plum palette and serif headings communicate assessment and editorial hierarchy. Horizontal navigation differentiates it from an operations console. Squared panels, dimension bars, architecture nodes, and phased cards organize structural decisions.

The SVG logos are editable source assets, not remote image dependencies. No externally hosted fonts or scripts are needed for the workspace interface.
