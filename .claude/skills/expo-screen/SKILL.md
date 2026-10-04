---
name: expo-screen
description: Add or change a screen, component, API call or auth flow in the Expo React Native app in front-end/. Use for any mobile UI work. The user knows React web but is new to React Native, so explain RN-specific choices briefly.
---

# Expo screen

## Layout (already built; extend, do not restructure)
```
front-end/                 Expo SDK 57, expo-router, TypeScript strict, React Compiler on
  AGENTS.md                Expo's own guidance: read it; check versioned docs before using an unfamiliar Expo API
  app.json                 app name, `extra.apiUrl` (backend address)
  src/app/_layout.tsx      Stack + auth gate with `Stack.Protected` (signed in: index, results, history; signed out: login)
  src/app/login.tsx        sign in / create account / demo account
  src/app/index.tsx        chat
  src/app/results.tsx      goal, breakdown, what-if, timeline, term vs permanent, sources, disclaimer
  src/app/history.tsx      past assessments
  src/components/ui.tsx    Button, Card, ErrorNote, Disclaimer
  src/lib/api.ts           the only place that calls fetch; ApiError; errorMessage()
  src/lib/auth.ts          zustand: token in expo-secure-store, login/register/logout/restore
  src/lib/conversation.ts  zustand: current conversation, assessment, what-if preview
  src/lib/types.ts         API shapes, mirror of docs/api.md
  src/lib/theme.ts         colors, space, font, formatUSD
```
`example/` is the template's sample code. Ignore it; it is excluded from type-checking.

## Rules
1. All network calls go through `api<T>(path, {body})` in `lib/api.ts`. Screens never call `fetch`.
2. Backend address: `EXPO_PUBLIC_API_URL`, else `extra.apiUrl` in `app.json`. Never `localhost`. HTTPS for the APK.
3. Token lives in `expo-secure-store` only. Never AsyncStorage, never logged.
4. Every screen handles loading, error (friendly message + retry) and empty states.
5. Styles: `StyleSheet.create` with values from `lib/theme.ts`. No inline hex colors, no UI kit, no icon packages.
6. All text inside `<Text>`. Touch targets at least 44pt with `accessibilityLabel`.
7. Money is formatted only with `formatUSD`. Amounts come from the API `assessment` JSON, never from chat text,
   and are never calculated in the app (what-if calls `POST /calculator/assess`).
8. Results screen always ends with `Disclaimer`.
9. Do not call setState synchronously inside `useEffect` (lint error under the React Compiler); set state in the
   async callback instead.
10. Only add packages that work in Expo Go, with `npx expo install <pkg>`. Native-only modules need a dev build; avoid them.

## Theme (ours, inspired by the host brand; no Lincoln logo or assets)
`primary #7A1F3D` (maroon), `accent #F2622E` (orange), `bg #FAF7F5`, `card #FFFFFF`, `text #1F2933`, `muted #6B7280`,
`success #1F7A6B`. Spacing scale 4/8/12/16/24. Radius 12. Body text 16, never below 14.

## Tone in UI copy
Calm and plain. "Here is what would help your family stay on track" rather than "You are underinsured".
Show the gap as a goal with progress (existing coverage vs need), not as a deficit in red.

## React web to React Native cheatsheet
`div` is `View`, `p/span` is `Text`, `input` is `TextInput`, `onClick` is `onPress`, CSS is `StyleSheet` (flex column by default),
react-router is expo-router (file = route), `localStorage` is `expo-secure-store`, lists are `FlatList`.

## Commands (from front-end/)
`npx expo start --tunnel` (scan the QR code with Expo Go), `npx tsc --noEmit`, `npx expo lint`,
`npx eas-cli@latest build -p android --profile preview` (APK).

## Done when
`npx tsc --noEmit` and `npx expo lint` are clean and the screen works on a real phone against the backend with the demo user.
