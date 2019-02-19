# -*- coding: utf-8 -*-

from fractions import Fraction as F
from attr import attrs, attrib


def frame_len(short_frame=False):
    if short_frame:
        return 16200
    else:
        return 64800


def S(modcod, short_frame=False):
    if short_frame:
        return {'2': 90,
                '3': 60,
                '4': 45,
                '5': 36}[modcod.order]
    else:
        return {'2': 360,
                '3': 240,
                '4': 180,
                '5': 144}[modcod.order]


def bch_t(modcod, short_frame=False):
    '''
    BCH t error correction
    '''
    t = 12
    if not short_frame:
        if modcod.ldpc_code_rate in [F(2, 3), F(5, 6)]:
            t = 10
        if modcod.ldpc_code_rate in [F(8, 9), F(9, 10)]:
            t = 8
    else:
        if modcod.ldpc_code_rate == F(9, 10):
            raise ValueError('BCH t error correction not defined')
    return t


def bch_poly_order(short_frame=False):
    if short_frame:
        return 14
    else:
        return 16


def eff_ldpc_rate(modcod, short_frame=False):
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
                F(8, 9): F(8, 9)}[modcod.ldpc_code_rate]
    else:
        return modcod.ldpc_code_rate


def K_bch(modcod, short_frame=False):
    t = bch_t(modcod, short_frame)
    inner_rate = eff_ldpc_rate(modcod, short_frame)

    K = (frame_len(short_frame) * inner_rate) - t*bch_poly_order(short_frame)
    assert K.denominator == 1
    return K


@attrs
class ModCod:
    order = attrib(type=int)
    ldpc_code_rate = attrib(type=F)


@attrs
class Conf:
    pilots = attrib(type=bool, default=False)
    short_frame = attrib(type=bool, default=False)
    roll_off = attrib(type=float, default=0.2)


def efficiency(modcod, conf):

    eff = 1
    eff *= 184/188

    k = K_bch(modcod, conf.short_frame)

    eff *= (1 - 80 / k)
    eff *= k / frame_len(conf.short_frame)

    s = S(modcod, conf.short_frame)
    pl = 90*(s + 1)
    if conf.pilots:
        pl += 36*int((s-1)/16)

    eff *= 90 * s / pl

    eff *= 1 / (1 + conf.roll_off)

    return eff
