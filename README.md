# R6 Movement & Object-Combat Animations

79 R6 animations in one style. The set includes remakes of the moves in your two reference videos
(*Ironpeak Movement System V6* and the *Movement system SHOWCASE*), plus:

- walk, sprint, jump and landing
- slide and ledge climb
- unarmed attacks and hit reactions
- a pickup / hold / throw / swing / block set for **four object sizes**

**[ANIMATIONS.md](ANIMATIONS.md) has a GIF preview of every animation.** Each GIF is rendered on a
standard R6 rig (round head, classic face) from the exact keyframes in the export files, with no
effects. **[comparisons/](comparisons/)** has side-by-side GIFs of the reference videos next to the
remakes (sprint, walk, crouch walk, rolls, slide, hit flinch).

```
animations/
  AnimSaves_ALL.rbxmx             <- all 79 KeyframeSequences in one Model named "AnimSaves"
  R6Animations_ByCategory.rbxmx   <- same, sorted into folders
  Movement/ Combat/ HitReactions/ Objects/{Small,Medium,Large,Huge}/   <- one .rbxmx per animation
  manifest.json                   <- name, length, priority, loop, joints, markers for each
previews/                         <- one GIF per animation
comparisons/                      <- reference video vs remake, side by side
examples/AnimationLayering.client.lua   <- sprint + swing/block layering, block weakening, block break
source/                           <- the generator (python3 source/build.py rebuilds everything)
```

## Getting them into Studio

1. Right-click **Workspace** (or any rig) and choose **Insert from File...**, then pick
   `animations/AnimSaves_ALL.rbxmx`. You get a Model called `AnimSaves` that holds every
   KeyframeSequence.
2. To publish, pick one of these:
   - Right-click a KeyframeSequence and choose **Save to Roblox**. Copy the asset ID it gives you.
   - Or put `AnimSaves` inside an R6 rig, open the **Animation Editor**, use **Load** to pick an
     animation, then **Publish to Roblox**.
3. You can test without publishing. Put `AnimSaves` in `ReplicatedStorage` and leave the IDs empty
   in `examples/AnimationLayering.client.lua`. In Studio it registers the KeyframeSequences on the
   fly using `KeyframeSequenceProvider:RegisterKeyframeSequence`.

Every animation already has its **Priority** and **Looped** settings, plus named **markers** for
`AnimationTrack:GetMarkerReachedSignal("Hit")`, `"Release"`, `"Footstep"` and so on.

## What's in the set

| Group | Animations |
|---|---|
| **Movement** (video remakes) | Idle, Walk, Sprint, CrouchIdle, CrouchWalk, Jump, Fall, Land, LandHeavy, LandRoll, Roll, SlideStart → Slide (loop) → SlideEnd, LedgeHang, LedgeClimb, WallClimb, WallRunEnterRight / WallRunEnterLeft → WallRunRight / WallRunLeft, WallJump, Vault |
| **Hit reactions** | HitReact (the flinch from the video), HitHeavy |
| **Combat** | Punch1-4 (4-hit combo, Punch4 is a launcher), Kick, HeavyPunch (charged), PunchBlocked, plus Punch1-3 `_UB` |
| **Objects** ×4 sizes | `{Size}Pickup`, `{Size}Hold` (loop), `{Size}Throw` + `_UB`, `{Size}Swing` + `_UB`, `{Size}SwingBlocked`, `{Size}Block` + `_UB`, `{Size}BlockHit`, `{Size}BlockBreak` |

How each object size feels:

| Size | Examples | Style |
|---|---|---|
| **Small** | rock, can, brick, bottle | One hand, light flick throw, quick smack |
| **Medium** | crate, barrel, chair, sign | One hand overhead, pitcher-style throw with knee lift, overhead smash |
| **Large** | car, boulder, dumpster | Two hands overhead, arch-back heave, ground-slam swing |
| **Huge** | train car, plane, bus (2-3× your height) | Wide two-hand titan lift, deep dip-and-launch throw, wide horizontal sweep at chest height |

