# Mini Program Optimization Checklist

## 1) Horizontal Scroll Root-Cause Scan

Run these checks first:
- Fixed width in narrow containers (`width: 200rpx` + side paddings)
- Missing `min-width: 0` in flex/grid children
- Default button margins (`button` in mini program)
- Long text without ellipsis or wrap strategy
- Nested paddings that exceed viewport width

Quick search patterns:
- `width:` with large fixed `rpx`
- `.touch-target` usage inside tight rows
- `grid-template-columns: 1fr 1fr 1fr` without `minmax(0, 1fr)`

## 2) Copy-Ready Layout Guard Snippets

Container pattern:
```css
.container {
  height: 100vh;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}
.content {
  flex: 1;
  min-height: 0;
  min-width: 0;
  overflow: hidden;
}
```

List wrapper pattern:
```css
.list {
  flex: 1;
  min-width: 0;
  overflow-x: hidden;
  box-sizing: border-box;
}
```

Row with long text + stepper:
```css
.row { display: flex; min-width: 0; overflow: hidden; }
.info { flex: 1; min-width: 0; }
.name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stepper { flex-shrink: 0; }
```

Button grid pattern:
```css
.actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}
.actions button {
  margin: 0;
  width: 100%;
  min-width: 0;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

## 3) Floating Header/Footer + Inner Scroll Strategy

- Put header/search/footer outside main list `scroll-view`.
- Put left sidebar and right list in the same flex content area.
- Disable page scroll in `index.json` when using internal scroll architecture.

## 4) Menu Linkage Strategy

- Track category anchors after render and after data/filter changes.
- Bind right list `bindscroll` and map `scrollTop` to current category.
- After clicking sidebar category, lock linkage updates briefly to prevent flicker.

## 5) Safe-Area Bottom Strategy

Use both of these:
- Footer padding: `padding-bottom: calc(base + env(safe-area-inset-bottom));`
- List spacer: add bottom spacing block so content is never covered.

## 6) Verify Before Finish

- Narrow device width: no horizontal scroll.
- Long dish names/order ids: no layout break.
- Modal action buttons: no clipping, no overflow.
- Left-right linkage: smooth and accurate during manual scroll.
- Fixed footer: no overlap with final interactive rows.
