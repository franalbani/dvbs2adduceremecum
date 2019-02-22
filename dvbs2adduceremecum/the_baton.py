# -*- coding: utf-8 -*-

from fractions import Fraction as F
from attr import attrs, attrib


MOD_ORDERS = [2, 3, 4, 5]
LDPC_RATES = [F(1, 4), F(1, 3), F(2, 5), F(1, 2), F(3, 5), F(2, 3), F(3, 4),
              F(4, 5), F(5, 6), F(8, 9), F(9, 10)]


def bits_per_fecframe(short_frame=False):
    '''
    Called n_ldpc in the standard.
    '''
    if short_frame:
        return 16200
    else:
        return 64800


def slots_per_plframe(modcod, short_frame=False):
    '''
    # of payload slots per PLFRAME. See page 31 of standard.
    '''
    if short_frame:
        return {2: 90,
                3: 60,
                4: 45,
                5: 36}[modcod.order]
    else:
        return {2: 360,
                3: 240,
                4: 180,
                5: 144}[modcod.order]


def bch_t(modcod, short_frame=False):
    '''
    BCH t error correction. See page 22 and 23 of standard.
    '''
    t = 12
    if not short_frame:
        if modcod.ldpc_rate in [F(2, 3), F(5, 6)]:
            t = 10
        if modcod.ldpc_rate in [F(8, 9), F(9, 10)]:
            t = 8
    else:
        if modcod.ldpc_rate == F(9, 10):
            raise ValueError('BCH t error correction not defined')
    return t


def bch_poly_order(short_frame=False):
    '''
    See page 23 of standard.
    '''
    return 14 if short_frame else 16


def eff_ldpc_rate(modcod, short_frame=False):
    '''
    Effective LDPC rate. For short frames, may differ from
    the LDPC "code identifier". See page 23 of standard.
    '''
    if short_frame:
        return {F(1, 4): F(1, 5),
                F(1, 3): F(1, 3),
                F(2, 5): F(2, 5),
                F(1, 2): F(4, 9),
                F(3, 5): F(3, 5),
                F(2, 3): F(2, 3),
                F(3, 4): F(11, 15),
                F(4, 5): F(7, 9),
                F(5, 6): F(37, 45),
                F(8, 9): F(8, 9)}[modcod.ldpc_rate]
    else:
        return modcod.ldpc_rate


def bits_per_bbframe(modcod, short_frame=False):
    '''
    Called K_bch in the standard. See page 22.
    '''
    t = bch_t(modcod, short_frame)
    inner_rate = eff_ldpc_rate(modcod, short_frame)

    K = (bits_per_fecframe(short_frame) * inner_rate) - t*bch_poly_order(short_frame)
    assert K.denominator == 1
    return int(K)


@attrs
class ModCod:
    order = attrib(type=int)
    ldpc_rate = attrib(type=F)

    @order.validator
    def check_order(self, attribute, value):
        if not value in MOD_ORDERS:
            raise ValueError('ModCod order must be in %r.' % MOD_ORDERS)

    @ldpc_rate.validator
    def check_ldpc_rate(self, attribute, value):
        if not value in LDPC_RATES:
            raise ValueError('LDPC rate must be in %r.' % LDPC_RATES)
 

@attrs
class Conf:
    pilots = attrib(type=bool, default=False)
    short_frame = attrib(type=bool, default=False)
    roll_off = attrib(type=float, default=0.2)


def user_bits_per_hertz(modcod, conf):
    '''
    User bits per Hz.
    '''

    eff = 1

    k = bits_per_bbframe(modcod, conf.short_frame)

    # Mode adaptation
    eff *= (1 - 80 / k)

    # Stream adapter, assuming no padding.
    # eff *= 1

    # FECFRAME
    eff *= k / bits_per_fecframe(conf.short_frame)

    # Now bits are packed into symbols...

    # XFECFRAME
    eff *= modcod.order

    # Physical layer framing
    s = slots_per_plframe(modcod, conf.short_frame)
    pl = 90 * (s + 1)
    if conf.pilots:
        pl += 36 * int((s - 1)/16)

    eff *= 90 * s / pl

    # Physical layer modulation
    eff *= 1 / (1 + conf.roll_off)

    return eff
