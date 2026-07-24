---
phase: 3
title: "Test and apply"
status: pending
priority: P1
effort: "1-2h"
dependencies: [2]
---

# Phase 3: Test and apply

## Overview
Exhaustively test add-weapon on COPIES of the real save, adversarially verify, then apply the 4 target items to slot 1. Game must be closed.

## Implementation Steps
1. **Roundtrip regression:** on a copy, run add-weapon then confirm: selftest PASS; find_pgd invariant holds; gaitem parse end == find_pgd; inventory integrity (common/key count==nonzero); the weapon's handle appears identically in the map entry, the inventory record, and (item_id) in GaItemData.
2. **Multi-add:** add all 4 in sequence on one copy; re-verify after each (counters/offsets shift each time). Confirm the 4 show up with correct names via the existing weapon-decode (gaitem_map lookup) and levels.
3. **Adversarial checks (proxy for "does the game load it"):**
   - Byte-diff the copy vs original: only the map region grew by N*13 and the tail shifted; no unrelated bytes changed except intended edits + checksum.
   - Confirm no existing weapon/gaitem entry was overwritten (all pre-existing handles still present).
   - Confirm dropped trailing bytes were all zero.
4. **Determine max upgrade** per target (standard +25 vs somber +10): Erdtree Seal, Buckler, Jellyfish Shield, Wing of Astel. If unsure for any, add at +0 and let the user upgrade in-game (has all stones + Hewg). Prefer +0 over a guessed level that could be an invalid item_id.
5. **Apply to real save** (game-closed guarded): backup, add the 4, verify, report. Keep the pre-change backup path.
6. Update tool docstring/CLI help; recommend `checkpoint` (git) after.

## Success Criteria
- [ ] All copy tests pass (selftest, integrity, map/inventory/GaItemData consistency, no overwrite)
- [ ] 4 items added to real save; integrity OK; backup retained
- [ ] User can equip/use them in-game (reported by user after loading)

## Risk Assessment
The only unverifiable step is in-game load. Mitigate by matching ClayAmore's exact writes + structural proofs + backup. If the user reports a crash/invalid item, restore backup and fall back to +0 or in-game acquisition.
