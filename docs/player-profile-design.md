# Player Profile / Username Design

This document defines the intended account model for `Terminal_Games`. It is a design specification only; username/account code is intentionally **not implemented yet**.

## Purpose

The current persistence layer stores one local anonymous player's saves and Best Scores. The next evolution is a lightweight local player profile selected by username so several people can use the same computer without sharing progress.

The goal is **identity and progress separation**, not authentication. A local username is not a security boundary and must not be presented as one.

## User experience

The launcher should eventually begin with an active-profile step such as:

```text
=== Terminal Games ===
Player: scientifica

1. Continue as scientifica
2. Switch player
3. Create player
4. Rename player
5. Delete player
Q. Quit
```

After a profile is selected, every game uses that profile's own:

- saved game slot;
- Best Score;
- future statistics/achievements/preferences.

The game code itself should not need to know how usernames are stored. It should continue calling the shared persistence API.

## Username rules

Recommended rules:

- 1-24 visible characters;
- Unicode allowed, including Arabic and Latin names;
- leading/trailing whitespace removed;
- display spelling preserved exactly;
- a normalized case-insensitive key used internally to avoid duplicate names such as `Scientifica` and `scientifica`;
- reserved/system names rejected;
- no path construction directly from raw usernames.

A generated internal profile ID is preferable to using the username as a filename. This avoids path traversal, rename problems, Unicode normalization issues, and accidental collisions.

## Proposed storage model

The current schema reserves profile metadata but keeps one anonymous record. A future schema can migrate to a structure conceptually similar to:

```json
{
  "version": 2,
  "active_profile_id": "p_01",
  "profiles": {
    "p_01": {
      "username": "scientifica",
      "games": {
        "2048": {
          "save": {},
          "best_score": 1472
        },
        "snake": {
          "save": null,
          "best_score": 300
        }
      }
    }
  }
}
```

This is illustrative, not a fixed serialization contract.

## Migration from the current anonymous player

When username support is implemented, existing progress must not disappear. The migration should:

1. read the current schema-v1 anonymous `games` section;
2. ask the player to create/select a username;
3. create one profile;
4. copy all current saves and Best Scores into that profile;
5. write the new schema atomically;
6. preserve a backup until the migration completes successfully.

## Save slots

For the current project, one save slot per game per player is sufficient. If multiple slots are added later, they should be introduced in the shared persistence layer rather than separately in each game.

## Authentication and passwords

No password is currently needed. A username on one computer only identifies whose local progress is being used.

If the project later introduces network synchronization, leaderboards, cloud saves, or remote accounts, authentication becomes a separate security feature and should be designed independently. Local usernames must not be retroactively described as secure accounts.

## Privacy

Player profiles should remain local by default. The project should not upload usernames, saves, scores, or gameplay statistics unless a future network feature is explicitly introduced and documented.

## Architectural rule

Games must depend on the persistence API, not on a username implementation. The persistence layer owns the mapping:

```text
active player -> game -> saved state / Best Score
```

This keeps account/profile changes from forcing rewrites across every game.
