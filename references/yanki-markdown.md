# Yanki Markdown reference

Yanki maps one Obsidian Markdown file to one Anki note. The note's parent folder determines the deck. Folder syncing is recursive, and nested folders become nested Anki decks.

Official documentation: <https://github.com/kitschpatrol/yanki-obsidian>

## Note types

### Basic

Separate front and back with one thematic break:

```markdown
What is the serial fraction in Amdahl's law?

---

The part of a workload that cannot be parallelized.
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

Make the final statement emphasized. Keep the answer short and exact.

```markdown
TCP expands to:

_Transmission Control Protocol_
```

### Cloze

Use Markdown strikethrough for each deletion:

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

Add a thematic break after cloze content for extra back-of-card material.

## Tags and metadata

Yanki reads tags from Obsidian properties, not inline body tags:

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

Do not create or modify `noteId`; Yanki owns that property. Standard Markdown, Obsidian wikilinks, math, and supported embeds may be used inside card content.

## Important behavior

- Removing a watched folder can delete Yanki-managed notes and their review history from Anki on the next sync.
- When `ignoreFolderNotes` is enabled, a note whose basename equals its parent folder name is excluded.
- Deleting implicitly numbered clozes can shift review history between remaining clozes. Prefer explicit numbers for cloze notes likely to change heavily.
