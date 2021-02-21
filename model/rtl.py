#!/usr/bin/env python3
# Copyright (c) 2021 TIANLAN.tech
# SPDX-License-Identifier: Apache-2.0

# Language: Python


class SinglePortRAM(object):
    '''
    Single Port RAM functional model
    '''

    def __init__(self, depth=1024, width=8, symbol=8, init=0, skip_align=True, **kw):
        assert width in [8, 16, 32, 64]
        assert symbol == 8
        for k, v in locals().items():
            0 if k == "self" else setattr(self, k, v)
        self.body = width//symbol
        self.init = init.to_bytes(self.body, "little")
        self.reset()

    def reset(self, **kw):
        self.mema = {k: self.init for k in range(getattr(self, "depth"))}

    def demux(self, address: int, **kw):
        be = (self.body).bit_length() - 1
        ra = address >> be
        rb = address & 0xff & ~(0xff << be)
        assert ra in range(getattr(self, "depth"))
        assert rb == 0 or getattr(self, "skip_align")
        return ra, rb

    def read(self, address: int, **kw):
        ra, rb = self.demux(address)
        rd = self.mema[ra]
        return int.from_bytes(rd, "little")

    def write(self, address: int, writedata: int, **kw):
        ra, rb = self.demux(address)
        self.mema[ra] = writedata.to_bytes(self.body, "little")
