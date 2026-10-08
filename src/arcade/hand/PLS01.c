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

// 0x0611CFDE
// No PS2 counterpart found. Like check_F_R_walk, but enters routines 11 and 12 and is gated by
// spmv_ng_flag bits 1 and 2. Called from nm_03000 and jumping_cg_type_check. In the PS2 state table
// routines 11 and 12 still exist (aliases of the walk handlers) but nothing in the PS2 source enters them.
s16 func_0611CFDE(PLW* wk) {
    s16 rnum = 0;

    switch (wk->cp->lever_dir) {
    case 1:
        if (!(wk->spmv_ng_flag & 1)) {
            wk->wu.routine_no[1] = 0;
            wk->wu.routine_no[2] = 11;
            wk->wu.routine_no[3] = 0;
            rnum = 1;
        }

        break;

    case 2:
        if (!(wk->spmv_ng_flag & 2)) {
            wk->wu.routine_no[1] = 0;
            wk->wu.routine_no[2] = 12;
            wk->wu.routine_no[3] = 0;
            rnum = 1;
        }

        break;
    }

    return rnum;
}

// 0x0611D150
// No PS2 counterpart found. Same as check_walking_lv_dir, for routines 11 and 12 instead of 3 and 4.
s16 func_0611D150(PLW* wk) {
    s16 rnum = 0;

    switch (wk->cp->lever_dir) {
    case 1:
        if (wk->wu.routine_no[2] != 11) {
            rnum = 1;
        }

        break;

    case 2:
        if (wk->wu.routine_no[2] != 12) {
            rnum = 1;
        }

        break;

    default:
        rnum = 1;
        break;
    }

    if (rnum) {
        if (wk->wu.pat_status < 32) {
            wk->wu.routine_no[2] = 1;
        } else {
            wk->wu.routine_no[2] = 9;
        }

        wk->wu.routine_no[1] = 0;
        wk->wu.routine_no[3] = 0;
    }

    return rnum;
}
