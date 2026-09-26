---
name: add-yanki-flashcards
description: Exclusively convert user-provided material into flashcards for the Obsidian Yanki plugin by writing each card as Yanki-compatible Markdown in the appropriate watched vault folder, validating it, and automatically triggering Yanki sync after every successful add operation. Use only when the user explicitly uses Yanki or asks to add cards through an existing Yanki-enabled Obsidian vault; do not use for native Anki, direct AnkiConnect, exports, or other Obsidian flashcard plugins.
---

# Add Yanki Flashcards

Create topic-coherent cards in the Yanki-enabled Obsidian vault where the agent is running, preferring one card for same-topic material within each add request. Read watched folders at runtime; never hardcode a personal vault path or assume the folder is named `ANKI`.

Resolve `<skill-dir>` to the directory containing this `SKILL.md`, and invoke the bundled script by its absolute path. Keep the working directory at the target vault root.

## Scope boundary

Use this skill only for the Obsidian plugin whose manifest ID is `yanki`. Require `.obsidian/plugins/yanki/manifest.json` and `data.json` in the target vault. Do not substitute native Anki operations, direct AnkiConnect writes, CSV/APKG exports, Obsidian Spaced Repetition, Obsidian_to_Anki, or any other flashcard plugin.

## Workflow

1. Check whether the requested content already exists. This is the mandatory first step for the entire add operation, before creating any folder or card or invoking sync.
   - First resolve the target vault and inspect Yanki using read-only operations so the duplicate check covers the correct folders.
   - By default, treat the agent's current working directory as the vault root. Require `.obsidian` directly inside that directory.
   - Do not scan the filesystem, Obsidian's vault registry, environment variables, recent vaults, or other known vault paths to locate a vault.
   - Use `--vault "/path/to/vault"` only when the user explicitly supplies a different vault path.
   - If the current working directory is not a Yanki-enabled vault root, stop and ask the user to open the agent at that vault root or provide its path.

   Inspect the current Yanki configuration:

   ```bash
   python "<skill-dir>/scripts/yanki_card.py" inspect
   ```

   Read the returned watched folders, deck directories, `sync`, and `filename_management` values. The source of truth is `.obsidian/plugins/yanki/data.json`; never modify it.

   - Search filenames and Markdown bodies recursively across **all configured watched folders**, including their subfolders, for each requested question or knowledge point. `/` means the entire vault. Do not limit the search to the intended destination folder.
   - Use distinctive phrases, key terms, and formulas to find candidates, then read them to compare the actual question and knowledge content. The same content may have a different title, wording, formatting, or card type; exact text equality is not required. A shared subject alone is not a duplicate.
   - Complete this check for the entire requested batch before writing anything. If any matching content already exists, **pause the whole add operation**, show the existing card's vault-relative path and the matching content, and ask the user what to do next. Wait for their answer before continuing.
   - Do not silently skip duplicates, add the remaining cards, merge or update existing cards, or reword content to bypass the check. Offer choices such as keeping the existing card and skipping that item, explicitly creating another copy, or discussing an update; do not choose for the user. An update or merge requires separate explicit direction and is not part of this add-only workflow.
   - Continue only when no duplicates are found or the user has explicitly resolved the disclosed duplicates. If the search cannot be completed, explain the limitation and ask for direction instead of treating it as a clean result.

2. Choose the corresponding deck folder.
   - Treat the returned deck directories as a filesystem hierarchy. `/` means the entire vault. Use each full vault-relative path when comparing candidates.
   - Do not assume every watched root becomes an Anki deck. A watched root without direct notes may be omitted from the Anki deck path; the created note's actual parent folder controls its deck.
   - Honor an explicit folder or deck from the user.
   - Otherwise match the material's subject against existing full folder paths and nearby cards. Read only a few representative filenames or cards when needed.
   - Prefer the most specific existing subfolder that clearly matches. Never place cards in a broad parent when a suitable descendant folder exists.
   - If exactly one existing folder is clearly appropriate, proceed directly. If several are equally plausible, ask the user to choose instead of guessing.
   - If no existing folder clearly matches, stop before writing any card. Propose a new subfolder with its complete vault-relative parent path and ask whether to create it. Do not create the folder or pass `--create-folder` until the user explicitly confirms that path. If the user declines, stop without writing cards.

