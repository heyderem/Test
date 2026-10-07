# Animation previews

Every GIF is rendered from the exact keyframes in the `.rbxmx` files on a classic R6 rig. Objects, sparks and dust are preview-only (they are not part of the animation). Blue ticks on the timeline are markers; the banner shows a marker as it fires.

Want something changed? Quote the animation name and what to change (e.g. *"MediumThrow: bigger knee lift, release later"*).

| Section | Animations |
|---|---|
| [Movement](#movement) | 21 |
| [Hit Reactions](#hit-reactions) | 2 |
| [Combat](#combat) | 10 |
| [Objects/Small](#objectssmall) | 11 |
| [Objects/Medium](#objectsmedium) | 11 |
| [Objects/Large](#objectslarge) | 11 |
| [Objects/Huge](#objectshuge) | 11 |

## Movement

Remakes of the movement in your reference video, plus walk / jump / landing / ledge pieces in the same style.

### Idle

`Idle · 2.40s · looped`  
Relaxed breathing idle, arms hanging slightly away from the body like the video.  

![Idle](previews/Idle.gif)

### Walk

`Movement · 0.80s · looped`  
Walk cycle (0.8 s). Play speed = WalkSpeed / 16.  
Markers: `Footstep` 0.00s, `Footstep` 0.40s

![Walk](previews/Walk.gif)

### Sprint

`Movement · 0.56s · looped`  
Big arm-pumping sprint with forward lean (0.56 s cycle). Back arm flares out like the video.  
Markers: `Footstep` 0.02s, `Footstep` 0.30s

![Sprint](previews/Sprint.gif)

### CrouchIdle

`Movement · 2.00s · looped`  
Low crouch, head down, arms hanging forward (video crouch).  

![CrouchIdle](previews/CrouchIdle.gif)

### CrouchWalk

`Movement · 1.00s · looped`  
Crouched waddle (1.0 s cycle). Play speed = crouch WalkSpeed / 8.  
Markers: `Footstep` 0.00s, `Footstep` 0.50s

![CrouchWalk](previews/CrouchWalk.gif)

### Jump

`Movement · 0.45s`  
Take-off: arms whip up and out, knee drives up. Holds into Fall.  
Markers: `Jump` 0.00s

![Jump](previews/Jump.gif)

### Fall

`Movement · 0.90s · looped`  
Free-fall: arms raised up and out, legs paddling (video fall pose).  

![Fall](previews/Fall.gif)

### Land

`Movement · 0.42s`  
Normal landing: quick knee-dip absorb, arms out for balance.  
Markers: `Land` 0.05s

![Land](previews/Land.gif)

### LandHeavy

`Action · 1.00s`  
Superhero landing from a big drop: fist to the floor, then rise.  
Markers: `Impact` 0.07s

![LandHeavy](previews/LandHeavy.gif)

### LandRoll

`Action · 0.86s`  
Landing from a high fall into a forward roll, then straight into a run (video).  
Markers: `Land` 0.05s, `Roll` 0.15s

![LandRoll](previews/LandRoll.gif)

### Roll

`Action · 0.78s`  
Dodge / forward shoulder roll from the video (arms spread as you come up).  
Markers: `Roll` 0.09s, `Recover` 0.60s

![Roll](previews/Roll.gif)

### SlideStart

`Action · 0.26s`  
Drop from a sprint into the feet-first slide. Chain into Slide (loop).  
Markers: `Slide` 0.08s

![SlideStart](previews/SlideStart.gif)

### Slide

`Movement · 0.60s · looped`  
Feet-first slide hold with a little ground shake (video slide pose).  

![Slide](previews/Slide.gif)

### SlideEnd

`Action · 0.40s`  
Pop back up out of the slide into a run.  
Markers: `Stand` 0.12s

![SlideEnd](previews/SlideEnd.gif)

### LedgeHang

`Movement · 1.60s · looped`  
Hanging from a ledge by both hands, legs swaying.  

![LedgeHang](previews/LedgeHang.gif)

### LedgeClimb

`Action · 0.75s`  
Pull-up and mantle over a ledge; arms fly out wide at the top (video climb). Tween the HumanoidRootPart up/forward ~0.05-0.5 s while it plays.  
Markers: `Grab` 0.00s, `Push` 0.25s, `Land` 0.55s

![LedgeClimb](previews/LedgeClimb.gif)

### WallClimb

`Movement · 0.48s · looped`  
Running straight up a wall: alternating high reaches and knee drives (video climb).  
Markers: `Step` 0.00s, `Step` 0.24s

![WallClimb](previews/WallClimb.gif)

### WallRunRight

`Movement · 0.50s · looped`  
Wall run with the wall on the right: body tilts away so the feet press the wall, outer arm pumps wide (video wall run).  
Markers: `Step` 0.00s, `Step` 0.25s

![WallRunRight](previews/WallRunRight.gif)

### WallRunLeft

`Movement · 0.50s · looped`  
Wall run with the wall on the left: body tilts away so the feet press the wall, outer arm pumps wide (video wall run).  
Markers: `Step` 0.00s, `Step` 0.25s

![WallRunLeft](previews/WallRunLeft.gif)

### WallJump

`Action · 0.50s`  
Tuck against the wall then explode off it (video wall kick).  
Markers: `Kick` 0.10s

![WallJump](previews/WallJump.gif)

### Vault

`Action · 0.62s`  
Speed vault over a waist-high wall: left hand plants, legs swing through to the side (video vault). Move the root up ~1.5 studs and forward while it plays.  
Markers: `Plant` 0.10s, `Land` 0.48s

![Vault](previews/Vault.gif)

## Hit Reactions

Getting hit (the flinch from the video and a heavier knock-back).

### HitReact

`Action3 · 0.50s`  
Light hit flinch from the video: arms jolt up and out, head snaps back.  
Markers: `Hit` 0.00s

![HitReact](previews/HitReact.gif)

### HitHeavy

`Action3 · 0.90s`  
Heavy hit: knocked back, stumbling steps, hunched recovery.  
Markers: `Hit` 0.00s, `Stumble` 0.26s

![HitHeavy](previews/HitHeavy.gif)

## Combat

Unarmed attacks. `_UB` = upper body only (plays on top of Walk/Sprint).

### Punch1

`Action2 · 0.36s`  
Combo hit 1 - quick lead-hand jab.  
Markers: `Swing` 0.05s, `Hit` 0.11s

![Punch1](previews/Punch1.gif)

### Punch2

`Action2 · 0.42s`  
Combo hit 2 - rear-hand cross with hip turn.  
Markers: `Swing` 0.07s, `Hit` 0.15s

![Punch2](previews/Punch2.gif)

### Punch3

`Action2 · 0.46s`  
Combo hit 3 - wide lead hook.  
Markers: `Swing` 0.08s, `Hit` 0.16s

![Punch3](previews/Punch3.gif)

### Punch4

`Action2 · 0.62s`  
Combo finisher - dipping rising uppercut (launcher).  
Markers: `Swing` 0.13s, `Hit` 0.22s

![Punch4](previews/Punch4.gif)

### Kick

`Action2 · 0.72s`  
Spinning-hip roundhouse kick.  
Markers: `Swing` 0.13s, `Hit` 0.26s

![Kick](previews/Kick.gif)

### HeavyPunch

`Action2 · 1.00s`  
Charged heavy punch: deep wind-up, lunging step, big follow-through.  
Markers: `Charge` 0.05s, `Swing` 0.38s, `Hit` 0.48s

![HeavyPunch](previews/HeavyPunch.gif)

### PunchBlocked

`Action3 · 0.55s`  
Your punch/kick hits a block: fist knocked back, recoil half-step, guard back up.  
Markers: `Blocked` 0.00s

![PunchBlocked](previews/PunchBlocked.gif)

### Punch1_UB

`Action2 · 0.36s · joints: Neck, Right Shoulder, Left Shoulder`  
Upper-body-only version of Punch1: plays on top of Walk/Sprint (legs keep running).  
Markers: `Swing` 0.05s, `Hit` 0.11s

![Punch1_UB](previews/Punch1_UB.gif)

### Punch2_UB

`Action2 · 0.42s · joints: Neck, Right Shoulder, Left Shoulder`  
Upper-body-only version of Punch2: plays on top of Walk/Sprint (legs keep running).  
Markers: `Swing` 0.07s, `Hit` 0.15s

![Punch2_UB](previews/Punch2_UB.gif)

### Punch3_UB

`Action2 · 0.46s · joints: Neck, Right Shoulder, Left Shoulder`  
Upper-body-only version of Punch3: plays on top of Walk/Sprint (legs keep running).  
Markers: `Swing` 0.08s, `Hit` 0.16s

![Punch3_UB](previews/Punch3_UB.gif)

## Objects/Small

Rocks, cans, bricks... **one hand, light and quick.**

### SmallPickup

`Action2 · 0.55s`  
Quick one-hand scoop of a small object.  
Markers: `Grab` 0.22s

![SmallPickup](previews/SmallPickup.gif)

### SmallHold

`Action · 1.60s · looped · joints: Right Shoulder`  
Carry a small object in the right hand. Only the right arm is animated, so the other arm keeps swinging with Walk/Sprint.  

![SmallHold](previews/SmallHold.gif)

### SmallThrow

`Action2 · 0.50s`  
Light one-hand flick throw.  
Markers: `Windup` 0.02s, `Release` 0.20s

![SmallThrow](previews/SmallThrow.gif)

### SmallThrow_UB

`Action2 · 0.50s · joints: Neck, Right Shoulder, Left Shoulder`  
Light one-hand flick throw. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Windup` 0.02s, `Release` 0.20s

![SmallThrow_UB](previews/SmallThrow_UB.gif)

### SmallSwing

`Action2 · 0.45s`  
Fast overhand smack with a small object.  
Markers: `Swing` 0.10s, `Hit` 0.18s

![SmallSwing](previews/SmallSwing.gif)

### SmallSwing_UB

`Action2 · 0.45s · joints: Neck, Right Shoulder, Left Shoulder`  
Fast overhand smack with a small object. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Swing` 0.10s, `Hit` 0.18s

![SmallSwing_UB](previews/SmallSwing_UB.gif)

### SmallSwingBlocked

`Action3 · 0.50s`  
Small-object hit bounces off a block: arm knocked back, half-step back.  
Markers: `Blocked` 0.00s

![SmallSwingBlocked](previews/SmallSwingBlocked.gif)

### SmallBlock

`Action2 · 4.00s`  
Forearm guard with the small object across the face; trembles and sags over 4 s.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![SmallBlock](previews/SmallBlock.gif)

### SmallBlock_UB

`Action2 · 4.00s · joints: Neck, Right Shoulder, Left Shoulder`  
Forearm guard with the small object across the face; trembles and sags over 4 s. Upper-body only: plays over Walk/Sprint.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![SmallBlock_UB](previews/SmallBlock_UB.gif)

### SmallBlockBreak

`Action3 · 0.72s`  
Guard knocked wide open, stumble back.  
Markers: `Break` 0.03s

![SmallBlockBreak](previews/SmallBlockBreak.gif)

### SmallBlockHit

`Action3 · 0.40s`  
Small block takes a hit: guard jolts back and the feet slide, then re-sets. Play over SmallBlock (it starts and ends in the block pose).  
Markers: `Impact` 0.00s

![SmallBlockHit](previews/SmallBlockHit.gif)

## Objects/Medium

Crates, barrels, chairs... **one hand, big dramatic wind-ups.**

### MediumPickup

`Action2 · 0.80s`  
Bend, grab the object one-handed and swing it up overhead.  
Markers: `Grab` 0.30s

![MediumPickup](previews/MediumPickup.gif)

### MediumHold

`Action · 1.60s · looped · joints: Right Shoulder`  
Carry a medium object raised one-handed over the shoulder. Only the right arm is animated, so the other arm keeps the Walk/Sprint swing.  

![MediumHold](previews/MediumHold.gif)

### MediumThrow

`Action2 · 0.86s`  
Pitcher-style one-hand throw: knee lift, big stride, whip release.  
Markers: `Windup` 0.05s, `Release` 0.46s

![MediumThrow](previews/MediumThrow.gif)

### MediumThrow_UB

`Action2 · 0.86s · joints: Neck, Right Shoulder, Left Shoulder`  
Pitcher-style one-hand throw: knee lift, big stride, whip release. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Windup` 0.05s, `Release` 0.46s

![MediumThrow_UB](previews/MediumThrow_UB.gif)

### MediumSwing

`Action2 · 0.80s`  
One-handed overhead smash with the object.  
Markers: `Swing` 0.27s, `Hit` 0.36s

![MediumSwing](previews/MediumSwing.gif)

### MediumSwing_UB

`Action2 · 0.80s · joints: Neck, Right Shoulder, Left Shoulder`  
One-handed overhead smash with the object. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Swing` 0.27s, `Hit` 0.36s

![MediumSwing_UB](previews/MediumSwing_UB.gif)

### MediumSwingBlocked

`Action3 · 0.66s`  
Medium smash slams into a block and rebounds overhead; stagger back.  
Markers: `Blocked` 0.00s

![MediumSwingBlocked](previews/MediumSwingBlocked.gif)

### MediumBlock

`Action2 · 4.00s`  
Object held out front as a shield, off-hand bracing; trembles, sags and gets pushed back over 4 s.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![MediumBlock](previews/MediumBlock.gif)

### MediumBlock_UB

`Action2 · 4.00s · joints: Neck, Right Shoulder, Left Shoulder`  
Object held out front as a shield, off-hand bracing; trembles, sags and gets pushed back over 4 s. Upper-body only: plays over Walk/Sprint.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![MediumBlock_UB](previews/MediumBlock_UB.gif)

### MediumBlockBreak

`Action3 · 0.86s`  
Shield-object knocked up and away, big stumble back.  
Markers: `Break` 0.03s

![MediumBlockBreak](previews/MediumBlockBreak.gif)

### MediumBlockHit

`Action3 · 0.50s`  
Medium block takes a hit: guard jolts back and the feet slide, then re-sets. Play over MediumBlock (it starts and ends in the block pose).  
Markers: `Impact` 0.00s

![MediumBlockHit](previews/MediumBlockHit.gif)

## Objects/Large

Cars, boulders, dumpsters... **two hands, heavy impacts.**

### LargePickup

`Action2 · 1.10s`  
Deep squat, grip underneath, explosive two-hand lift to overhead.  
Markers: `Grab` 0.40s, `Settle` 0.86s

![LargePickup](previews/LargePickup.gif)

### LargeHold

`Action · 2.00s · looped · joints: Right Shoulder, Left Shoulder`  
Large object held overhead with both arms, straining. Arms only, so legs/torso come from Idle/Walk/Sprint.  

![LargeHold](previews/LargeHold.gif)

### LargeThrow

`Action2 · 1.10s`  
Two-hand overhead heave: arch back, step and launch with full-body follow-through.  
Markers: `Windup` 0.05s, `Release` 0.55s

![LargeThrow](previews/LargeThrow.gif)

### LargeThrow_UB

`Action2 · 1.10s · joints: Neck, Right Shoulder, Left Shoulder`  
Two-hand overhead heave: arch back, step and launch with full-body follow-through. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Windup` 0.05s, `Release` 0.55s

![LargeThrow_UB](previews/LargeThrow_UB.gif)

### LargeSwing

`Action2 · 1.00s`  
Two-handed overhead slam: rise, arch back, crash it into the ground.  
Markers: `Swing` 0.36s, `Hit` 0.50s

![LargeSwing](previews/LargeSwing.gif)

### LargeSwing_UB

`Action2 · 1.00s · joints: Neck, Right Shoulder, Left Shoulder`  
Two-handed overhead slam: rise, arch back, crash it into the ground. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Swing` 0.36s, `Hit` 0.50s

![LargeSwing_UB](previews/LargeSwing_UB.gif)

### LargeSwingBlocked

`Action3 · 0.90s`  
Slam stopped by a block: object bounces back overhead, heavy stagger.  
Markers: `Blocked` 0.00s

![LargeSwingBlocked](previews/LargeSwingBlocked.gif)

### LargeBlock

`Action2 · 4.00s`  
Object braced in front as a wall with both arms; pushed back, buckling and shaking over 4 s.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![LargeBlock](previews/LargeBlock.gif)

### LargeBlock_UB

`Action2 · 4.00s · joints: Neck, Right Shoulder, Left Shoulder`  
Object braced in front as a wall with both arms; pushed back, buckling and shaking over 4 s. Upper-body only: plays over Walk/Sprint.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![LargeBlock_UB](previews/LargeBlock_UB.gif)

### LargeBlockBreak

`Action3 · 1.10s`  
The weight crushes the guard: buckle down to a knee, then heave back up.  
Markers: `Break` 0.04s

![LargeBlockBreak](previews/LargeBlockBreak.gif)

### LargeBlockHit

`Action3 · 0.60s`  
Large block takes a hit: guard jolts back and the feet slide, then re-sets. Play over LargeBlock (it starts and ends in the block pose).  
Markers: `Impact` 0.00s

![LargeBlockHit](previews/LargeBlockHit.gif)

## Objects/Huge

Trains, planes, buses (2-3x your height)... **titan-sized two-hand moves.**

### HugePickup

`Action2 · 1.50s`  
Titan lift: squat under it, strain, then explode it up overhead.  
Markers: `Grab` 0.44s, `Lift` 0.84s, `Settle` 1.26s

![HugePickup](previews/HugePickup.gif)

### HugeHold

`Action · 2.40s · looped · joints: Right Shoulder, Left Shoulder`  
Train/plane balanced overhead, arms wide, slow heavy wobble. Arms only.  

![HugeHold](previews/HugeHold.gif)

### HugeThrow

`Action2 · 1.60s`  
Deep dip, arch and full-body launch of a vehicle-sized object.  
Markers: `Windup` 0.05s, `Release` 0.72s

![HugeThrow](previews/HugeThrow.gif)

### HugeThrow_UB

`Action2 · 1.60s · joints: Neck, Right Shoulder, Left Shoulder`  
Deep dip, arch and full-body launch of a vehicle-sized object. Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Windup` 0.05s, `Release` 0.72s

![HugeThrow_UB](previews/HugeThrow_UB.gif)

### HugeSwing

`Action2 · 1.70s`  
Grab it by one end and sweep it like a giant bat (wide horizontal arc).  
Markers: `Swing` 0.50s, `Hit` 0.68s

![HugeSwing](previews/HugeSwing.gif)

### HugeSwing_UB

`Action2 · 1.70s · joints: Neck, Right Shoulder, Left Shoulder`  
Grab it by one end and sweep it like a giant bat (wide horizontal arc). Upper-body only: plays over Walk/Sprint, legs keep running.  
Markers: `Swing` 0.50s, `Hit` 0.68s

![HugeSwing_UB](previews/HugeSwing_UB.gif)

### HugeSwingBlocked

`Action3 · 1.10s`  
The sweep is stopped dead by a block; the recoil spins you back and you stagger.  
Markers: `Blocked` 0.00s

![HugeSwingBlocked](previews/HugeSwingBlocked.gif)

### HugeBlock

`Action2 · 4.00s`  
Vehicle held up in front like a wall, legs wide; driven back and buckling over 4 s.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![HugeBlock](previews/HugeBlock.gif)

### HugeBlock_UB

`Action2 · 4.00s · joints: Neck, Right Shoulder, Left Shoulder`  
Vehicle held up in front like a wall, legs wide; driven back and buckling over 4 s. Upper-body only: plays over Walk/Sprint.  
Markers: `Raised` 0.16s, `Weakening` 1.60s, `Critical` 3.12s, `Exhausted` 3.95s

![HugeBlock_UB](previews/HugeBlock_UB.gif)

### HugeBlockBreak

`Action3 · 1.40s`  
Crushed under the weight: driven down low, shaking, then a last-second heave back up.  
Markers: `Break` 0.05s

![HugeBlockBreak](previews/HugeBlockBreak.gif)

### HugeBlockHit

`Action3 · 0.75s`  
Huge block takes a hit: guard jolts back and the feet slide, then re-sets. Play over HugeBlock (it starts and ends in the block pose).  
Markers: `Impact` 0.00s

![HugeBlockHit](previews/HugeBlockHit.gif)
