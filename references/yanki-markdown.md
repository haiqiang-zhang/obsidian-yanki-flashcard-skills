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

Make the final statement emphasized with `*answer*` or `_answer_`. Keep the answer short, exact, and on one line.

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

Add a thematic break after cloze content for extra back-of-card material.

Keep every cloze deletion on one line. Yanki does not support clozing across multiple lines or block elements. Images, math, and other inline syntax may be clozed when they remain inline.

Deleting an implicitly numbered cloze can shift review history between the remaining clozes. Prefer explicit numbering for notes likely to change, and use Anki's **Tools → Empty Cards...** after removing a cloze that left an empty card.

## Rich Markdown content

Yanki supports normal Markdown inside card content. Preserve useful structure rather than converting it to plain prose.

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

Do not create or modify `noteId`; Yanki owns that property. Standard Markdown, Obsidian wikilinks, math, tables, lists, and supported embeds may be used inside card content.

## Important behavior

- Removing a watched folder can delete Yanki-managed notes and their review history from Anki on the next sync.
- When `ignoreFolderNotes` is enabled, a note whose basename equals its parent folder name is excluded.
- Deleting implicitly numbered clozes can shift review history between remaining clozes. Prefer explicit numbers for cloze notes likely to change heavily.
