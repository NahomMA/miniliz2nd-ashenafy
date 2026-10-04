# Task list (draft v1)

One task per coding session. Finish the "done when" check before moving on. Estimates total about 8 hours.
Skill to use is in brackets.

## Phase 0: setup (30 min)
- [ ] T0.1 `git init`, first commit of docs and `.claude/`. Done when: `git status` shows no `.env`, keys or `prev_projects`.
- [x] T0.2 Bedrock test call script (loads `.env` with python-dotenv). Done when: it prints a reply and we have a working `BEDROCK_MODEL_ID` and `AWS_REGION`.
- [~] T0.3 (code written, needs phone test) `npx create-expo-app front-end`, run on the phone with Expo Go. Done when: the default screen shows on the phone.
- [ ] T0.4 Start an EAS preview APK build of the empty app in the background. Done when: the APK installs on an Android device. (Removes the biggest unknown early.)
- [x] T0.5 Verify the two assumption values and record sources. Done 2026-10-03, see calculator-spec.md.

## Phase 1: backend core (2.5 h)
- [x] T1.1 [mcp-calculator] `calculator.py` + tests from the Maria table. Done when: `pytest` passes.
- [x] T1.2 [mcp-calculator] `server.py` with 4 tools and 3 resources, plus `.mcp.json`. Done when: the server starts and lists 4 tools.
- [x] T1.3 [flask-endpoint] App factory, models, errors, auth routes, seed demo user. Done when: login by curl returns a token; auth tests pass.
- [x] T1.4 [mcp-calculator] `mcp_client.py` bridge with direct-call fallback. Done when: a test calls a tool through MCP and through the fallback with equal results.
- [x] T1.5 [bedrock-chat] Converse loop, system prompt, `/assessments` and `/chat`. Done when: a curl conversation as Maria returns `total_need` 1,633,900.
- [x] T1.6 [bedrock-chat] Input and output guardrails, scripted fallback. Done when: a wrong model ID still completes the flow; an SSN in a message is redacted.
- [x] T1.7 [flask-endpoint] `/what-if`, history endpoints. Done when: tests pass and `docs/api.md` matches.

## Phase 2: mobile (2.5 h)
- [~] T2.1 (code written, needs phone test) [expo-screen] Theme, `lib/api.ts`, auth store, login screen, auth gate. Done when: demo user logs in on the phone and stays logged in after restart.
- [~] T2.2 (code written, needs phone test) [expo-screen] Chat screen. Done when: the full Maria conversation works on the phone with the keyboard not covering the input.
- [~] T2.3 (code written, needs phone test) [expo-screen] Results screen: total, progress toward goal, breakdown rows with reasons, disclaimer. Done when: numbers match the API JSON.

## Phase 3: polish (1 h)
- [~] T3.1 (code written, needs phone test) [expo-screen] What-if sliders. Done when: moving a slider updates totals within a second.
- [~] T3.2 (code written, needs phone test) [expo-screen] Term vs permanent card and "how we calculated this" (assumptions with sources). Done when: Maria sees a 20-year suggestion with the reason.
- [~] T3.3 (code written, needs phone test) [expo-screen] History tab. Cut first if behind.

## Phase 4: ship (1.5 h)
- [ ] T4.1 Dockerfile, HTTPS hosting (tunnel first; AWS Lightsail if time). Done when: `/health` answers over HTTPS from mobile data.
- [ ] T4.2 Final EAS APK pointed at the HTTPS URL. Done when: installed APK completes the Maria flow.
- [ ] T4.3 README: description, architecture diagram, security section, demo login, licensing note. Done when: a stranger could run it.
- [ ] T4.4 Record a backup screen video of the full flow.
- [ ] T4.5 Rehearse `docs/demo.md` twice under 5:00.

## Cut order if behind
T3.3, then T3.1, then AWS deploy (stay on tunnel), then T1.7 history endpoints. Never cut T1.6 fallback or T4.4 backup video.