All of them follow the same style rules taken from the videos: arms flare away from the body, the
chest is never square (it leans, rolls and twists into every move; the sprint's shoulders tilt about
15° each stride, measured from the showcase video), contacts snap in 2-3 frames then hold, and the
head and arms lag a little behind the body and settle. Feet are kept on the floor automatically.

## Using them while sprinting (layering)

Roblox plays several animations at once. For each joint, the highest-priority animation that
**animates that joint** wins. Joints it doesn't animate fall through to lower priorities.

- **Walk / Sprint** are `Movement` priority and animate the whole body.
- The **`_UB` versions** (`MediumSwing_UB`, `LargeBlock_UB`, `Punch2_UB`...) are `Action2` and only
  animate the **neck and shoulders**. The torso and legs keep running from Sprint. Where the
  full-body version twists the torso, the `_UB` version puts that twist into the arms instead, so
  the swing still points the same way.
- The **Hold** loops (`Action`) animate only the arm(s) holding the object. You can carry
  something while Idle, Walk or Sprint plays normally.
- The "something happened" animations (`SwingBlocked`, `BlockHit`, `BlockBreak`, `PunchBlocked`,
  hit reactions) are `Action3`, so they cut over any swing or block that's playing.

The rule `examples/AnimationLayering.client.lua` follows: standing still plays the full-body
version, moving plays the `_UB` version.

```lua
local track = (isMoving() and tracks.MediumSwing_UB) or tracks.MediumSwing
track:Play(0.05)
```

Two notes:

- Sprint is authored for about 26 studs/s and Walk for 16. Use `track:AdjustSpeed(speed / 26)`
  (or `/ 16`) so the feet don't slide.
- The default R6 `Animate` script also plays its own walk at Core priority. Your Movement-priority
  Walk/Sprint override it, but you can also swap the IDs inside `Animate`.

## Blocks that weaken and break

- `{Size}Block` / `{Size}Block_UB` are **4 seconds** long and hand-keyed in stages: the guard slams
  up and holds solid (breathing) until 1.8 s, gives once and re-braces, gives again with a foot
  sliding back at 2.65 s, shakes harder and harder, then buckles at the end.
- For a 3-5 second block, use `track:AdjustSpeed(4 / blockSeconds)`.
- Markers: `Raised` (0.1 s), `Weakening` (1.85 s, first give), `Critical` (3.0 s, hard shaking),
  `Exhausted` (3.95 s). Play `{Size}BlockBreak` on `Exhausted`, or whenever your own block-health
  logic says it breaks.
- `{Size}BlockHit` is the flinch when a hit lands on your guard. It starts and ends in the block
  pose, so play it on top of the block.
- `{Size}SwingBlocked` / `PunchBlocked` are for the **attacker** when their hit lands on a block.
  Stop the swing and play this.

The movements are generic: no hand poses, no object-specific bones. So the same animation works
for any object of that size class.

## Attaching objects to the hands

The animations don't include the object. Every animation in a size class uses the **same grip**, so
one weld per object works for the pickup, hold, throw, swing and block. Weld the object to the
**Right Arm** (`Part0 = Right Arm`, `Part1 = object`, `C1 = CFrame.identity`). `h` is the distance
from the hand(s) to the object's centre (about half its height).

| Size | `Weld.C0` |
|---|---|
| Small (1 hand) | `CFrame.new(0, -1 - h, 0)` |
| Medium (1 hand) | `CFrame.new(0, -1 - h, 0)` |
| Large (2 hands) | `CFrame.new(-1.84, -0.40, 0) * CFrame.Angles(math.pi, 0, math.rad(18)) * CFrame.new(0, h, 0)` |
| Huge (2 hands) | `CFrame.new(-1.89, 0.01, 0) * CFrame.Angles(math.pi, 0, math.rad(28)) * CFrame.new(0, h, 0)` |

