// CPU AI routines of arcade character slot 15 (CPS-3, 990512). The PS2 build has no such slot.
// The slot has its own dispatcher and its own table of 149 routines; they mirror the first 149 routines of
// active14.c (Akuma, slot 14). Only the routines whose content differs from Akuma's arcade routine
// are listed here; every other PatternSG_NNNN equals the arcade Pattern14_NNNN.
// Generated with tools/lift_patterns.py; notes compare against the PS2 routine of the same number.

// 0x0607A074
//   PS2 Pattern14_0022 case 0: J_Command_Attack arg1 9 -> 8
void PatternSG_0022(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x1E, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607A0BC
//   PS2 Pattern14_0023 case 0: J_Command_Attack arg1 9 -> 8
void PatternSG_0023(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        J_Command_Attack(wk, 8, 0x20, 9, -1);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x1E, 8, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607AF68
//   PS2 Pattern14_0058 case 1: Jump_Attack_Term arg4 0x400 -> 0x200
//   PS2 Pattern14_0058 case 1: Jump_Attack_Term arg8 0x400 -> 0x200
//   PS2 Pattern14_0058 case 2: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0058 case 2: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0058 case 3: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0058(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Attack_Term(wk, -0x7FA8, -0x7FC8, 9, 0x200, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 3:
        Normal_Attack(wk, 0xC, 0x102);
        break;

    case 4:
        Command_Attack(wk, 0xC, 0x1F, 0xA, -1);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607AFE8
//   PS2 Pattern14_0059 case 1: Jump_Attack_Term arg4 0x400 -> 0x200
//   PS2 Pattern14_0059 case 1: Jump_Attack_Term arg8 0x400 -> 0x200
//   PS2 Pattern14_0059 case 2: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0059 case 2: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0059 case 3: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0059(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Attack_Term(wk, -0x7FA8, -0x7FC8, 9, 0x200, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 3:
        Normal_Attack(wk, 0xC, 0x102);
        break;

    case 4:
        Command_Attack(wk, 0xC, 0x1F, 0xA, -1);
        break;

    case 5:
        Wait(wk, 1);
        break;

    case 6:
        SA_Term(wk, 0x2F, 0x30, 0x31, 0x7F);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607B0B4
//   PS2 Pattern14_0060 case 1: Jump_Attack_Term arg4 0x400 -> 0x200
//   PS2 Pattern14_0060 case 1: Jump_Attack_Term arg8 0x400 -> 0x200
//   PS2 Pattern14_0060 case 2: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0060 case 2: Normal_Attack arg2 0x220 -> 0x120
void PatternSG_0060(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Attack_Term(wk, -0x7FA8, -0x7FC8, 9, 0x200, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 3:
        SA_Term(wk, 0x32, 0xFFFFFFFF, 0xFFFFFFFF, 0xBF);
        break;

    case 4:
        Com_Random_Select(wk, 6, 0x77, 0x77, 0x78, 0x79, 2);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607B218
//   PS2 Pattern14_0062 case 1: Jump_Attack_Term arg4 0x400 -> 0x200
//   PS2 Pattern14_0062 case 1: Jump_Attack_Term arg8 0x400 -> 0x200
//   PS2 Pattern14_0062 case 2: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0062 case 2: Normal_Attack arg2 0x220 -> 0x120
void PatternSG_0062(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Attack_Term(wk, -0x7FA8, -0x7FC8, 9, 0x200, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 3:
        SA_Term(wk, 0x34, 0x34, 0x34, 0x7F);
        break;

    case 4:
        Com_Random_Select(wk, 6, 0x77, 0x77, 0x78, 0x79, 2);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607B2D6
//   PS2 Pattern14_0063 case 1: Jump_Command_Attack_Term arg10 0x400 -> 0x200
//   PS2 Pattern14_0063 case 2: Normal_Attack arg2 0x202 -> 0x102
//   PS2 Pattern14_0063 case 3: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0063 case 3: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0063 case 4: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0063(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Command_Attack_Term(wk, 8, 0x2E, 8, -1, -1, 0x34, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x102);
        break;

    case 3:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 4:
        Normal_Attack(wk, 0xC, 0x102);
        break;

    case 5:
        Command_Attack(wk, 0xC, 0x1F, 0xA, -1);
        break;

    case 6:
        Wait(wk, 1);
        break;

    case 7:
        SA_Term(wk, 0x2F, 0x30, 0x31, 0x7F);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607B3CC
//   PS2 Pattern14_0064 case 1: Jump_Command_Attack_Term arg10 0x400 -> 0x200
//   PS2 Pattern14_0064 case 3: Normal_Attack arg2 0x202 -> 0x102
//   PS2 Pattern14_0064 case 4: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0064 case 4: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0064 case 5: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0064(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Approach_Walk(wk, 0xBF, 2);
        break;

    case 1:
        Jump_Command_Attack_Term(wk, 8, 0x2E, 8, -1, -1, 0x34, 0, -0x7F80, -1, 0x200);
        break;

    case 2:
        Lever_Attack(wk, 9, 0, 0x20);
        break;

    case 3:
        Normal_Attack(wk, 9, 0x102);
        break;

    case 4:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 5:
        Normal_Attack(wk, 0xC, 0x102);
        break;

    case 6:
        Command_Attack(wk, 0xC, 0x1F, 0xA, -1);
        break;

    case 7:
        Wait(wk, 1);
        break;

    case 8:
        SA_Term(wk, 0x2F, 0x30, 0x31, 0x7F);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BB9C
//   PS2 Pattern14_0084 case 0: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0084 case 1: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0084 case 1: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0084 case 2: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0084 case 4: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0084 case 6: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0084 case 7: Normal_Attack arg2 0x400 -> 0x200
void PatternSG_0084(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 1:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 3:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 4:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 5:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 6:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 7:
        Normal_Attack(wk, 8, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BC2E
//   PS2 Pattern14_0085 case 0: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0085 case 0: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0085 case 1: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0085 case 2: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0085(PLW* wk) {
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
        Normal_Attack(wk, 8, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BC96
//   PS2 Pattern14_0086 case 1: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0086 case 1: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0086 case 2: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0086 case 3: Normal_Attack arg2 0x202 -> 0x102
void PatternSG_0086(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x12);
        break;

    case 1:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 3:
        Normal_Attack(wk, 8, 0x102);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BCE4
//   PS2 Pattern14_0087 case 0: Normal_Attack arg1 9 -> 8
//   PS2 Pattern14_0087 case 0: Normal_Attack arg2 0x220 -> 0x120
//   PS2 Pattern14_0087 case 1: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0087 case 3: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0087 case 4: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0087 case 7: Normal_Attack arg2 0x402 -> 0x202
void PatternSG_0087(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 8, 0x120);
        break;

    case 1:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 2:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 3:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 4:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 5:
        Lever_On(wk, 1, 2);
        break;

    case 6:
        Wait(wk, 2);
        break;

    case 7:
        Normal_Attack(wk, 8, 0x202);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BD94
//   PS2 Pattern14_0088 case 0: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0088 case 3: Lever_Attack arg3 0x110 -> 0x40
void PatternSG_0088(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 1:
        SA_Term(wk, 0x34, 0x34, 0x34, 0x7F);
        break;

    case 2:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 3:
        Lever_Attack(wk, 8, 0, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BDF2
//   PS2 Pattern14_0089 case 0: Normal_Attack arg2 0x100 -> 0x80
//   PS2 Pattern14_0089 case 3: Lever_Attack arg2 1 -> 0
//   PS2 Pattern14_0089 case 3: Lever_Attack arg3 0x110 -> 0x200
void PatternSG_0089(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x80);
        break;

    case 1:
        SA_Term(wk, 0x34, 0x34, 0x34, 0x7F);
        break;

    case 2:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 3:
        Lever_Attack(wk, 8, 0, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BE78
//   PS2 Pattern14_0090 case 0: Normal_Attack arg2 0x100 -> 0x80
//   PS2 Pattern14_0090 case 2: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0090 case 5: Lever_Attack arg3 0x110 -> 0x40
void PatternSG_0090(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x80);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 3:
        SA_Term(wk, 0x34, 0x34, 0x34, 0x7F);
        break;

    case 4:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 5:
        Lever_Attack(wk, 8, 0, 0x40);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}

// 0x0607BEFA
//   PS2 Pattern14_0091 case 0: Normal_Attack arg2 0x100 -> 0x80
//   PS2 Pattern14_0091 case 2: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0091 case 4: Normal_Attack arg2 0x102 -> 0x82
//   PS2 Pattern14_0091 case 7: Lever_Attack arg2 1 -> 0
//   PS2 Pattern14_0091 case 7: Lever_Attack arg3 0x110 -> 0x200
void PatternSG_0091(PLW* wk) {
    switch (CP_Index[wk->wu.id][0]) {
    case 0:
        Normal_Attack(wk, 9, 0x80);
        break;

    case 1:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 2:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 3:
        J_Command_Attack(wk, 8, 0x20, 8, -1);
        break;

    case 4:
        Normal_Attack(wk, 9, 0x82);
        break;

    case 5:
        SA_Term(wk, 0x34, 0x34, 0x34, 0x7F);
        break;

    case 6:
        Approach_Walk(wk, 0x10, 2);
        break;

    case 7:
        Lever_Attack(wk, 8, 0, 0x200);
        break;

    default:
        End_Pattern(wk);
        break;
    }
}
