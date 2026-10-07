# Yanki Markdown reference

Yanki maps one Obsidian Markdown file to one Anki note. The note's parent folder determines the deck. Folder syncing is recursive, and nested folders become nested Anki decks. A watched folder value of `/` means the entire vault. A watched root with no notes directly inside it may be omitted from the Anki deck path until it contains a direct note.

Official documentation: <https://github.com/kitschpatrol/yanki-obsidian>

Authoring reference: [official Yanki Obsidian agent skill, version 1.13.0](https://github.com/kitschpatrol/yanki-obsidian/blob/1.13.0/skills/yanki-obsidian/SKILL.md). Use it for syntax and rendering details; this skill's duplicate preflight, same-topic grouping, explicit-tags-only rule, and automatic post-add sync remain the workflow requirements.

## Note types

### Basic

Separate front and back with one thematic break. Leave blank lines around `---` so it is not parsed as a heading underline; extra breaks do not create additional notes:

```markdown
What is the serial fraction in Amdahl's law?

---

The part of a workload that cannot be parallelized.
```

A file without a note-type cue becomes a front-only Basic note. Use this only when an empty back is intentional:

```markdown
This entire note appears on the front.
```

### Basic and reversed, with optional extra

Use two consecutive thematic breaks between the two directions. A third break introduces content shown on the back of both generated cards.

```markdown
TCP

---

---

Transmission Control Protocol

---

A connection-oriented transport protocol.
```

### Type in the answer

Make the final statement emphasized with `*answer*` or `_answer_`, with a visible prompt before it. Keep the answer plain text, short, exact, and on one line. Do not include thematic breaks in the body or visible content after the answer; YAML frontmatter delimiters are fine.

```markdown
TCP expands to:

_Transmission Control Protocol_
```

### Cloze

Use Markdown strikethrough for each deletion. Multiple deletions create multiple cards by default:

```markdown
Amdahl's law says speedup is limited by the ~~serial fraction~~.
```

Add `_hint text_` at the end of the struck-through content for a hint:

```markdown
Amdahl's law says speedup is limited by the ~~serial fraction _cannot be parallelized_~~.
```

Prefix clozed content with a one- or two-digit number to group deletions on the same generated card:

```markdown
~~1 TCP~~ is a ~~1 connection-oriented~~ transport protocol.
```

Add a thematic break after cloze content for extra back-of-card material. Cloze deletions must be before the first thematic break. A leading one- or two-digit number can be interpreted as a cloze number; to hide the full answer "12 months", write `~~1 12 months~~`.

Keep every cloze deletion on one line. Yanki does not support clozing across multiple lines or block elements. Images, math, and other inline syntax may be clozed when they remain inline.

Deleting an implicitly numbered cloze can shift review history between the remaining clozes. Prefer explicit numbering for notes likely to change, and use Anki's **Tools → Empty Cards...** after removing a cloze that left an empty card.

## Rich Markdown content

Yanki supports normal Markdown inside card content. Preserve useful structure rather than converting it to plain prose. Yanki uses its own Markdown renderer, so an Obsidian preview is not proof of the Anki result.

### Rendering limits

- Note embeds such as `![[Some note]]` or `![[Some note#Heading]]` and PDF embeds become links, not embedded note text or PDF pages. Include the required question, explanation, or source excerpt in the card body itself.
- Mermaid fences render as code rather than diagrams, and plugin features such as Dataview are not automatically rendered. Preserve the needed meaning in supported Markdown or use an existing supported image; do not assume every Obsidian callout variant works.
- The vault's **Strict line breaks** setting controls paragraph newlines. Use blank lines for separate paragraphs or explicit Markdown hard breaks when required.

### Images

Use Obsidian embeds or standard Markdown images. Keep referenced assets resolvable from the vault; do not move, copy, or download images unless the user asks.

```markdown
What structure is shown?

---

![[tcp-header.png]]
```

```markdown
![TCP header](attachments/tcp-header.png)
```

### Audio and video

Yanki can sync linked image, audio, and video assets into Anki media. Use Obsidian embeds or supported Markdown links:

```markdown
![[pronunciation.mp3]]

![[demonstration.mp4]]
```

Honor Yanki's `sync.mediaMode` setting:

- `all`: copy local and remote assets.
- `local`: copy local assets only; this is Yanki's default.
- `remote`: copy remote assets only.
- `off`: do not copy media into Anki. Remote hotlinks may still render when the learner has network access.

### Tables

```markdown
Compare TCP and UDP.

---

| Property | TCP | UDP |
| --- | --- | --- |
| Connection | Yes | No |
| Delivery guarantee | Yes | No |
```

### Lists

```markdown
What are the three steps?

---

1. Inspect the input.
2. Transform it.
3. Verify the output.
```

Bullet lists are also supported:

```markdown
- First fact
- Second fact
```

Task lists are supported as GitHub Flavored Markdown:

```markdown
- [x] Completed step
- [ ] Remaining step
```

### Other supported syntax

Yanki also supports fenced code with syntax highlighting, GitHub-style alerts, autolinks, LaTeX math, `==highlights==`, DenDen furigana such as `{東京|とうきょう}`, and Obsidian heading or block links such as `[[Note#Heading]]` and `[[Note#^block-id]]`.

Yanki 1.11.9 correctly resolves local note links, WikiLinks, and media embeds whose target filename contains a literal `?` on macOS or Linux. Preserve the literal `?` in the Markdown target and let Yanki encode the generated link. Do not create or reference such filenames on Windows, where `?` is not allowed in filenames.

Yanki 1.11.10 correctly resolves Obsidian heading and block anchors containing `/`, dot segments, backslashes, or Unicode, such as `[[Protocols#2G/EDGE]]`. Preserve the anchor text exactly as the user supplied it; do not rewrite its slash as a file path separator or pre-encode it.

Yanki 1.12.0 keeps the same card formats, `data.json` keys, media modes, and `yanki:sync` command ID. It adds searchable declarative settings on Obsidian 1.13 and later; continue reading the stored values from `data.json` rather than relying on settings UI labels.

Yanki 1.12.1 fixes media filename hash collisions. Distinct local assets with the same size and modification time, and distinct remote assets with identical response metadata, now receive distinct Anki media filenames. Keep each intended asset reference unchanged; do not rename, duplicate, or otherwise disambiguate assets as a workaround.

Do not use `~~strikethrough~~` decoratively in a flashcard: Yanki treats it as Cloze syntax. Do not use native Anki markup such as `{{c1::answer}}`; it can conflict with Yanki's Markdown parser.

## Tags and metadata

Omit tags and tag frontmatter by default. Add tags only when the user explicitly specifies their values; never infer or generate tags from the card subject or nearby cards. If tags are requested, Yanki reads them from Obsidian properties, not inline body tags:

```markdown
---
tags:
  - networking
  - protocols
---

Card front

---

Card back
```

Do not create or modify `noteId`; Yanki owns that property. Do not invent `deck`, `deckName`, or `type` frontmatter: the folder and Markdown syntax control those values, not these properties. The bundled script's JSON `type` field chooses the generated syntax; it is not a frontmatter field. Standard Markdown, Obsidian wikilinks, math, tables, lists, and supported embeds may be used inside card content.

## Compatibility and runtime troubleshooting

Verified against [Yanki 1.13.0](https://github.com/kitschpatrol/yanki-obsidian/releases/tag/1.13.0), which bundles the Yanki 3.1.0 core and adds an official agent skill. Card syntax, watched-folder mapping, stored settings keys, and the `yanki:sync` command remain unchanged. Upstream requires both the Obsidian app and installer versions to be 1.9.12 or newer.

This workflow uses the core bundled with the Obsidian plugin. The standalone Yanki CLI/library's Node.js requirements are not a system Node.js prerequisite here; do not install or invoke the standalone CLI as a substitute.

If sync reports an unexplained `TypeError` even though the Obsidian app appears current, ask the user to open **Settings → General** or run `Show debug info` and check the **installer version** separately. In-app updates do not update the underlying Electron/Chromium runtime. If the installer is older than 1.9.12, direct the user to Obsidian's [installer update instructions](https://obsidian.md/help/updates#Installer+updates). Do not reinstall Obsidian or change Yanki settings automatically.

## Important behavior

- Removing a watched folder can delete Yanki-managed notes and their review history from Anki on the next sync.
- When `ignoreFolderNotes` is enabled, a note whose basename equals its parent folder name is excluded.
- Deleting implicitly numbered clozes can shift review history between remaining clozes. Prefer explicit numbers for cloze notes likely to change heavily.
- Automatic sync can run almost immediately after a watched note changes. When this skill adds cards, proceed under the user's add request and still perform the explicit post-validation sync required by the main workflow.
- Automatic note naming can rename created files on change or immediately before sync; report the final path.
- Yanki 1.11.7 renamed the full Obsidian sync command ID from `yanki:sync-yanki-obsidian` to `yanki:sync`; existing hotkeys bound to the old ID must be re-bound. The displayed command remains `Yanki: Sync flashcard notes to Anki`.