The two-hand grips put the object centred between both hands, upright when it's held overhead
(that's where the GIFs show it). Turn a large/huge object 90° around Y if it should sit lengthwise.
Weld on the `Grab` marker (for Large/Huge, tween the weld in over the lift), unweld on `Release` and
give the object velocity.

## Markers → sound effects

| Marker | Where | Sound to use |
|---|---|---|
| `Footstep`, `Step` | Walk, Sprint, CrouchWalk, WallClimb, WallRun | Light footstep (concrete/grass by floor material) |
| `Jump`, `Kick` (wall), `Land`, `Impact` | Jump, WallJump, Land, LandHeavy | Cloth whoosh, landing thud; heavy ground impact + debris for LandHeavy |
| `Slide`, `Roll` | SlideStart, Roll, LandRoll | Sliding scrape loop, body roll/thump |
| `Grab`, `Push`, `Plant` | LedgeClimb, Vault | Hand slap on stone, effort grunt |
| `Swing` / `Windup` | all attacks and throws | Whoosh: short and airy for Small, deep "vwoom" for Large/Huge |
| `Hit` | punches, swings | Punch impact (Small), wood crash (Medium), metal crunch (Large), huge metal + glass crash (Huge) |
| `Release` | throws | Whoosh + grunt |
| `Blocked`, `Impact` (BlockHit) | SwingBlocked, PunchBlocked, BlockHit | Dull "thunk" / metal clang |
| `Weakening`, `Critical` | Blocks | Creaking metal / straining grunt |
| `Break` | BlockBreak | Glass-shatter-style guard break, crunch |

### SFX packs that fit this style

- **Roblox Creator Store (Toolbox → Audio).** Roblox has added 100,000+ sound effects from licensed
  partners such as Pro Sound Effects, all free to use in your experiences. You don't need to upload
  anything, which avoids the monthly audio upload limits. Useful searches: *"punch impact", "body
  hit", "whoosh swing", "metal crash", "car crash", "debris", "footstep concrete", "body fall",
  "cloth movement"*. See [Audio assets](https://create.roblox.com/docs/en-us/audio/assets).
- **Kenney – Impact Sounds** (130+ files, CC0, free, no credit needed): footsteps, thuds,
  plate/metal hits. [kenney.nl/assets/impact-sounds](https://kenney.nl/assets/impact-sounds)
- **Sonniss GDC Game Audio Bundles** (free, royalty-free, no attribution; many GB going back to
  2015): best for the Large/Huge crashes, metal, debris and big whooshes.
  [sonniss.com/gameaudiogdc](https://sonniss.com/gameaudiogdc)
- **Floraphonic – Punch Whoosh & Impact** (~$4-5, 50 sounds: 20 whooshes, 20 impacts of different
  strength, 10 combined). Very close to the punchy anime-style hits.
  [itch.io](https://floraphonic.itch.io/punching-whoosh-and-impact-sound-effects)
- **Mixkit – Punch sound effects** (free, Mixkit license).
  [mixkit.co/free-sound-effects/punch](https://mixkit.co/free-sound-effects/punch/)
- **CrashMetal 01** on Fab (metal clang / crash / debris / slam sets): for car/train hits and block
  breaks. [fab.com listing](https://www.fab.com/listings/2e8f32d5-e3c7-4230-9d5f-c960de40d812)

If you upload your own audio, Roblox limits how many uploads you get per month (higher once you
verify your ID). Using the Creator Store sounds first saves uploads for the few you really need.

## Changing an animation

Tell me the animation name and what to change, e.g. *"Sprint: less lean, arms tighter"* or
*"HugeThrow: hold the dip longer"*. Everything is generated from `source/anims/*.py`:

```bash
python3 source/build.py                # re-export every .rbxmx + render every GIF
python3 source/build.py --only Sprint  # just one GIF
python3 source/make_docs.py            # refresh ANIMATIONS.md
```

(Python 3 with numpy and Pillow.)
