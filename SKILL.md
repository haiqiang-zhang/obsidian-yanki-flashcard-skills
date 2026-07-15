---
name: add-yanki-flashcards
description: Exclusively convert user-provided material into flashcards for the Obsidian Yanki plugin by writing each card as Yanki-compatible Markdown in the appropriate watched vault folder. Use only when the user explicitly uses Yanki or asks to add cards through an existing Yanki-enabled Obsidian vault; do not use for native Anki, direct AnkiConnect, exports, or other Obsidian flashcard plugins.
---

# Add Yanki Flashcards

Create focused cards in the Yanki-enabled Obsidian vault where the agent is running. Read watched folders at runtime; never hardcode a personal vault path or assume the folder is named `ANKI`.

## Scope boundary

Use this skill only for the Obsidian plugin whose manifest ID is `yanki`. Require `.obsidian/plugins/yanki/manifest.json` and `data.json` in the target vault. Do not substitute native Anki operations, direct AnkiConnect writes, CSV/APKG exports, Obsidian Spaced Repetition, Obsidian_to_Anki, or any other flashcard plugin.

## Workflow

1. Identify the target vault.
   - By default, treat the agent's current working directory as the vault root. Require `.obsidian` directly inside that directory.
   - Do not scan the filesystem, Obsidian's vault registry, environment variables, recent vaults, or other known vault paths.
   - Use `--vault "/path/to/vault"` only when the user explicitly supplies a different vault path.
   - If the current working directory is not a Yanki-enabled vault root, stop and ask the user to open the agent at that vault root or provide its path.

2. Inspect Yanki before every write.

   ```bash
   python scripts/yanki_card.py inspect
   ```

   Read the returned watched folders and existing deck directories. The source of truth is `.obsidian/plugins/yanki/data.json`, especially `folders` and `ignoreFolderNotes`.

3. Choose the corresponding deck folder.
   - Honor an explicit folder or deck from the user.
   - Otherwise match the material's subject to existing folder names and nearby cards. Read only a few representative filenames or cards when needed.
   - Remember that the note's parent folder determines its Anki deck and nested folders create nested decks.
   - If exactly one folder is clearly appropriate, proceed directly. If several are equally plausible, ask the user instead of guessing.
   - Create a new subfolder only when the user explicitly requests a new deck or the intended new taxonomy is unambiguous.

4. Design the cards.
   - Before writing, enumerate every distinct knowledge point the user asks to add or supplies for conversion as a coverage checklist, including required facts, steps, conditions, exceptions, formulas, notation, and examples.
   - Treat every checklist item as mandatory. Split the material into as many focused cards as needed, but never drop, silently omit, or generalize away a requested knowledge point to reduce the card count.
   - Put one testable recall target in each note. Split unrelated facts into separate cards.
   - Preserve the user's language and exact technical notation.
   - Prefer `basic`. Use `reversed` only for genuinely symmetric facts, `type-answer` for a short exact response, and `cloze` when context is essential.
   - Read [references/yanki-markdown.md](references/yanki-markdown.md) before using a non-basic type or advanced syntax.
   - Do not add `noteId`; Yanki manages it during sync.

5. Write each card with the bundled script. Prefer a JSON spec for multiline or punctuation-heavy content:

   ```json
   {
     "folder": "Flashcards/Computer Science",
     "title": "Amdahl's law speedup limit",
     "type": "basic",
     "front": "What limits parallel speedup according to Amdahl's law?",
     "back": "The serial fraction of the workload.",
     "tags": ["parallelism"]
   }
   ```

   ```bash
   python scripts/yanki_card.py add --spec /tmp/card.json
   ```

   The script refuses paths outside Yanki's watched folders, avoids overwriting files, detects same-folder duplicate card bodies, and avoids names that Yanki would treat as ignored folder notes. Pass `--create-folder` only under the rule in step 3.

6. Verify every created file.

   ```bash
   python scripts/yanki_card.py validate --file "/path/to/card.md"
   ```

   Re-read the final file if the card contains math, code, embeds, or unusual Markdown. Map every coverage-checklist item to at least one created card; if any item is missing, create or repair cards and repeat verification before reporting completion. Report the vault-relative path and inferred card type.

7. Do not trigger Anki or AnkiWeb synchronization unless the user asks. Writing the Markdown note completes the default task. If useful, mention that the user can run `Yanki: Sync flashcard notes to Anki` in Obsidian.

## Failure handling

- If Yanki is missing or has no watched folders, stop and tell the user what must be configured in Obsidian.
- If Obsidian CLI is unavailable, continue with the filesystem script; the script does not require Obsidian to be running.
- Never edit Yanki's `data.json`, delete cards, move watched folders, or overwrite an existing note as part of adding a card.
- Treat the Obsidian Markdown files as the source of truth. Do not write directly to AnkiConnect for this workflow.
