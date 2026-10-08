// Arcade (CPS-3, 990512) versions of routines in Source/Game/PLPDM.c, written by reading the arcade code.
#include "sf33rd/Source/Game/PLPDM.h"
#include "common.h"
#include "sf33rd/Source/Game/SLOWF.h"
#include "sf33rd/Source/Game/SpGauge.h"
#include "sf33rd/Source/Game/workuser.h"

// 0x06124BC4
// Same damage, death and stun logic as PS2. The arcade build lacks three PS2 additions: the
// `omop_vital_ix[id] == 5` test that zeroes the damage, the rumble hook, and the training-mode hook.
// Note the stun counter is the high half of py->now.timer: at offset 8 on the big-endian arcade CPU.
void subtract_dm_vital(PLW* wk) {
    if (wk->dead_flag == 0) {
        if (wk->wu.dm_vital && (wk->wu.routine_no[1] != 1 || wk->wu.routine_no[2] > 11 || wk->wu.routine_no[3] != 0)) {
            Additinal_Score_DM((WORK_Other*)wk->wu.dmg_adrs, wk->wu.dm_ten_ix);
        }

        add_sp_arts_gauge_hit_dm(wk);

        if (wk->atemi_flag) {
            wk->dm_vital_backup = wk->wu.dm_vital;
        } else {
            wk->dm_vital_backup = 0;
        }

        wk->dm_vital_use = 0;
        wk->wu.vital_new -= wk->wu.dm_vital;

        if (wk->wu.dm_guard_success == -1 && wk->wu.vital_old > 0 && wk->wu.vital_new < 0 && wk->wu.vital_new > -3) {
            wk->wu.vital_new = 0;
        }

        if (wk->wu.dm_nodeathattack && wk->wu.vital_new < 0) {
            wk->wu.vital_new = 0;
        }

        if (wk->wu.vital_new < 0) {
            wk->wu.vital_new = -1;
            wk->dead_flag = 1;
            dead_voice_flag = 1;

            if (wk->wu.dm_guard_success != -1) {
                wk->kezurijini_flag = 1;
            }

            if (round_slow_flag == 0) {
                set_conclusion_slow();
                round_slow_flag = 1;
            }
        } else if (wk->py->flag == 0) {
            wk->py->now.quantity.h += wk->wu.dm_piyo;

            if (wk->py->now.quantity.h >= wk->py->genkai) {
                wk->py->now.timer = 0;
                wk->py->flag = 1;
            }
        }
    }

    wk->wu.dm_vital = 0;
    wk->wu.dm_piyo = 0;
}
