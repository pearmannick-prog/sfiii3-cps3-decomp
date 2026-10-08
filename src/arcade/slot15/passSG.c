// CPU AI routines of arcade character slot 15 (CPS-3, 990512). The PS2 build has no such slot.
// The slot has its own dispatcher and its own table of 249 routines; they mirror the first 249 routines of
// pass14.c (Akuma, slot 14). Only the routines whose content differs from Akuma's arcade routine
// are listed here; every other PassiveSG_NNNN equals the arcade Passive14_NNNN.
// Generated with tools/lift_patterns.py; notes compare against the PS2 routine of the same number.

// 0x0604CD76
//   PS2 Passive14_0005 case 2: Lever_Attack arg3 0x110 -> 0x40
void PassiveSG_0005(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 1:
        EM_Term(wk, -1, -0x7FF8, 6, 1, -1);
        break;

    case 2:
        Lever_Attack(wk, 8, 0, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604CDCA
//   PS2 Passive14_0006 case 2: Lever_Attack arg2 1 -> 0
//   PS2 Passive14_0006 case 2: Lever_Attack arg3 0x110 -> 0x200
void PassiveSG_0006(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 1:
        EM_Term(wk, -1, -0x7FF8, 6, 1, -1);
        break;

    case 2:
        Lever_Attack(wk, 8, 0, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604D666
//   PS2 Passive14_0025 case 3: Lever_Attack arg3 0x110 -> 0x40
void PassiveSG_0025(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Command_Attack(wk, 8, 0, -1, -1);
        break;

    case 1:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 2:
        EM_Term(wk, -1, -0x7FF8, 6, 1, -1);
        break;

    case 3:
        Lever_Attack(wk, 8, 0, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604D6D6
//   PS2 Passive14_0026 case 3: Lever_Attack arg2 1 -> 0
//   PS2 Passive14_0026 case 3: Lever_Attack arg3 0x110 -> 0x200
void PassiveSG_0026(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Command_Attack(wk, 8, 0, -1, -1);
        break;

    case 1:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 2:
        EM_Term(wk, -1, -0x7FF8, 6, 1, -1);
        break;

    case 3:
        Lever_Attack(wk, 8, 0, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604F156
//   PS2 Passive14_0094 case 0: Normal_Attack arg1 9 -> 8
//   PS2 Passive14_0094 case 0: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Passive14_0094 case 1: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Passive14_0094 case 2: Normal_Attack arg2 0x202 -> 0x102
void PassiveSG_0094(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 1:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x102);
        break;

    case 3:
        Command_Attack(wk, 8, 0x1F, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604FB90
//   PS2 Passive14_0129 case 1: Lever_Attack arg3 0x110 -> 0x40
void PassiveSG_0129(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 1:
        Lever_Attack(wk, 8, 0, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604FBDC
//   PS2 Passive14_0130 case 1: Lever_Attack arg2 1 -> 0
//   PS2 Passive14_0130 case 1: Lever_Attack arg3 0x110 -> 0x200
void PassiveSG_0130(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 1:
        Lever_Attack(wk, 8, 0, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604FE20
//   PS2 Passive14_0140 case 0: J_Command_Attack arg1 9 -> 0xA
void PassiveSG_0140(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        J_Command_Attack(wk, 0xA, 0x20, 8, -1);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x1E, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604FE68
//   PS2 Passive14_0141 case 0: J_Command_Attack arg1 9 -> 0xA
void PassiveSG_0141(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        J_Command_Attack(wk, 0xA, 0x20, 9, -1);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x1E, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0604FEB0
//   PS2 Passive14_0142 case 0: J_Command_Attack arg1 9 -> 0xA
void PassiveSG_0142(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        J_Command_Attack(wk, 0xA, 0x20, 0xA, -1);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x1E, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}
