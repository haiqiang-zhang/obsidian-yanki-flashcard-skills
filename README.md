# Obsidian Yanki Flashcard Skill

A Codex skill that turns your content into Yanki-compatible flashcards inside your Obsidian vault, preferring one card per topic within each add request.

Requires the [Yanki Obsidian plugin](https://github.com/kitschpatrol/yanki-obsidian) with at least one watched folder configured.

Compatible with Yanki 1.12.2.

## Install

```bash
mkdir -p ~/.agents/skills
git clone https://github.com/haiqiang-zhang/obsidian-yanki-flashcard-skills.git \
  ~/.agents/skills/add-yanki-flashcards
```

Restart Codex, open your Yanki-enabled vault, and invoke `$add-yanki-flashcards`.
