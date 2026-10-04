# Demo plan (5 minutes, draft v1)

## Setup on stage
- Android phone running the installed APK, mirrored to the laptop with `scrcpy` over USB, laptop on the projector.
- Phone on mobile data or hotspot, not venue Wi-Fi.
- Already logged out, on the login screen. Demo login typed once beforehand so autofill works.
- Laptop second window: one architecture slide.
- Backup: recorded screen video of the same flow, open and paused.

## Script
| Time | What | Say |
|---|---|---|
| 0:00 | Problem | "Most families don't know how much life insurance they need. Calculators feel like a math test, and the answer is a scary number with no explanation." |
| 0:30 | Log in, start chat | "Meet Maria. 34, two kids, a mortgage." |
| 0:45 | 5 chat turns (below) | "One question at a time, plain language. She can say 'not sure'." |
| 2:15 | Results appear | "Here is her number, and here is exactly why: each part with its reason." |
| 2:45 | Move the income-years slider | "She can explore. Every number comes from tested code, not from the AI." |
| 3:15 | Term vs permanent card | "Her need drops once the kids finish school and the mortgage shrinks, around year 19. That is why a 20-year term fits her situation." |
| 3:45 | Architecture slide | "One Bedrock agent. It talks; MCP tools calculate; it explains. JWT, argon2, encrypted token storage, no SSN or health data, guardrails on input and output, and a fallback if the model is down." |
| 4:30 | Close | "Next: advisor handoff, Bedrock AgentCore, Lincoln's real products. Built spec-first: contract, calculator spec, task list." |

## Maria's lines (fixed, rehearsed)
1. "I'm 34 and I have two kids, 3 and 6."
2. "I make about 85 thousand a year."
3. "We owe 240k on the house with 25 years left, and about 15k on a car."
4. "Yes, I'd like to cover college. We have around 30k saved."
5. "I have 50k through work."
Expected: total 1,633,900, gap 1,553,900, suggested term 20 years.

## If something fails
- Model slow or down: fallback flow runs automatically; keep talking.
- Network down: switch to the backup video and narrate it.
- Never debug on stage.

## Likely judge questions
- "How do you know the numbers are right?" Deterministic calculator, unit tests, sources shown in the app.
- "What stops the AI giving advice?" System rules, output check on dollar amounts, optional Bedrock Guardrail, disclaimer.
- "Why MCP?" The calculator is a reusable tool any agent can call; the same server works in our dev tools.
- "Why not multiple agents?" One agent is faster and easier to audit; complexity only where it earns its place.
- "What data do you store?" Email, password hash, the profile the user typed. No SSN, no health data.