3. Design the cards.
   - Before writing, enumerate every distinct knowledge point the user asks to add or supplies for conversion as a coverage checklist, including required facts, steps, conditions, exceptions, formulas, notation, and examples.
   - Treat every checklist item as mandatory unless the user explicitly chose to keep an existing card instead in step 1; record that card as covering the item. Never drop, silently omit, or generalize away a requested knowledge point to reduce the card count.
   - Within the same add request, group material by topic and prefer **one card per topic**, not one card per knowledge point. Keep a topic's related definitions, properties, conditions, formulas, and examples together; multiple checklist items may map to the same card. This groups new material only and does not authorize merging existing notes or bypassing step 1.
   - Use an overarching question or a few related subquestions on the front, with a complete, structured answer on the back. For example, a request covering binary search's prerequisites, procedure, and complexity should normally become one card covering all three.
   - Split only when the user explicitly requests separate cards, the topics are genuinely distinct, or combining the content would make a single card clearly unwieldy to review. Multiple facts alone are not a reason to split. If splitting one topic is necessary, briefly explain why.
   - Preserve the user's language and exact technical notation.
   - Prefer `basic`, especially for grouped same-topic material so it is reviewed as one card. Use front-only `basic` when a card intentionally has no back, `reversed` only for genuinely symmetric facts, `type-answer` for a short exact response, and `cloze` when context is essential.
   - Use Yanki-supported Markdown when it improves a card: images, audio, video, tables, task/bullet/numbered lists, fenced code, alerts, math, highlights, furigana, wikilinks, and other inline formatting. Preserve user-provided rich Markdown instead of flattening it to prose.
   - Read [references/yanki-markdown.md](references/yanki-markdown.md) before using a non-basic type, image/embed, table, list, math, or advanced syntax. Follow its Cloze numbering, hint, and single-line restrictions.
   - Before using local or remote media, compare it with `sync.media_mode`. If the value is `null`, ask the user to verify Yanki's media setting. Do not promise that an asset will appear in Anki when its media category is not enabled. Stop and ask whether to proceed if a required local asset will not be copied; never change Yanki settings yourself.
   - Do not add tags unless the user explicitly specifies the tag values. Never infer tags from the subject, generate them automatically, or copy them from nearby cards. If the user asks for tags without naming them, ask which tags to use before writing.
   - Do not add `noteId`; Yanki manages it during sync.

4. Write each card with the bundled script. Prefer a JSON spec for multiline or punctuation-heavy content:

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

   The script refuses paths outside Yanki's watched folders, avoids overwriting files, detects same-folder duplicate card bodies, and avoids names that Yanki would treat as ignored folder notes. Its exact-body duplicate check is only a backstop, not a replacement for step 1. If it detects a duplicate, stop adding cards and apply the same pause-and-ask rule. Never pass `--allow-duplicate` unless the user explicitly chose to create another copy of that disclosed duplicate. Pass `--create-folder` only after the explicit user confirmation required by step 2.

5. Verify every created file.

   ```bash
   python "<skill-dir>/scripts/yanki_card.py" validate --file "/path/to/card.md"
   ```

   Re-read the final file if the card contains math, code, embeds, or unusual Markdown. Map every coverage-checklist item to at least one created card or an existing card the user explicitly chose to keep in step 1; if any item is missing, create or repair cards and repeat verification before reporting completion. If `filename_management.auto_rename_trigger` is `file-changed`, re-check the path after Yanki has processed the file; if it was renamed, find the unique same-folder note with the identical card body and validate that final path. Report the final vault-relative path and inferred card type.

6. Synchronize automatically after all created files pass verification.
   - The duplicate pause in step 1 takes precedence: do not invoke sync while awaiting the user's decision. If the user chooses to keep existing cards and no new cards are created, report that outcome without invoking sync.
   - Do not ask whether to sync. Invoke `Yanki: Sync flashcard notes to Anki` through an available Obsidian interface immediately after each successful add operation, even when Yanki may already have run background automatic sync.
   - If `sync.auto_sync_enabled` is `true`, creating files may trigger an earlier background sync. After the duplicate check is resolved, proceed without separate sync consent, then still run this explicit post-validation sync. If the value is `null`, do not guess it or block the write; follow this explicit sync procedure.
   - Report the actual command result. Never imply that writing the Markdown files alone means they synced, and never claim success from an unobserved background sync.
   - When the interface requires a command ID, use the exact `sync.command_id` returned by `inspect`: Yanki 1.11.7 and later use `yanki:sync`; versions through 1.11.6 use `yanki:sync-yanki-obsidian`. Do not try the legacy ID on a current installation merely because it used to work.
   - If `sync.command_id` is `null`, do not guess from an unparseable or missing plugin version. Invoke the command by its displayed name only if the interface supports name lookup; otherwise tell the user to run it manually.
   - If the command fails, no callable Obsidian interface is available, or Obsidian is not running, do not claim success; report that automatic sync could not complete and tell the user to run `Yanki: Sync flashcard notes to Anki` manually.
   - If `filename_management.auto_rename_trigger` is `before-sync`, re-check and validate the final paths after any observed sync before reporting them.
   - Do not write directly to AnkiConnect or implement a secondary synchronization path. Let Yanki manage every downstream synchronization action.

## Failure handling

- If Yanki is missing or has no watched folders, stop and tell the user what must be configured in Obsidian.
- If Obsidian CLI is unavailable, continue with the filesystem script; the script does not require Obsidian to be running.
- If Yanki sync fails with an unexplained `TypeError` despite an up-to-date Obsidian app, follow [the runtime troubleshooting guidance](references/yanki-markdown.md#compatibility-and-runtime-troubleshooting) to distinguish the app version from the installer version.
- If a required media asset cannot sync under the current Yanki `mediaMode`, explain the exact mismatch instead of silently dropping the media.
- Never edit Yanki's `data.json`, delete cards, move watched folders, or overwrite an existing note as part of adding a card.
- Treat the Obsidian Markdown files as the source of truth. Do not write directly to AnkiConnect for this workflow.
