# LibTV Cultural Benchmarks

Public sample set captured on 2026-04-09 from LibTV TV Show public feed and detail endpoints.

Selection rule:

- related to `《一滴墨的旅程》` by at least one dimension: Chinese cultural tone, craft or heritage, literary or mythic source, scenic-humanities framing, or essay-like cultural argument
- detail endpoint exposes usable `snapshotData`, so the canvas can be studied as workflow evidence

## Sample Set

1. [为什么中国神话鲜少有女性英雄？——巨妮JUNIE](https://www.liblib.tv/detail/178b536a7354417aa52ce7d4db589038)
Relation: humanities essay, Chinese myth discourse
Likes: 84
Canvas shape: 885 nodes, 783 images, 98 text, 3 videos
Copy: thesis-first research canvas, explicit text anchors
Avoid: copying its exploration scale into budget-sensitive production

2. [东方奇谭｜天阙之战](https://www.liblib.tv/detail/0fcddbcc2d2f4f5facd821d83c1de9e1)
Relation: oriental mythic short, strong visual system
Likes: 46
Canvas shape: 2 script nodes, 18 rows, 2 storyboard groups, 33 images, 12 videos
Copy: `script -> storyboard group -> image -> video` structure
Avoid: expanding chapter count without keeping the script node as the source of truth

3. [水浒传·风雪山神庙](https://www.liblib.tv/detail/8244d6f1b7e147eca05accb7e0c347c6)
Relation: literary adaptation, historical Chinese setting
Likes: 44
Canvas shape: 166 images, 53 videos, 1 video-story node
Copy: large image library fanning into many short clips
Avoid: letting the clip library sprawl before the final structure is locked

4. [中式深空禅意美学AI短片《太虚游记》](https://www.liblib.tv/detail/946ee75b69de47cc9bc37dfd1cffae62)
Relation: Chinese philosophical atmosphere, essay-like visual poem
Likes: 31
Canvas shape: 72 images, 9 text, 14 videos
Copy: text anchors before image exploration, then promote winners to clips
Avoid: treating mood exploration as a substitute for shot logic

5. [敦煌短片](https://www.liblib.tv/detail/bdf2765f208e489689d1c797925b8cf1)
Relation: cultural motif, mural and heritage imagery
Likes: 10
Canvas shape: 2 script nodes, 12 rows, 6 storyboard groups, 24 images, 18 videos
Copy: group-per-board segmentation for cultural motif breakdown
Avoid: adding more clips before the board groups are coherent

6. [StarVideo2.0东方美学CG幻想游戏短片](https://www.liblib.tv/detail/8ac702a824d74780ba0c51d3509ce44a)
Relation: oriental lookdev and CG fantasy
Likes: 10
Canvas shape: 36 images, 13 videos
Copy: fast lookdev with image-to-image stabilization
Avoid: copying its multi-model stack when the project mainly needs consistency

7. [中式美学敦煌飞天舞蹈裸眼3D](https://www.liblib.tv/detail/74cb49cee61948eeabe6e2e4b069dd79)
Relation: Chinese stage performance, cultural motion design
Likes: 5
Canvas shape: 36 images, 8 videos, audio and text support
Copy: performance-centered motion emphasis
Avoid: replacing story or process beats with pure pose spectacle

8. [黄沙漫过丝路，文创敦煌短片](https://www.liblib.tv/detail/7cdbb7b8fa374300a13a27dc1ada3daa)
Relation: regional culture,文旅/文创 framing
Likes: 5
Canvas shape: 37 images, 15 videos
Copy: motif consistency across many scenic clips
Avoid: staying at postcard level when the user asked for cultural meaning

9. [聊斋·她宇宙](https://www.liblib.tv/detail/2dcd3fdfcbd44abbb0a5a7519fffc2fd)
Relation: classical source + humanities reinterpretation
Likes: 5
Canvas shape: 1 script node, 9 rows, 15 images, 17 videos, audio
Copy: compact script-led cultural reinterpretation
Avoid: skipping audio or narration thinking until the end

10. [东方美学3D西湖踏青短片](https://www.liblib.tv/detail/03f87640a5cd4bb1a51c2bafda693fe8)
Relation: scenic culture and place identity
Likes: 2
Canvas shape: 39 images, 15 videos
Copy: location identity through repeated scenic language
Avoid: scenic beauty without human or historical intent

## Stable Patterns

### Pattern A: script-led compression

Observed in:

- 东方奇谭｜天阙之战
- 敦煌短片
- 聊斋·她宇宙

What works:

- 1-2 script nodes are enough
- 9-18 rows are already workable for a short cultural piece
- storyboard groups make later compression much easier

### Pattern B: image matrix to clip fanout

Observed in:

- 西湖踏青
- 丝路敦煌
- StarVideo2.0 东方美学
- 敦煌飞天舞蹈裸眼3D

What works:

- strong `image -> image` chains stabilize look
- `image -> video` is the dominant production edge
- scenic clips often land around 4-6 seconds

### Pattern C: research-heavy concept canvas

Observed in:

- 巨妮JUNIE

What works:

- text nodes preserve thesis and argument
- giant image libraries are useful for motif discovery

What fails for most production work:

- too expensive
- too hard to compress quickly
- too easy to mistake exploration volume for progress

### Pattern D: large historical clip library

Observed in:

- 水浒传·风雪山神庙

What works:

- many short clips can be built from a relatively small set of stabilized image families

What to watch:

- without a strong structure, the canvas gets noisy fast

## Implications For Craft-led Cultural Docs

For projects like `《一滴墨的旅程》`, the benchmark set points to one strong rule:

- prefer the script-led compression route, not the research-heavy concept route

Recommended translation:

- chapter first
- one information point per shot
- board groups before clip generation
- one baseline model for most frames
- limited hero-shot upgrades
- scene and material references matter more than standalone character sheets
