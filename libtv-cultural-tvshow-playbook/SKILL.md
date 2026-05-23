---
name: libtv-cultural-tvshow-playbook
description: Benchmark and operationalize LibTV TV Show methods for Chinese cultural documentary, oriental-aesthetic, mythology, literary, scenic, non-heritage, or humanities short-form video projects. Use when Codex needs to study public LibTV TV Show examples, extract repeatable workflow patterns, and turn them into a tighter brief, storyboard, asset budget, model ladder, and failure-avoidance plan before running LibTV generation.
---

# LibTV Cultural TV Show Playbook

## Overview

Use this skill before `$libtv-skill` when the main risk is not API execution but creative drift, shot bloat, asset explosion, or loss of Chinese-cultural tone.

This skill owns benchmark-driven preproduction. `$libtv-skill` still owns actual LibTV session creation, upload, polling, and download.

## Workflow

1. Classify the target project.

- `cultural-doc`: history, craft, transmission, civilization, or humanities framing
- `mythic-short`: 志怪, 神话, 史诗, 东方幻想
- `scenic-cultural`: 地域景观, 文旅, 地方文化意象
- `humanities-essay`: 议题短片, 文化评论, 观点视频
- `literary-adaptation`: 聊斋, 水浒, 古典文本改编

2. Pull 5-10 related public LibTV TV Show references.

- If template UUIDs are known or you need structured metrics, run `scripts/extract_libtv_detail_summary.py`.
- Prefer projects whose detail endpoint exposes `snapshotData`. If detail returns no nodes, keep that project only as aesthetic reference, not as workflow evidence.

3. Score each reference on four axes.

- subject relation
- visual relation
- structure relation
- production relation

4. Freeze the production envelope before writing prompts.

- target duration
- shot count
- chapter count
- asset ceiling
- model ladder
- hero-shot quota
- banned drift patterns

5. Choose one pipeline and commit to it.

6. Rewrite the brief, storyboard, and asset plan first. Do not start generation from a drifted first frame.

## Pipeline Choice

### 1. Script-led storyboard pipeline

Use for cultural docs, literary adaptation, or any project that needs one meaning beat per shot.

Pattern:

- `script/text anchor -> storyboard group -> image refs -> shot stills -> video clips -> final assemble`

Use when you need chapter control, compressibility, and a clean way to preserve meaning while reducing cost.

### 2. Image-matrix exploration pipeline

Use for scenic, mythic, or aesthetic discovery when identity continuity is weak.

Pattern:

- `text note -> image variations -> promote winners -> video clips`

Use only until the visual language is found. Then collapse back to a constrained production plan.

### 3. Research-heavy concept pipeline

Use sparingly for manifesto or essay films where motif exploration is the product.

Pattern:

- dense `text + image` canvas, many branches, few final clips

Do not copy this into budget-sensitive cultural documentary work unless the user explicitly wants broad exploration.

## What Benchmarks Consistently Show

- The strongest cultural projects lock a narrow visual system early, then repeat it across clips.
- Working pipelines usually stay `image -> video`; they do not jump straight to many unrelated video prompts.
- Reference images matter more than prompt flourish once identity or material continuity matters.
- Public high-craft canvases often use multiple models, but defaulting to that stack is usually wasteful.
- When a project has a real script node, the canvas is much easier to compress without losing meaning.
- Scenic or concept-heavy projects with no script node tend to overproduce images first, then retrofit narrative later.

## Defaults For Cultural Documentary Work

Use these unless the user already defined stronger constraints:

- Keep one core information point per shot.
- Prefer 12-20 clips for a sub-3-minute cut.
- Keep each clip visually responsible for only one era, process step, or meaning beat.
- Use one dominant baseline image model for most shots. Escalate only for a few hero frames.
- Keep reference-image chains short and intentional.
- Build chapter groups when there are era or argument transitions.
- Treat character sheets as optional. For craft-led films, scene and material references usually matter more than人物设定.

## Failure Avoidance

- If the result drifts into `器物广告` or `静物陈列`, explicitly ban hero prop closeups and restate `主体 + 动作/过程 + 环境`.
- If the canvas exceeds roughly 80-120 nodes before a usable cut exists, compress the plan immediately.
- If three or more image models appear without a clear role split, collapse to baseline plus one escalation model.
- If every shot is visually rich but semantically empty, add text or script anchors before more generation.
- If a project is scenic-only but the user asked for culture or civilization, restore historical, human, or transmission logic.
- If chapter boundaries are weak, use group nodes and explicit transition motifs instead of longer prompts.

## Output Contract

When using this skill, produce:

- a relation-ranked reference list
- the reusable patterns worth copying
- the patterns to avoid
- a chosen pipeline
- a production envelope
- a model ladder
- a first-frame policy
- a failure-avoidance checklist

If the workspace already contains planning artifacts such as `script_analysis.md`, `storyboard.md`, `scene_index.json`, or `asset_list.md`, rewrite those before invoking `$libtv-skill`.

## Resources

- Benchmark notes: read `references/libtv-cultural-benchmarks-2026-04-09.md`
- Structured benchmark data: read `references/libtv-cultural-benchmarks-2026-04-09.json`
- If you need to refresh or extend the benchmark set from public template UUIDs, run `scripts/extract_libtv_detail_summary.py`
