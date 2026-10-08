// Arcade (CPS-3, 990512) versions of routines in Source/Game/PLS02.c, written by reading the arcade code.
#include "sf33rd/Source/Game/PLS02.h"
#include "common.h"
#include "sf33rd/Source/Game/workuser.h"

// The arcade build has exactly four random-number functions. Each advances its own index and reads its own
// table; none of them has the PS2 `Debug_w[0x3B] == 0xE0` reset.
// PS2 adds random_32_com / random_16_com / random_32_ex_com / random_16_ex_com (separate streams used by the
// CPU-opponent code when Play_Mode != 0) and random_16_bg. They do not exist here: arcade CPU-opponent code
// calls random_32 and random_16 directly, sharing the stream with everything else.

// 0x0611E0D6  (index at 0x020155EA, table at 0x065EB334)
s32 random_32() {
    Random_ix32++;
    Random_ix32 &= 0x7F;
    return random_tbl_32[Random_ix32];
}

// 0x0611E0EE  (index at 0x020155E8, table at 0x065EB434)
s32 random_16() {
    Random_ix16++;
    Random_ix16 &= 0x3F;
    return random_tbl_16[Random_ix16];
}

// 0x0611E106  (index at 0x02016AE2, table at 0x065EB4B4)
s32 random_32_ex() {
    Random_ix32_ex++;
    Random_ix32_ex &= 0x1F;
    return random_tbl_32_ex[Random_ix32_ex];
}

// 0x0611E11E  (index at 0x02016AE0, table at 0x065EB4F4)
s32 random_16_ex() {
    Random_ix16_ex++;
    Random_ix16_ex &= 0xF;
    return random_tbl_16_ex[Random_ix16_ex];
}
