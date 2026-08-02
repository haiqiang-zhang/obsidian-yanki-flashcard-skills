---
name: add-yanki-flashcards
description: Exclusively convert user-provided material into flashcards for the Obsidian Yanki plugin by writing each card as Yanki-compatible Markdown in the appropriate watched vault folder, validating it, and automatically triggering Yanki sync after every successful add operation. Use only when the user explicitly uses Yanki or asks to add cards through an existing Yanki-enabled Obsidian vault; do not use for native Anki, direct AnkiConnect, exports, or other Obsidian flashcard plugins.
---

# Add Yanki Flashcards

Create focused cards in the Yanki-enabled Obsidian vault where the agent is running. Read watched folders at runtime; never hardcode a personal vault path or assume the folder is named `ANKI`.

Resolve `<skill-dir>` to the directory containing this `SKILL.md`, and invoke the bundled script by its absolute path. Keep the working directory at the target vault root.

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
   python "<skill-dir>/scripts/yanki_card.py" inspect
   ```

   Read the returned watched folders, deck directories, `sync`, and `filename_management` values. The source of truth is `.obsidian/plugins/yanki/data.json`; never modify it.
   - Do not ask for separate sync consent. Invoking this skill to add cards authorizes the Yanki synchronization required by step 7 for that add operation.
   - If `sync.auto_sync_enabled` is `true`, creating files may trigger an earlier background sync. Proceed without pausing, then still run the explicit post-validation sync in step 7 so the completed add operation ends with a sync.
   - If `sync.push_to_anki_web` is `true`, the Yanki sync may also attempt AnkiWeb synchronization. Preserve that setting and report it; never change Yanki's configuration.
   - If either sync setting is `null`, do not guess its value or block the write. Follow the explicit sync procedure in step 7 and report only the result that can be observed.

3. Choose the corresponding deck folder.
   - Treat the returned deck directories as a filesystem hierarchy. `/` means the entire vault. Use each full vault-relative path when comparing candidates.
   - Do not assume every watched root becomes an Anki deck. A watched root without direct notes may be omitted from the Anki deck path; the created note's actual parent folder controls its deck.
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
   - Use Yanki-supported Markdown when it improves a card: images, audio, video, tables, task/bullet/numbered lists, fenced code, alerts, math, highlights, furigana, wikilinks, and other inline formatting. Preserve user-provided rich Markdown instead of flattening it to prose.
   - Read [references/yanki-markdown.md](references/yanki-markdown.md) before using a non-basic type, image/embed, table, list, math, or advanced syntax. Follow its Cloze numbering, hint, and single-line restrictions.
   - Before using local or remote media, compare it with `sync.media_mode`. If the value is `null`, ask the user to verify Yanki's media setting. Do not promise that an asset will appear in Anki when its media category is not enabled. Stop and ask whether to proceed if a required local asset will not be copied; never change Yanki settings yourself.
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
   python "<skill-dir>/scripts/yanki_card.py" add --spec /tmp/card.json
   ```

   The script refuses paths outside Yanki's watched folders, avoids overwriting files, detects same-folder duplicate card bodies, and avoids names that Yanki would treat as ignored folder notes. Pass `--create-folder` only after the explicit user confirmation required by step 3.

6. Verify every created file.

   ```bash
   python "<skill-dir>/scripts/yanki_card.py" validate --file "/path/to/card.md"
   ```

   Re-read the final file if the card contains math, code, embeds, or unusual Markdown. Map every coverage-checklist item to at least one created card; if any item is missing, create or repair cards and repeat verification before reporting completion. If `filename_management.auto_rename_trigger` is `file-changed`, re-check the path after Yanki has processed the file; if it was renamed, find the unique same-folder note with the identical card body and validate that final path. Report the final vault-relative path and inferred card type.

7. Synchronize automatically after all created files pass verification.
   - Do not ask whether to sync. Invoke `Yanki: Sync flashcard notes to Anki` through an available Obsidian interface immediately after each successful add operation, even when Yanki may already have run background automatic sync.
   - Report the actual command result. Never imply that writing the Markdown files alone means they synced, and never claim success from an unobserved background sync.
   - When `sync.push_to_anki_web` is `true`, state that the invoked Yanki sync also attempts AnkiWeb synchronization, but distinguish the locally observed Yanki result from independently verified AnkiWeb completion.
   - When the interface requires a command ID, use the exact `sync.command_id` returned by `inspect`: Yanki 1.11.7 and later use `yanki:sync`; versions through 1.11.6 use `yanki:sync-yanki-obsidian`. Do not try the legacy ID on a current installation merely because it used to work.
   - If `sync.command_id` is `null`, do not guess from an unparseable or missing plugin version. Invoke the command by its displayed name only if the interface supports name lookup; otherwise tell the user to run it manually.
   - If the command fails, no callable Obsidian interface is available, or Obsidian is not running, do not claim success; report that automatic sync could not complete and tell the user to run `Yanki: Sync flashcard notes to Anki` manually.
   - If `filename_management.auto_rename_trigger` is `before-sync`, re-check and validate the final paths after any observed sync before reporting them.
   - Do not write directly to AnkiConnect or trigger AnkiWeb synchronization as a substitute.

## Failure handling

- If Yanki is missing or has no watched folders, stop and tell the user what must be configured in Obsidian.
- If Obsidian CLI is unavailable, continue with the filesystem script; the script does not require Obsidian to be running.
- If a required media asset cannot sync under the current Yanki `mediaMode`, explain the exact mismatch instead of silently dropping the media.
- Never edit Yanki's `data.json`, delete cards, move watched folders, or overwrite an existing note as part of adding a card.
- Treat the Obsidian Markdown files as the source of truth. Do not write directly to AnkiConnect for this workflow.
