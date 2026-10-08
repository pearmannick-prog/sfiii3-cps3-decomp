// Arcade (CPS-3, 990512) versions of routines in Source/Game/Ck_Pass.c, written by reading the arcade code.
// These are the per-matchup CPU checks. Everything else in the file agrees with PS2 on calls and arguments.
#include "sf33rd/Source/Game/Ck_Pass.h"
#include "common.h"

// Against Makoto, PS2 adds one more Check_Special_Technique call to each of the six functions below
// (technique 14 or 25, range 24, pattern 95). The arcade build has none of them.

// 0x06014090  (PS2: Check_Special_Technique(wk, em, 14, 24, 95, -1, -1))
s32 VS_MAKOTO_AS(PLW* wk) {
    return 0;
}

// 0x060148C6  (PS2: Check_Special_Technique(wk, em, 25, 24, 95, 1, -1))
s32 VS_MAKOTO_A(PLW* wk) {
    return 0;
}

// 0x060150C4
s32 VS_MAKOTO_BS(PLW* wk) {
    WORK* em = (WORK*)wk->wu.target_adrs;

    if (Check_Special_Technique(wk, em, 8, 8, 92, -1, -1)) {
        return 1;
    }

    return 0;
}

// 0x06015A32
s32 VS_MAKOTO_B(PLW* wk) {
    WORK* em = (WORK*)wk->wu.target_adrs;

    if (Check_Special_Technique(wk, em, 8, 8, 92, 1, -1)) {
        return 1;
    }

    return 0;
}

// 0x0601622E
s32 VS_MAKOTO_CS(PLW* wk) {
    WORK* em = (WORK*)wk->wu.target_adrs;

    if (Check_Special_Technique(wk, em, 8, 8, 92, -1, -1)) {
        return 1;
    }

    return 0;
}

// 0x06016ADA
s32 VS_MAKOTO_C(PLW* wk) {
    WORK* em = (WORK*)wk->wu.target_adrs;

    if (Check_Special_Technique(wk, em, 8, 8, 92, 1, -1)) {
        return 1;
    }

    return 0;
}

// 0x0601674A  (PS2 passes 8 as the technique; the arcade build passes 24, as VS_IBUKI_A and VS_IBUKI_B do)
s32 VS_IBUKI_C(PLW* wk) {
    WORK* em = (WORK*)wk->wu.target_adrs;

    if (Check_Special_Technique(wk, em, 24, 24, 26, 1, -1)) {
        return 1;
    }

    return 0;
}
