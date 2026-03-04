---
name: skill-miniprogram-optimization
description: Optimize WeChat Mini Program pages for responsive layout, scrolling architecture, and interaction consistency. Use when fixing horizontal overflow, button truncation, cross-device adaptation, scroll-view-only list scrolling, floating headers and footers, left-menu and right-list sync, spec modal layout, and safe-area bottom actions in pages such as menu, cart, and orderDetail.
---

# Miniprogram Optimization

## Execute Workflow

1. Scope the page and constraints.
- Identify target page(s) and components: header/search/content list/sidebar/footer/modal.
- Decide whether to disable page-level scroll (`disableScroll: true`) and which `scroll-view` owns vertical scrolling.

2. Establish scrolling architecture.
- Keep non-list UI floating: place header/search/footer outside the main list `scroll-view`.
- Set container stack:
  - parent: `height: 100vh; overflow: hidden; display: flex; flex-direction: column;`
  - list wrapper: `flex: 1; min-height: 0;`
- Keep only intended areas scrollable (`scroll-y` on sidebar/content list).

3. Eliminate horizontal overflow baseline.
- Add width guards to flex/grid children:
  - `min-width: 0; box-sizing: border-box; overflow-x: hidden;`
- Clamp long single-line labels with ellipsis:
  - `white-space: nowrap; text-overflow: ellipsis; overflow: hidden;`
- For values that must wrap (order id/remark), use `word-break: break-all`.

4. Stabilize button adaptation across devices.
- Remove implicit button margins (`margin: 0`).
- Prefer fluid width:
  - full-width buttons: `width: 100%; min-width: 0;`
  - bounded buttons: `width: <percent>; min-width: <rpx>; max-width: <rpx>;`
- In grid layouts use `repeat(n, minmax(0, 1fr))`.
- Prevent text from forcing layout: apply ellipsis and compact padding on small screens.

5. Apply safe-area and fixed bottom actions.
- For fixed footers:
  - `position: fixed; left: 0; right: 0; bottom: 0;`
  - `padding-bottom: calc(base + env(safe-area-inset-bottom));`
- Reserve content bottom spacer so fixed bars never cover controls.

6. Implement menu scroll linkage (when category sidebar exists).
- Bind right list `bindscroll`.
- Measure section anchors using `createSelectorQuery` with `boundingClientRect` and `scrollOffset`.
- Map `scrollTop` to active category and sync left sidebar highlight.
- Add a short programmatic-scroll lock after click to prevent jitter loops.

7. Optimize spec modal.
- Use bottom-sheet container with safe-area padding.
- Use two-column action grid: `repeat(2, minmax(0, 1fr))`.
- Force action buttons to `width: 100%; min-width: 0; box-sizing: border-box`.
- Keep option chips wrapped (`flex-wrap: wrap`).

8. Validate on a device matrix.
- Validate on at least:
  - narrow phone width (iPhone SE class)
  - common iPhone/Android width
  - devices with bottom safe area
- Check:
  - no horizontal scrollbar
  - no button clipping/truncation layout break
  - category linkage accuracy
  - fixed footer does not cover active content

## Apply-by-File Checklist

- `index.json`
  - Set `disableScroll: true` when adopting inner `scroll-view` architecture.
- `index.wxml`
  - Separate floating zones and list zones.
  - Bind `bindscroll` where linkage is needed.
- `index.wxss`
  - Add container/flex/grid/ellipsis/safe-area guards.
  - Add `@media (max-width: 360px)` compaction when needed.
- `index.ts` or `index.js`
  - Implement linkage measurement and re-measure after data changes.
  - Keep a short scroll lock window for click-to-scroll transitions.

## References

- Read [references/mini-program-optimization-checklist.md](references/mini-program-optimization-checklist.md) to diagnose root causes and apply copy-ready patterns.
