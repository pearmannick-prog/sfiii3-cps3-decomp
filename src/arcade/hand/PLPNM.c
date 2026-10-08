// Arcade (CPS-3, 990512) versions of routines in Source/Game/PLPNM.c, written by reading the arcade code.
#include "sf33rd/Source/Game/PLPNM.h"
#include "common.h"
#include "sf33rd/Source/Game/CHARSET.h"
#include "sf33rd/Source/Game/PLS02.h"
#include "sf33rd/Source/Game/SpGauge.h"

// 0x06121EC0  (player routines 31-33: ground parry)
// PS2 differences in case 0: PS2 makes dm_stop negative when it is positive, and calls subtract_dm_vital
// (and the PS2-only rumble hook) after add_sp_arts_gauge_paring. The arcade build does neither.
void Normal_31000(PLW* wk) {
    if (((WORK*)wk->wu.target_adrs)->cg_prio != 2) {
        wk->wu.next_z = 32;
    }

    wk->guard_chuu = guard_kind[wk->wu.routine_no[2] - 27];
    wk->scr_pos_set_flag = 0;

    switch (wk->wu.routine_no[3]) {
    case 0:
        wk->wu.routine_no[3]++;
        wk->wu.rl_flag = (wk->wu.dm_rl + 1) & 1;
        set_char_move_init(&wk->wu, 0, wk->wu.routine_no[2] - 7);
        set_hit_stop_hit_quake(&wk->wu);
        add_sp_arts_gauge_paring(wk);
        break;

    case 1:
        wk->wu.routine_no[3]++;
        char_move_wca(&wk->wu);
        break;

    case 2:
        char_move(&wk->wu);
        break;
    }
}
