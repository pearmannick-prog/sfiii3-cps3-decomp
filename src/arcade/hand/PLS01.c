// Arcade (CPS-3, 990512) versions of routines in Source/Game/PLS01.c, written by reading the arcade code.
#include "sf33rd/Source/Game/PLS01.h"
#include "common.h"
#include "sf33rd/Source/Game/Grade.h"

// 0x0611CEA4
// PS2 adds two spmv_ng_flag tests here (0x20000 before the high-jump branch, 0x10000 before the normal jump).
// The arcade function has neither.
s32 check_jump_ready(PLW* wk) {
    if (!(wk->cp->sw_new & 1)) {
        return 0;
    }

    if (wk->cp->waza_flag[2] != 0) {
        wk->wu.routine_no[2] = 17;
        grade_add_command_waza(wk->wu.id);
    } else {
        wk->wu.routine_no[2] = 16;
    }

    wk->wu.routine_no[1] = 0;
    wk->wu.routine_no[3] = 0;
    wk->jpdir = 0;
    return 1;
}

// 0x0611CE6C
// No PS2 counterpart found (PS2 never reads waza_flag[13]). The standing-state routines (nm_01000 and
// relatives) call it between check_F_R_dash and check_jump_ready. What routine 19 does here is not yet traced.
s32 func_0611CE6C(PLW* wk) {
    if (wk->spmv_ng_flag & 0x10000) {
        return 0;
    }

    if (wk->cp->waza_flag[13] == 0) {
        return 0;
    }

    wk->wu.routine_no[1] = 0;
    wk->wu.routine_no[2] = 19;
    wk->wu.routine_no[3] = 0;
    wk->jpdir = 0;
    return 1;
}
