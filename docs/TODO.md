# TODO: hardware ideas not yet built

What might come next for the plastic, and what has already been measured for it. The enclosure's
own open risks stay where they are, in
[`hardware/enclosure/README.md`](../hardware/enclosure/README.md) under "Open risks" - this file is
for things that do not exist yet.

Nothing here has been printed, modelled or committed to. Numbers below were read off Pollen's mesh
(`cad/reachy-mini/reachy_mini_full.stl`) on 2026-09-22; anything not measured says so.


## 1. A hat

Asked for 2026-09-22: something with more character on the head, that does not get in the way of the
antennas or the microphones.

### What the head gives you (measured, robot frame R)

The head runs from the body's rim at **z 185** up to a crown that closes at about **z 252**. It is
wider than it is deep: roughly **94 mm front-to-back** (x +43.6 at the face, -52.3 at the back) and
**150 mm side-to-side** (|Y| up to 75.0). The face is flat-ish in X from z 190 to 226 and then
curves away.

| z | max radius | x front | x back | max \|Y\| |
|---|---|---|---|---|
| 190 | 77.4 | 42.3 | -50.8 | 74.9 |
| 200 | 77.5 | 43.6 | -51.5 | 75.0 |
| 210 | 77.1 | 43.0 | -51.3 | 75.0 |
| **220** | **79.7** | 41.5 | -52.3 | 74.4 |
| 230 | 78.2 | 39.9 | -50.8 | 72.8 |
| 240 | 70.0 | 36.9 | -38.4 | 67.3 |
| 245 | 73.6 | 33.5 | -45.0 | 60.5 |
| 250 | 42.9 | 24.2 | -7.5 | 39.6 |

**The bulge at z 220-225 is real but shallow, and it is not the belly.** The collar works because
the body's widest ring has 3-4 mm of taper on both sides of it; here there is only **2.3 mm of
taper below** (77.4 at z 190 against 79.7 at z 220) against a strong narrowing above. So a band on
the bulge is held well against riding **up** and hardly at all against creeping **down** - it would
need friction (TPU), a lip, or something hooked over the crown. *(Said the other way round in chat
first; the table is what to believe.)*

### The antennas are the hard constraint

Two stalks, |Y| **52.6..62.0**, x **-44.8..-34.9**, rising from about **z 258**; the tip at z 390 is
only 3.4 x 3.5 mm, at x -27..-24. They emerge **behind** the crown.

Two things make them worse than they look:

- **The CAD only has the zero pose.** The full mesh has almost no triangles between z 290 and 365,
  so even the static stalk is barely modelled - base and tip, little between.
- **The sweep is enormous.** The sibling repo's CLAUDE.md records that in the sleep pose the
  antennas pass about **14 mm outside the collar top**, and the collar top is z 124. So they travel
  from vertical (z 390) all the way down alongside the head. Any crown, and any band closed at the
  back, is somewhere in that arc.

**Nothing should be designed against the zero pose.** Drive the antennas through their range, record
the envelope, and design against that.

### Settle these two before covering anything

1. **Where the microphone ports are.** The XVF3800 array is in the head (`head_mic_3dprint` on the
   `xl_330` link) and direction-of-arrival is load-bearing - it is how she turns to whoever spoke.
   Not visible in the mesh. Cheap test: tape a blank ring or cap blank on, play a sound from a known
   bearing, and compare `GET /api/state/doa` with and without it. That is a fact rather than a guess.
2. **The antenna sweep**, as above.

Also unmeasured: **what the Stewart platform will carry.** Six small servos, and a hat is mass at the
end of the lever. There is no payload figure anywhere in either repo. Keep it light and low, and say
so rather than assuming.

### Options, by how much they risk

**Low risk - nothing over the mics, nothing in the antenna arc**

| Idea | Why it is safe | Notes |
|---|---|---|
| **Hatband on the bulge** | A **C**, open at the back, so drooping antennas clear it. No crown. | On its own it reads as a sweatband. Its real job is to be the mount for everything below. Needs the creep problem solved (see above). |
| **Carpenter's pencil behind the ear** | A flat pencil tucked into that band, nothing else. | The most in-character object this robot could own, and about 2 g. |
| **Flat cap, worn forward** | Crown only on the front half (x +40 back to about -10); the antennas emerge behind it whatever they do. | Maximum workwear, minimum risk. Check the peak against the camera's upward field of view. |
| **Visor** | Brim and band, no crown at all. | Green translucent eyeshade, or matte for the workshop. Weighs nothing. |
| **Ear defenders, pushed up or slung round the neck** | Funny *because* they are not covering anything. | The "just clocked off" look. |

**Higher risk - charming, but only after the microphone test**

| Idea | What it costs |
|---|---|
| **Beanie with antenna slots** | Antennas poke through like ears. The crown covers whatever is on top, and the slots must fit the whole sweep, not the zero pose. |
| **Hard hat** | Perfect with dungarees. Tallest and heaviest option, all of it cantilevered on the platform. |
| **Bandana knotted at the back** | The knot lands exactly where the antennas live. |

### The one worth pursuing

**Make the band the product and the hats swappable.** Solve the hard part once - a light C-band that
stays put on the bulge, open at the rear, verified against DOA and against a measured antenna sweep -
then give it a dovetail or peg so toppers clip on: flat cap, visor, pencil, flower, party hat, beret,
Santa hat in December. The risky interface is tested a single time; after that each new hat is a
twenty-minute print with no new risk to the antennas, the microphones or the servos.

Two things to carry into whichever one wins:

- **Light and low.** See the unmeasured payload above.
- **Its own colour.** The AMS height-range trick already documented for the cuff and waistband
  (enclosure README, "Printing") would let a brown cap read as a separate garment rather than as
  more enclosure. The dungarees' own language - dashed stitching, teardrop buttons - is what will
  make it look designed rather than bolted on.
