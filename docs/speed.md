# Game speed on the arcade board (990512)

Speed is the main goal for builds of this project: they should run at the speed of a real CPS-3 board,
which no port so far has matched.

## How the program paces itself (read from the code)

All of this is static reading of the 990512 program. Nothing here has been measured on hardware.

- **Vertical blank interrupt** (vector 70, handler `0x06000528`, acknowledged at `0x05100000`): sets the
  flag `0x02007F0A`, adds one to the frame counter `0x02007F00`, reads inputs, runs sound and video
  upkeep, and in the normal mode calls `task_tick` (`0x0600094C`).
- **Tasks**: 8 slots of 64 bytes at `0x0200D794`. Status byte: 0 free, 1 sleeping, 2 ready, 3 running,
  5 waiting with no timer. `task_tick` counts down the timer of every sleeping task and makes it ready at 0.
  Only sleeping tasks are counted down, so a task that is still running when the interrupt arrives
  gets nothing from that frame.
- **Scheduler** (`0x06000840`, the idle loop): runs ready tasks in slot order and starts again from slot 0
  whenever a new frame interrupt has arrived.
- **`task_sleep(n)`** (`0x06000D28`): marks the running task sleeping for `n` frames and switches away.
- **`Game_Task`** (`0x06094D78`): an endless loop of *one* game step (`Main_Jmp_Tbl[G_No[0]]`, then two
  more calls), then `task_sleep(1)`. Unlike the PS2 version there is no catch-up loop (PS2 runs
  `Process_Counter` steps per frame).

Consequence: the game advances at most one step per frame, and the step after one that overruns
the frame is delayed by a whole frame. When the work of all tasks, plus the interrupt handler, does not
fit in one frame, the game slows down; it never skips ahead to make up. The average game speed is
therefore the board's refresh rate times the share of frames that finish in time, and that share
depends on what is on screen. This fits Iron Galaxy's statement that arcade speed varies by stage and
character.

Not yet read: the meaning of modes 1-3 of `0x02007F09` (mode 2 only counts down on frames where
`counter & mask(0x02007F04)` is 0, which looks like a slow-motion or test setting).

## Implications

- The rebuilt ROM is the original code, so on a real board it reproduces this exactly.
- C replacements compiled with another compiler run at a different speed and can move the overrun frames;
  builds meant to play like the arcade keep original code until a function matches byte for byte.
- An emulator or native port reproduces arcade speed only if it reproduces when the work overruns a frame.
  A single lower refresh rate (below) is an average for one scene.

## Reference measurements

| Source | Scene | Method | Result | Notes |
|---|---|---|---|---|
| [YouTube qPEU6ZPb9Ug](https://www.youtube.com/watch?v=qPEU6ZPb9Ug) | one stage (Chun-Li in view) | FBNeo refresh adjusted until it lined up with camera footage of a cabinet | 59.266666 Hz effective vs 59.599491 Hz refresh: about 1 frame in 180 repeated | camera footage, one scene, matched by eye |

Refresh rate: 59.599491 Hz is the commonly cited value and the one MAME uses; MAME's CPS-3 timing was
originally a guess ([MAMETesters #2110](https://mametesters.org/view.php?id=2110)). A measurement on a
real board is still needed.
