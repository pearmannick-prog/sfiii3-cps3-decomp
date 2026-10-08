// Arcade (CPS-3, 990512) versions of CPU AI routines that differ from the PS2 build.
// Each function overrides the one of the same name in 3s-decomp's Source/Game/pass16.c.
// Written from the arcade disassembly; address of the arcade function is given per routine.
// Button/lever masks use the arcade bit layout (see README, "button-mask remap").
#include "sf33rd/Source/Game/pass16.h"
#include "common.h"
#include "sf33rd/Source/Game/Com_Sub.h"
#include "sf33rd/Source/Game/workuser.h"

// 0x06053D5C  (PS2: single case, Walk only)
void Passive16_0031(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Search_Back_Term(wk, 0x40, 6, 0x6C);
        break;

    case 1:
        Walk(wk, 1, 0x20, 1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x060543DE  (PS2: Command_Attack(wk, 8, 0x1E, 8, -1))
void Passive16_0053(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Lever_Attack(wk, 8, 0, 0x202);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x06054690  (PS2: Lever_Attack(wk, 8, 0, 0x400))
void Passive16_0064(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 8, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x06055540  (PS2: Jump_Command_Attack_Term(wk, 8, 0x2E, 8, -1, ...))
void Passive16_0104(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Command_Attack(wk, 8, 0x1C, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x06055572  (PS2: Jump_Command_Attack_Term(wk, 8, 0x2E, 9, -1, ...))
void Passive16_0105(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Command_Attack(wk, 8, 0x1C, 9, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x060555C8  (PS2: Jump_Command_Attack_Term(wk, 8, 0x2E, 0xA, -1, ...))
void Passive16_0106(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Command_Attack(wk, 8, 0x1C, 0xA, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x06055EC4  (PS2: Jump_Command_Attack_Term(wk, 8, 0x2E, 0xA, 0x700, ...))
void Passive16_0139(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Jump_Attack(wk, 0xC, 0xA, 0x42, 2);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}
