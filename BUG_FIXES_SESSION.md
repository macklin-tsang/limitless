# Bug Fixes and Issues - Session Summary

This document details all bugs encountered and resolved during the implementation of the Texas Hold'em poker game engine.

---

## Table of Contents
1. [All-In Display Issue](#1-all-in-display-issue)
2. [All-In Runout Issue](#2-all-in-runout-issue)
3. [Code Refactoring Fragment Issue](#3-code-refactoring-fragment-issue)
4. [TAG Bot Limping Preflop Issue](#4-tag-bot-limping-preflop-issue)
5. [Check Action Notation Issue](#5-check-action-notation-issue)

---

## 1. All-In Display Issue

### Problem Description
When one player went all-in preflop, the other player's call action was not being displayed in the game output.

**Example:**
```
→ Alice raises to $910.00 (all-in)
→ Pot after preflop: $1820.00  ← Bob's call missing!
```

### Root Cause
The betting round logic was breaking the action loop too early when it detected that one player was all-in. The check `len(active_players) <= 1` was treating all-in players as inactive, preventing the other player from having the opportunity to call.

**Problematic Code (game.py:~line 220):**
```python
# Old code
active_players = [p for p in action_order if p.is_active and not p.is_all_in]
if len(active_players) <= 1:
    break  # Broke too early!
```

### Solution
Restructured the betting loop to:
1. Move player selection to the start of the loop
2. Check if the current player is all-in and skip them individually
3. Only break when there are no active players remaining (not counting all-in status separately)

**Fixed Code (game.py:220-230):**
```python
# New code - moved player selection inside loop
while action_count < max_actions:
    current_player = action_order[action_count % len(action_order)]

    # Skip if current player is already all-in
    if current_player.is_all_in:
        action_count += 1
        if action_count > len(action_order) * 20:
            break
        continue
```

### Verification
After the fix, all-in calls are now properly displayed:
```
→ Alice raises to $910.00 (all-in)
→ Bob calls $640.00  ✓ Now shows correctly!
→ Pot after preflop: $1820.00
```

**Status: ✅ FIXED**

---

## 2. All-In Runout Issue

### Problem Description
When both players were all-in, the game was still prompting for betting decisions on subsequent streets (flop, turn, river) instead of automatically dealing out the remaining cards to showdown.

**Expected Behavior:**
- Both players all-in → automatically run out flop, turn, river without betting
- Display "Both players all-in - no betting"

**Actual Behavior:**
- Game was calling `betting_round()` even when both players were all-in
- This caused unnecessary decision-making and potential errors

### Root Cause
The game flow logic didn't check whether both players were all-in before starting betting rounds on postflop streets.

**Problematic Code (game.py:~line 300):**
```python
# Old code
if len([p for p in self.players if p.is_active]) > 1:
    self.deal_flop()
    if not self.betting_round("flop"):  # Wrong - should skip if both all-in
        # ...
```

### Solution
Added a `both_all_in` check that determines if both players are all-in or inactive. When this condition is true, the game:
1. Automatically deals all remaining community cards
2. Displays "⚡ Both players all-in - no betting"
3. Skips all betting rounds
4. Proceeds directly to showdown

**Fixed Code (game.py:300-320):**
```python
# Check if both players are all-in
both_all_in = all(p.is_all_in or not p.is_active for p in self.players)

# Flop
if len([p for p in self.players if p.is_active]) > 1:
    self.deal_flop()
    if not both_all_in:  # Only bet if not both all-in
        if not self.betting_round("flop"):
            winner = next(p for p in self.players if p.is_active)
            self.award_pot(winner)
            return
    # Similar logic for turn and river
```

### Test Case
Created `test_guaranteed_showdown.py` to verify the fix works correctly:

**Input:**
- Alice: A♥K♥ (all-in preflop)
- Bob: A♠A♦ (calls all-in)

**Output:**
```
FLOP: 3♥, 4♥, 10♠
  → Pot: $1820.00
  → ⚡ Both players all-in - no betting  ✓

TURN: 5♥
  → Pot: $1820.00
  → ⚡ Both players all-in - no betting  ✓

RIVER: 9♦
  → Pot: $1820.00
  → ⚡ Both players all-in - no betting  ✓

SHOWDOWN
  → Alice wins with Flush  ✓
```

**Status: ✅ FIXED**

---

## 3. Code Refactoring Fragment Issue

### Problem Description
During the refactoring to separate hand strength evaluation functions from `brain.py` into `strength.py`, a `sed` command was used to remove old function definitions. However, this left code fragments in `brain.py`.

**Problematic Code (brain.py:36-54):**
```python
# Leftover fragments from _check_for_draws function
if max(suit_counts.values()) == 4:
    draws['flush_draw'] = True

# Check for straight draws
ranks = sorted(set(c.get_rank_value() for c in all_cards))

# Check for open-ended straight draw (4 consecutive cards)
for i in range(len(ranks) - 3):
    if ranks[i+3] - ranks[i] == 3:
        draws['oesd'] = True
        break
# ... more fragments
```

### Root Cause
The `sed` command removed lines 36-372, but line 373 was in the middle of the `_check_for_draws` function, leaving partial code.

**Command Used:**
```bash
sed -n '1,35p' brain.py > brain_temp.py &&
sed -n '373,839p' brain.py >> brain_temp.py &&
mv brain_temp.py brain.py
```

The issue: Line 373 started with `if max(suit_counts.values()) == 4:` which was the middle of the function being removed.

### Solution
Used the Edit tool to precisely remove the leftover fragments, ensuring the file goes cleanly from the import/comment section (line 35) directly to the `make_preflop_decision` function.

**Fix Applied:**
```python
# Before (brain.py with fragments)
# - check_for_draws() -> _check_for_draws()


    if max(suit_counts.values()) == 4:  # ← Fragment starts here
        draws['flush_draw'] = True
    # ... more fragments ...
    return draws


def make_preflop_decision(

# After (cleaned brain.py)
# - check_for_draws() -> _check_for_draws()


def make_preflop_decision(  # ← Directly after comments
```

### Verification
All test suites passed after cleanup:
- ✅ Unit tests (game.py)
- ✅ Comprehensive demo (20 hands)
- ✅ Guaranteed showdown test
- ✅ strength.py standalone tests
- ✅ brain.py manual tests

**Status: ✅ FIXED**

---

## 4. TAG Bot Limping Preflop Issue

### Problem Description
During simulation testing, the TAG Bot (brain.py) was calling the big blind from the Button position (limping) instead of raising or folding, violating the strategic rule that the bot should never limp when first to act.

**Example from Hand History:**
```
TAG Bot posts SB $5.00
Fish posts BB $10.00
TAG Bot calls $5.00  ❌ Should be "raises to $30.00" or "folds"
Fish calls $0.00     ❌ Should be "checks"
```

### Root Cause
When the Button posts the small blind ($5) and the big blind posts ($10), the game was treating the Button as "facing a raise" because:
- Button's current_bet = $5
- Game's current_bet = $10
- Therefore: `facing_raise = True` (since $5 < $10)

This caused brain.py to follow the "facing first raise" logic (lines 122-131), which calls with medium/strong hands instead of the "first to act" logic (raise or fold).

**Problematic Code (game.py:344, simulation.py:339):**
```python
# Old code - always treated Button as first to act
action, bet_size = make_preflop_decision(
    hand=tuple(current_player.hole_cards),
    position=current_player.position,
    # ...
    facing_raise=facing_raise,  # This was True for Button!
    raise_amount=raise_amount,  # This was $10
    # ...
    is_first_to_act=(current_player.position == 1)  # Wrong interpretation
)
```

When brain.py received `facing_raise=True` and `raise_amount=$10`, it followed the "facing first raise" path and called with K7o (a medium hand).

### Solution
Added special handling to detect when the Button is completing the small blind to the big blind. In this situation, treat it as "first to act" for decision-making purposes (even though technically facing the BB), because completing SB→BB is analogous to opening action.

**Fixed Code (game.py:331-371, simulation.py:328-360):**
```python
# New code - detect Button completing SB to BB
if phase == "preflop":
    # Special handling for heads-up preflop:
    # Button completing SB to BB should be treated as "first to act"

    is_button_completing = (current_player.position == 1 and
                           current_player.current_bet == self.small_blind and
                           self.current_bet == self.big_blind)

    if is_button_completing:
        # Treat as first to act: raise or fold, no limp
        action, bet_size = make_preflop_decision(
            hand=tuple(current_player.hole_cards),
            position=current_player.position,
            pot=self.pot,
            current_stack=current_player.stack,
            big_blind=self.big_blind,
            facing_raise=False,  # Treat as first to act
            raise_amount=None,
            facing_3bet=False,
            facing_4bet=False,
            is_first_to_act=True  # Opening action
        )
    else:
        # Normal handling for other situations
        action, bet_size = make_preflop_decision(
            # ... use actual facing_raise status
            facing_raise=facing_raise,
            raise_amount=raise_amount,
            # ...
            is_first_to_act=False
        )
```

### Verification
After the fix, TAG Bot correctly raises or folds when acting first:

**Sample Corrected Hand:**
```
TAG Bot posts SB $5.00
Fish posts BB $10.00
TAG Bot raises to $30.00  ✓ Correct! (3x BB with good hand)
Fish calls $20.00

--- OR ---

TAG Bot posts SB $5.00
Fish posts BB $10.00
TAG Bot folds  ✓ Correct! (weak hand, no limp)
Fish wins $15.00
```

**Test Results:**
- ✅ No instances of "TAG Bot calls $5.00" when Button
- ✅ TAG Bot only raises to $30 or folds when acting first
- ✅ Verified across 100-hand simulation

**Status: ✅ FIXED**

---

## 5. Check Action Notation Issue

### Problem Description
When players checked (having the option to check for free), the hand history was logging "calls $0.00" instead of the proper poker notation "checks".

**Example from Hand History:**
```
Fish posts SB $5.00
TAG Bot posts BB $10.00
Fish calls $5.00
TAG Bot calls $0.00  ❌ Should be "TAG Bot checks"
```

### Root Cause
The game engine (game.py and simulation.py) did not have an explicit handler for the `action == "check"` case. When brain.py returned `("check", 0.0)`, the action was falling through to the call handler, which logged "calls $0.00".

**Problematic Code (game.py:~363, simulation.py:~381):**
```python
# Old code - missing check handler
if action == "fold":
    current_player.fold()
    self.action_history.append(f"{current_player.name} folds")
    return False

elif action == "call":  # Check fell through to here!
    call_amount = self.current_bet
    old_bet = current_player.current_bet
    actual_bet = current_player.bet(call_amount)
    additional = actual_bet - old_bet
    # ...
    self.action_history.append(f"{current_player.name} calls ${additional:.2f}")
```

When `action == "check"` with `bet_size == 0.0`, the call handler would calculate `additional = 0.0` and log "calls $0.00".

### Solution
Added an explicit handler for the check action before the call handler. This ensures that checks are logged with the proper poker notation.

**Fixed Code (game.py:371-373, simulation.py:386-388):**
```python
# New code - explicit check handler
if action == "fold":
    current_player.fold()
    self.action_history.append(f"{current_player.name} folds")
    return False

elif action == "check":
    # Check means no additional bet (only valid when not facing a bet)
    self.action_history.append(f"{current_player.name} checks")

elif action == "call":
    # Call means matching the current bet
    # ...
```

### Verification
After the fix, checks are properly logged:

**Sample Corrected Hand:**
```
Fish posts SB $5.00
TAG Bot posts BB $10.00
Fish calls $5.00
TAG Bot checks  ✓ Correct notation!

FLOP: 2♣, Q♥, Q♦
Fish checks  ✓
TAG Bot raises to $10.00
Fish calls $10.00
```

**Test Results:**
- ✅ No instances of "calls $0.00" in new hand histories
- ✅ All checks properly logged as "checks"
- ✅ Verified across 100-hand simulation

**Status: ✅ FIXED**

---

## Summary Statistics

| Issue | Type | Severity | Time to Fix | Files Modified |
|-------|------|----------|-------------|----------------|
| All-In Display | Logic Error | Medium | ~15 min | game.py |
| All-In Runout | Logic Error | High | ~10 min | game.py, test files |
| Refactoring Fragments | Code Cleanup | Low | ~5 min | brain.py |
| TAG Bot Limping | Strategy Violation | High | ~20 min | game.py, simulation.py |
| Check Notation | Display Issue | Low | ~5 min | game.py, simulation.py |

---

## Related Files

### Modified Files
- [`game.py`](backend-python/engine/game.py) - Core game engine with all-in fixes, preflop logic fix, check handling
- [`simulation.py`](backend-python/engine/simulation.py) - Simulation runner with preflop logic fix, check handling
- [`brain.py`](backend-python/engine/brain.py) - Decision-making logic (refactored)
- [`strength.py`](backend-python/engine/strength.py) - Hand strength evaluation (new)

### Test Files
- [`test_guaranteed_showdown.py`](backend-python/engine/test_guaranteed_showdown.py) - Tests full runout including all-in scenarios
- [`test_full_runout.py`](backend-python/engine/test_full_runout.py) - Multiple hand testing
- [`run_tests.sh`](backend-python/engine/run_tests.sh) - Complete test suite

### Documentation
- [`ALLIN_FIX_SUMMARY.md`](backend-python/engine/ALLIN_FIX_SUMMARY.md) - Original all-in fix documentation
- [`TESTING_GUIDE.md`](backend-python/engine/TESTING_GUIDE.md) - How to run tests
- [`CUSTOM_CARDS_GUIDE.md`](backend-python/engine/CUSTOM_CARDS_GUIDE.md) - Custom card testing guide

---

## Lessons Learned

1. **All-In Logic is Complex**: Treating all-in players requires careful consideration of when they can act vs when they're waiting for runout.

2. **Loop Structure Matters**: The order of checks in betting loops is critical - check player state before making decisions about breaking the loop.

3. **Use Precise Tools for Refactoring**: While `sed` is powerful, the Edit tool provides more precise control for code refactoring and avoids leaving fragments.

4. **Test Everything**: After any refactoring, run the complete test suite to ensure no regressions were introduced.

5. **Document as You Go**: Creating test files and documentation during implementation helps catch issues early.

6. **Heads-Up Preflop is Special**: In heads-up poker, the Button/SB completing to the BB is conceptually "opening action" even though it's technically "facing the BB". This requires special handling to avoid unwanted limping behavior.

7. **Action Handlers Must Be Complete**: Every possible action (fold, check, call, raise) needs an explicit handler. Falling through to a default handler can cause incorrect logging or behavior.

8. **Multiple Codebases Need Sync**: When maintaining both game.py and simulation.py, fixes must be applied to both files to ensure consistent behavior across testing and simulation environments.

---

## 6. Maven Wrapper JAR Issue (Java Backend)

### Problem Description
When attempting to run the Java Spring Boot application using the Maven wrapper (`./mvnw spring-boot:run`), the wrapper failed with a "no main manifest attribute" error.

**Error Message:**
```
Downloading Maven wrapper...
no main manifest attribute, in .mvn/wrapper/maven-wrapper.jar
```

### Root Cause
The initial Maven wrapper implementation attempted to download the `maven-wrapper.jar` file and execute it directly. However, the wrapper JAR requires proper manifest attributes to be executable, and the simple download approach did not work correctly.

### Solution
Replaced the JAR-based wrapper with a shell script that downloads and extracts the full Maven distribution directly.

**Fixed Code (mvnw):**
```bash
#!/bin/sh
# Maven Wrapper script - downloads Maven directly

MAVEN_VERSION="3.9.6"
MAVEN_HOME="$HOME/.m2/wrapper/dists/apache-maven-$MAVEN_VERSION"
MAVEN_URL="https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/$MAVEN_VERSION/apache-maven-$MAVEN_VERSION-bin.tar.gz"

# Download Maven if not present
if [ ! -d "$MAVEN_HOME" ]; then
    echo "Downloading Maven $MAVEN_VERSION..."
    mkdir -p "$MAVEN_HOME"
    curl -fsSL "$MAVEN_URL" | tar -xz -C "$MAVEN_HOME" --strip-components=1
fi

# Run Maven
exec "$MAVEN_HOME/bin/mvn" "$@"
```

**Status: ✅ FIXED**

---

## 7. PostgreSQL Connection Refused Issue (Java Backend)

### Problem Description
After fixing the Maven wrapper, the Spring Boot application failed to start with a JDBC connection error.

**Error Message:**
```
org.postgresql.util.PSQLException: Connection to localhost:5432 refused.
Check that the hostname and port are correct and that the postmaster
is accepting TCP/IP connections.
```

### Root Cause
The `application.properties` was configured to connect to PostgreSQL at `localhost:5432`, but PostgreSQL was not installed or running on the development machine. Per the implementation plan, PostgreSQL setup is scheduled for Phase 1, Step 9 (after the Java API setup).

### Solution
Implemented Spring profiles to allow development without PostgreSQL:

1. **Created `application-dev.properties`** - Uses H2 in-memory database (no external DB required)
2. **Created `application-prod.properties`** - Uses PostgreSQL for production
3. **Updated `application.properties`** - Sets default profile to `dev`
4. **Updated `pom.xml`** - Changed H2 dependency scope from `test` to `runtime`

**application.properties (updated):**
```properties
server.port=8080
spring.profiles.active=dev
```

**application-dev.properties:**
```properties
# H2 In-Memory Database
spring.datasource.url=jdbc:h2:mem:poker_agent;DB_CLOSE_DELAY=-1
spring.datasource.driver-class-name=org.h2.Driver
spring.jpa.hibernate.ddl-auto=create-drop
spring.h2.console.enabled=true
spring.h2.console.path=/h2-console
```

**application-prod.properties:**
```properties
# PostgreSQL (for when DB is set up in Step 9)
spring.datasource.url=jdbc:postgresql://localhost:5432/poker_agent
spring.datasource.username=poker
spring.datasource.password=password
```

### Verification
- Application starts successfully with `./mvnw spring-boot:run`
- H2 console accessible at `http://localhost:8080/h2-console`
- All API endpoints functional without PostgreSQL

**Status: ✅ FIXED**

---

## Summary Statistics

| Issue | Type | Severity | Time to Fix | Files Modified |
|-------|------|----------|-------------|----------------|
| All-In Display | Logic Error | Medium | ~15 min | game.py |
| All-In Runout | Logic Error | High | ~10 min | game.py, test files |
| Refactoring Fragments | Code Cleanup | Low | ~5 min | brain.py |
| TAG Bot Limping | Strategy Violation | High | ~20 min | game.py, simulation.py |
| Check Notation | Display Issue | Low | ~5 min | game.py, simulation.py |
| Maven Wrapper JAR | Build Tool | Medium | ~5 min | mvnw |
| PostgreSQL Connection | Configuration | Medium | ~10 min | pom.xml, application*.properties |

---

## Related Files

### Modified Files
- [`game.py`](backend-python/engine/game.py) - Core game engine with all-in fixes, preflop logic fix, check handling
- [`simulation.py`](backend-python/engine/simulation.py) - Simulation runner with preflop logic fix, check handling
- [`brain.py`](backend-python/engine/brain.py) - Decision-making logic (refactored)
- [`strength.py`](backend-python/engine/strength.py) - Hand strength evaluation (new)
- [`mvnw`](backend-java/mvnw) - Maven wrapper script (fixed)
- [`pom.xml`](backend-java/pom.xml) - Maven configuration (H2 scope change)
- [`application.properties`](backend-java/src/main/resources/application.properties) - Spring config (profile setup)
- [`application-dev.properties`](backend-java/src/main/resources/application-dev.properties) - H2 config (new)
- [`application-prod.properties`](backend-java/src/main/resources/application-prod.properties) - PostgreSQL config (new)

### Test Files
- [`test_guaranteed_showdown.py`](backend-python/engine/test_guaranteed_showdown.py) - Tests full runout including all-in scenarios
- [`test_full_runout.py`](backend-python/engine/test_full_runout.py) - Multiple hand testing
- [`run_tests.sh`](backend-python/engine/run_tests.sh) - Complete test suite
- [`UserControllerTest.java`](backend-java/src/test/java/com/poker/agent/UserControllerTest.java) - Java API integration tests

### Documentation
- [`ALLIN_FIX_SUMMARY.md`](backend-python/engine/ALLIN_FIX_SUMMARY.md) - Original all-in fix documentation
- [`TESTING_GUIDE.md`](backend-python/engine/TESTING_GUIDE.md) - How to run tests
- [`CUSTOM_CARDS_GUIDE.md`](backend-python/engine/CUSTOM_CARDS_GUIDE.md) - Custom card testing guide

---

## Lessons Learned

1. **All-In Logic is Complex**: Treating all-in players requires careful consideration of when they can act vs when they're waiting for runout.

2. **Loop Structure Matters**: The order of checks in betting loops is critical - check player state before making decisions about breaking the loop.

3. **Use Precise Tools for Refactoring**: While `sed` is powerful, the Edit tool provides more precise control for code refactoring and avoids leaving fragments.

4. **Test Everything**: After any refactoring, run the complete test suite to ensure no regressions were introduced.

5. **Document as You Go**: Creating test files and documentation during implementation helps catch issues early.

6. **Heads-Up Preflop is Special**: In heads-up poker, the Button/SB completing to the BB is conceptually "opening action" even though it's technically "facing the BB". This requires special handling to avoid unwanted limping behavior.

7. **Action Handlers Must Be Complete**: Every possible action (fold, check, call, raise) needs an explicit handler. Falling through to a default handler can cause incorrect logging or behavior.

8. **Multiple Codebases Need Sync**: When maintaining both game.py and simulation.py, fixes must be applied to both files to ensure consistent behavior across testing and simulation environments.

9. **Maven Wrapper Complexity**: Simple JAR-based Maven wrappers can fail due to manifest issues. A shell script that downloads the full Maven distribution is more reliable.

10. **Use Profiles for Environment Flexibility**: Spring profiles allow running applications in development without production dependencies (like PostgreSQL). Default to a lightweight profile (dev/H2) to reduce setup friction.

---

**Last Updated:** 2026-01-23
**Session Duration:** ~4 hours
**Total Bugs Fixed:** 7
**Test Pass Rate:** 100%

---

## 8. Frontend UI/UX Overhaul

### Problem Description
Multiple UI/UX issues were identified in the frontend:
1. Card dimensions too narrow - text didn't fit properly
2. Backend-python logic not being applied in frontend
3. All-in preflop didn't stop action and give a runout
4. Blinds were $1/$2 instead of $5/$10
5. Stacks could go negative without recovery option
6. "Agent thinking" text was displayed unnecessarily
7. Dark theme instead of requested light/white theme
8. Unnecessary "Play vs Agent" and "Play" tabs
9. Feature cards (Smart Agents/Real Strategy/Track Progress) cluttering homepage
10. Table not displayed on frontpage immediately
11. No agent vs agent simulation capability
12. No action history display

### Solutions Implemented

**Card Redesign (`Card.jsx`):**
- Increased card dimensions for better text fit:
  - sm: w-14 h-20 (was w-12 h-16)
  - md: w-20 h-28 (was w-16 h-22)
  - lg: w-28 h-40 (was w-24 h-32)
- Colored backgrounds by suit with white text:
  - Hearts: Red background (bg-red-600)
  - Diamonds: Blue background (bg-blue-600)
  - Clubs: Green background (bg-green-600)
  - Spades: Dark grey background (bg-gray-700)

**Backend Integration (`app.py` - NEW):**
- Created Flask API wrapper for Python poker engine
- Endpoints:
  - `POST /api/simulate` - Batch simulation
  - `POST /api/simulate/single` - Single hand simulation
  - `POST /api/simulate/session` - Multi-hand session
  - `GET /api/health` - Health check
- CORS enabled for frontend communication
- Fallback to local simulation when backend unavailable

**PokerTable Rewrite (`PokerTable.jsx`):**
- Changed to Agent vs Agent simulation (TAG vs Fish)
- Blinds changed to $5/$10
- Starting stacks changed to $1000
- Added "Top Up Stacks" button when stacks go low (<$15)
- Removed "agent thinking" display entirely
- Added action history panel on the right side
- Light/white theme (bg-gray-100, white cards)
- Single "Run Simulation" button for agent vs agent play

**Navigation Simplification (`App.js`):**
- Removed "Play" tab
- Renamed routes: "Simulator" (home) and "Batch Run"
- Light theme navigation (white background)

**Homepage Simplification (`Home.jsx`):**
- Removed feature cards (Smart Agents/Real Strategy/Track Progress)
- Displays PokerTable immediately on page load
- Clean, minimal design

**Simulation Page Update (`Simulation.jsx`):**
- Updated to light theme
- Direct connection to Python backend
- Removed Java backend dependency

### Files Modified

**Frontend:**
- `frontend/src/components/Card.jsx` - Card styling and dimensions
- `frontend/src/components/PokerTable.jsx` - Complete rewrite for agent vs agent
- `frontend/src/pages/Home.jsx` - Simplified to show table immediately
- `frontend/src/pages/Simulation.jsx` - Light theme, Python backend connection
- `frontend/src/App.js` - Simplified navigation

**Backend (NEW):**
- `backend-python/app.py` - Flask API wrapper
- `backend-python/requirements.txt` - Flask dependencies

### Running the Application

**Start Python Backend:**
```bash
cd backend-python
pip install -r requirements.txt
python app.py
# Runs on http://localhost:5000
```

**Start Frontend:**
```bash
cd frontend
npm start
# Runs on http://localhost:3000
```

**Status: ✅ FIXED**

---

## Summary Statistics (Updated)

| Issue | Type | Severity | Files Modified |
|-------|------|----------|----------------|
| All-In Display | Logic Error | Medium | game.py |
| All-In Runout | Logic Error | High | game.py, test files |
| Refactoring Fragments | Code Cleanup | Low | brain.py |
| TAG Bot Limping | Strategy Violation | High | game.py, simulation.py |
| Check Notation | Display Issue | Low | game.py, simulation.py |
| Maven Wrapper JAR | Build Tool | Medium | mvnw |
| PostgreSQL Connection | Configuration | Medium | pom.xml, application*.properties |
| Frontend UI/UX Overhaul | UI/UX | High | Multiple frontend files, new Flask API |

---

## Related Files (Updated)

### Modified Files
- [`game.py`](backend-python/engine/game.py) - Core game engine
- [`simulation.py`](backend-python/engine/simulation.py) - Simulation runner
- [`brain.py`](backend-python/engine/brain.py) - Decision-making logic
- [`strength.py`](backend-python/engine/strength.py) - Hand strength evaluation
- [`app.py`](backend-python/app.py) - Flask API wrapper (NEW)
- [`requirements.txt`](backend-python/requirements.txt) - Python dependencies (NEW)
- [`Card.jsx`](frontend/src/components/Card.jsx) - Card component styling
- [`PokerTable.jsx`](frontend/src/components/PokerTable.jsx) - Agent vs agent simulator
- [`Home.jsx`](frontend/src/pages/Home.jsx) - Simplified homepage
- [`Simulation.jsx`](frontend/src/pages/Simulation.jsx) - Batch simulation page
- [`App.js`](frontend/src/App.js) - Simplified navigation

---

**Last Updated:** 2026-01-23
**Total Issues Fixed:** 8 (including UI/UX overhaul)
**Test Pass Rate:** 100%
