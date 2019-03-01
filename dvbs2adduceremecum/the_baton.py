# -*- coding: utf-8 -*-

from fractions import Fraction as F
from attr import attrs, attrib


MOD_ORDERS = [2, 3, 4, 5]
LDPC_RATES = [F(1, 4), F(1, 3), F(2, 5), F(1, 2), F(3, 5), F(2, 3), F(3, 4),
              F(4, 5), F(5, 6), F(8, 9), F(9, 10)]

# This values are for 10^-7 TS PER
EsN0_min_dB = {
    # QPSK
    (2, F(1,  4)): -2.35,
    (2, F(1,  3)): -1.24,
    (2, F(2,  5)): -0.30,
    (2, F(1,  2)):  1.00,
    (2, F(3,  5)):  2.23,
    (2, F(2,  3)):  3.10,
    (2, F(3,  4)):  4.03,
    (2, F(4,  5)):  4.68,
    (2, F(5,  6)):  5.18,
    (2, F(8,  9)):  6.20,
    (2, F(9, 10)):  6.42,
    # 8-PSK
    (3, F(3,  5)):  5.50,
    (3, F(2,  3)):  6.62,
    (3, F(3,  4)):  7.91,
    (3, F(5,  6)):  9.35,
    (3, F(8,  9)): 10.69,
    (3, F(9, 10)): 10.98,
    # 16-APSK
    (4, F(2,  3)):  8.97,
    (4, F(3,  4)): 10.21,
    (4, F(4,  5)): 11.03,
    (4, F(5,  6)): 11.61,
    (4, F(8,  9)): 12.89,
    (4, F(9, 10)): 13.13,
    # 32-APSK
    (5, F(3,  4)): 12.73,
    (5, F(4,  5)): 13.64,
    (5, F(5,  6)): 14.28,
    (5, F(8,  9)): 15.69,
    (5, F(9, 10)): 16.05,
    }
 

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

    def __attrs_post_init__(self):
        try:
            self.esno_min_dB = EsN0_min_dB[(self.order, self.ldpc_rate)]
        except KeyError as ke:
            n, d = self.ldpc_rate.numerator, self.ldpc_rate.denominator
            raise ValueError('ModCod(%d, %2d / %2d) does not exist.'
                              % (self.order, n, d))


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
