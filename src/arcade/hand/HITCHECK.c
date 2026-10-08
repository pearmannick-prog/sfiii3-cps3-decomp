// Arcade (CPS-3, 990512) versions of routines in Source/Game/HITCHECK.c, written by reading the arcade code.
// Field names are the 3s-decomp ones; the arcade struct offsets they were read from are noted where useful.
#include "sf33rd/Source/Game/HITCHECK.h"
#include "common.h"
#include "sf33rd/Source/Game/Grade.h"
#include "sf33rd/Source/Game/PLS01.h"

// 0x0608D6E4
// Two parameters in the arcade build. PS2 adds `kom` (chip damage is divided by kezuri_pow / kom),
// the kezurare_flag bookkeeping, and two option tests (spmv_ng_flag 0x8000, spmv_ng_flag2 0x10000000).
s16 check_dm_att_guard(WORK* as, WORK* ds) {
    s16 rnum = 0;

    if (as->kezuri_pow) {
        if (ds->dm_vital != 0) {
            ds->dm_vital = ds->dm_vital / as->kezuri_pow;

            if (ds->dm_vital == 0) {
                ds->dm_vital = 1;
            }

            if (ds->dm_vital > ds->vital_new) {
                if (as->no_death_attack) {
                    ds->dm_vital = ds->vital_new;
                } else {
                    ds->dm_guard_success = ds->routine_no[2];
                    rnum = 1;
                }
            }
        }
    } else {
        ds->dm_vital = 0;
    }

    return rnum;
}

// 0x0608DAE8
// PS2 differences: PS2 has one air parry (waza_flag[5], routine 34) plus a just-guarded ("just_now") path,
// the abs/ags option flags, and a dead_flag test. The arcade build has two air parries and none of the rest,
// and its guard path always requires the lever (no auto_guard or sw_lvbt test).
s32 defense_sky(PLW* as, PLW* ds, s8 gddir) {
    if (ds->py->flag == 0 && !(ds->guard_flag & 2) && as->wu.att.guard & 4) {
        if (!(ds->spmv_ng_flag & 0x400) && ds->cp->waza_flag[5] != 0) {
            blocking_point_count_up(ds);
            as->wu.hf.hit.player = 0x80;
            ds->wu.routine_no[2] = 34;

            if (check_dm_att_blocking(&as->wu, &ds->wu, 7)) {
                return 2;
            }

            return 0;
        }

        if (!(ds->spmv_ng_flag & 0x800) && ds->cp->waza_flag[6] != 0) {
            blocking_point_count_up(ds);
            as->wu.hf.hit.player = 0x80;
            ds->wu.routine_no[2] = 35;

            if (check_dm_att_blocking(&as->wu, &ds->wu, 7)) {
                return 2;
            }

            return 0;
        }
    }

    if (!(as->wu.att.guard & 32)) {
        return 2;
    }

    if (ds->guard_flag & 1) {
        return 2;
    }

    if (ds->spmv_ng_flag & 32) {
        return 2;
    }

    if (!(ds->saishin_lvdir & gddir)) {
        return 2;
    }

    as->wu.hf.hit.player = 0x20;
    ds->wu.routine_no[2] = 7;

    if (check_dm_att_guard(&as->wu, &ds->wu)) {
        return 2;
    }

    return 1;
}

// 0x0608DBEC
// PS2 only calls grade_add_blocking when spmv_ng_flag & 0x80; the arcade build always calls it.
void blocking_point_count_up(PLW* wk) {
    wk->kind_of_blocking = 0;

    if (wk->wu.routine_no[1] == 0 && wk->wu.routine_no[2] > 30 && wk->wu.routine_no[2] < 36) {
        wk->kind_of_blocking = 1;
    }

    if (wk->wu.routine_no[1] == 1 && wk->wu.routine_no[2] > 3 && wk->wu.routine_no[2] < 8) {
        wk->kind_of_blocking = 2;
    }

    grade_add_blocking(wk);
}

// 0x0608DC44
// PS2 differences:
//  - no abs/ags option flags (spmv_ng_flag 0x80 / 0x40) and no dead_flag test
//  - the just-guarded thresholds come from a table indexed by attack type only (arcade data at 0x0618BBE4);
//    PS2 indexes grdb by player id as well, and gates this path with spmv_ng_flag 0x1000 instead of 0x100/0x200
//  - parrying a jump attack high needs waza_flag[12] only (PS2 also tests spmv_ng_flag 0x800), and the low
//    parry makes no jump-attack distinction
//  - guarding always tests the lever unless auto_guard is set (PS2 skips the test while just_now, unless
//    spmv_ng_flag 0x2000)
//  - check_normal_attack is expanded inline in the arcade code
s32 defense_ground(PLW* as, PLW* ds, s8 gddir) {
    s8 just_now;
    s8 attr_att;

    just_now = 0;

    if (ds->guard_chuu != 0 && ds->guard_chuu < 5) {
        just_now = 1;
        attr_att = check_normal_attack(as->wu.kind_of_waza);
    }

    if (ds->py->flag == 0 && !(ds->guard_flag & 2) && as->wu.att.guard & 3) {
        if (as->wu.att.guard & 2 && !(ds->spmv_ng_flag & 0x100)) {
            if (just_now ? (ds->cp->waza_flag[3] >= grdb[attr_att][0])
                         : (as->wu.jump_att_flag ? (ds->cp->waza_flag[12] != 0) : (ds->cp->waza_flag[3] != 0))) {
                blocking_point_count_up(ds);
                as->wu.hf.hit.player = 64;

                if (check_attbox_dir(ds) == 0) {
                    ds->wu.routine_no[2] = 31;
                } else {
                    ds->wu.routine_no[2] = 32;
                }

                if (check_dm_att_blocking(&as->wu, &ds->wu, 5)) {
                    return 2;
                }

                return 0;
            }
        }

        if (as->wu.att.guard & 1 && !(ds->spmv_ng_flag & 0x200)) {
            if (just_now ? (ds->cp->waza_flag[4] >= grdb[attr_att][1]) : (ds->cp->waza_flag[4] != 0)) {
                blocking_point_count_up(ds);
                as->wu.hf.hit.player = 64;
                ds->wu.routine_no[2] = 33;

                if (check_dm_att_blocking(&as->wu, &ds->wu, 6)) {
                    return 2;
                }

                return 0;
            }
        }
    }

    if (!(as->wu.att.guard & 0x18)) {
        return 2;
    }

    if (ds->guard_flag & 1) {
        return 2;
    }

    if (ds->spmv_ng_flag & 0x10) {
        return 2;
    }

    if (!ds->auto_guard) {
        if (!(ds->saishin_lvdir & gddir)) {
            return 2;
        }

        if (ds->cp->sw_lvbt & 1) {
            return 2;
        }
    }

    switch (as->wu.att.guard & 0x18) {
    case 8:
        if (!(ds->cp->sw_lvbt & 2)) {
            return 2;
        }

        ds->wu.routine_no[2] = 6;
        break;

    case 16:
        if (ds->cp->sw_lvbt & 2) {
            return 2;
        }

        ds->wu.routine_no[2] = 5;
        break;

    default:
        if (ds->cp->sw_lvbt & 2) {
            ds->wu.routine_no[2] = 6;
            break;
        }

        ds->wu.routine_no[2] = 5;
        break;
    }

    as->wu.hf.hit.player = 16;

    if (ds->wu.routine_no[2] == 5 && check_attbox_dir(ds) == 0) {
        ds->wu.routine_no[2] = 4;
    }

    if (check_dm_att_guard(&as->wu, &ds->wu)) {
        return 2;
    }

    return 1;
}
