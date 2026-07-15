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
   - Treat the returned deck directories as a hierarchy. Use each full vault-relative path when comparing candidates; watched folders are roots, and their descendant directories are nested decks.
   - Honor an explicit folder or deck from the user.
   - Otherwise match the material's subject against existing full folder paths and nearby cards. Read only a few representative filenames or cards when needed.
   - Prefer the most specific existing subfolder that clearly matches. Never place cards in a broad parent when a suitable descendant folder exists.
   - If exactly one existing folder is clearly appropriate, proceed directly. If several are equally plausible, ask the user to choose instead of guessing.
   - If no existing folder clearly matches, stop before writing any card. Propose a new subfolder with its complete vault-relative parent path and ask whether to create it. Do not create the folder or pass `--create-folder` until the user explicitly confirms that path. If the user declines, stop without writing cards.

4. Design the cards.
   - Before writing, enumerate every distinct knowledge point the user asks to add or supplies for conversion as a coverage checklist, including required facts, steps, conditions, exceptions, formulas, notation, and examples.
   - Treat every checklist item as mandatory. Split the material into as many focused cards as needed, but never drop, silently omit, or generalize away a requested knowledge point to reduce the card count.
   - Put one testable recall target in each note. Split unrelated facts into separate cards.
   - Preserve the user's language and exact technical notation.
   - Prefer `basic`. Use front-only `basic` when a card intentionally has no back, `reversed` only for genuinely symmetric facts, `type-answer` for a short exact response, and `cloze` when context is essential.
   - Use Yanki-supported Markdown when it improves a card: Obsidian or standard Markdown images, tables, bullet or numbered lists, math, wikilinks, and other inline formatting. Preserve user-provided rich Markdown instead of flattening it to prose.
   - Read [references/yanki-markdown.md](references/yanki-markdown.md) before using a non-basic type, image/embed, table, list, math, or advanced syntax. Follow its Cloze numbering, hint, and single-line restrictions.
   - Do not add tags unless the user explicitly specifies the tag values. Never infer tags from the subject, generate them automatically, or copy them from nearby cards. If the user asks for tags without naming them, ask which tags to use before writing.
   - Do not add `noteId`; Yanki manages it during sync.

5. Write each card with the bundled script. Prefer a JSON spec for multiline or punctuation-heavy content:

   ```json
   {
     "folder": "Flashcards/Computer Science",
     "title": "Amdahl's law speedup limit",
     "type": "basic",
     "front": "What limits parallel speedup according to Amdahl's law?",
     "back": "The serial fraction of the workload."
   }
   ```

   ```bash
   python scripts/yanki_card.py add --spec /tmp/card.json
   ```

   The script refuses paths outside Yanki's watched folders, avoids overwriting files, detects same-folder duplicate card bodies, and avoids names that Yanki would treat as ignored folder notes. Pass `--create-folder` only after the explicit user confirmation required by step 3.

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
