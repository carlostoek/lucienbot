---
status: testing
phase: 14-webapp-dados-3d
source:
  - 14-01-SUMMARY.md
  - 14-02-SUMMARY.md
  - 14-03-SUMMARY.md
  - 14-04-SUMMARY.md
started: "2026-04-06T03:35:00Z"
updated: "2026-04-06T03:35:00Z"
---

## Current Test

number: 1
name: WebApp 3D Dice Rendering
expected: |
  When opening the WebApp (dice.html), two 3D dice should be visible on screen with proper dot textures (1-6). The scene has a dark background (#121212), proper lighting, and dice are positioned to roll.
awaiting: user response

## Tests

### 1. WebApp 3D Dice Rendering
expected: |
  When opening the WebApp (dice.html), two 3D dice should be visible on screen with proper dot textures (1-6). The scene has a dark background (#121212), proper lighting, and dice are positioned to roll.
result: pending

### 2. Roll Animation
expected: |
  Clicking "Lanzar Dados" button should trigger dice rolling animation with realistic physics. Dice should rotate and bounce before settling on random values 1-6.
result: pending

### 3. Result Display
expected: |
  After dice settle, the result should display as "die1 + die2 = total" (e.g., "3 + 5 = 8") with contextual message based on outcome.
result: pending

### 4. Telegram WebApp Button
expected: |
  In Telegram, clicking "🎲 Lanzar dados" in minigames menu should open the WebApp in fullscreen mode.
result: pending

### 5. WebApp Data Return
expected: |
  After rolling dice in WebApp, the result should be sent back to the bot and the WebApp should close automatically.
result: pending

### 6. Bot Result Message
expected: |
  Bot should display result message with dice values and indicate if user won or lost.
result: pending

### 7. Besitos Awarded on Win
expected: |
  When dice show both even numbers OR doubles, user should receive 1 besito with victory message in Lucien voice.
result: pending

### 8. Cooldown Enforcement
expected: |
  Attempting to roll again within 5 seconds should show a cooldown message instead of processing the roll.
result: pending

### 9. Invalid Results Rejected
expected: |
  If WebApp sends manipulated/fake dice values (outside 1-6), the bot should reject with error message.
result: pending

### 10. Configuration
expected: |
  WEBAPP_URL and WEBAPP_DEV_URL can be configured via environment variables for dev/prod deployments.
result: pending

## Summary

total: 10
passed: 0
issues: 0
pending: 10
skipped: 0

## Gaps

[none yet]
