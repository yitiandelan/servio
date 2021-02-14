#!/usr/bin/env python3
# Copyright (c) 2021 TIANLAN.tech
# SPDX-License-Identifier: Apache-2.0

# Language: Python

import os
import re
from random import randint
from cocotb import test as testbench
from cocotb import triggers, clock, fork
from cocotb.drivers.avalon import AvalonMemory
from cocotb_test import simulator
from test_serv import set_reset, set_regs


@testbench(timeout_time=50,
           timeout_unit="us",
           skip=("servio_rom" != os.getenv("TOPLEVEL")))
async def servio_rom_function(dut):
    fork(clock.Clock(dut.clk, 10, "ns").start())
    fork(set_reset(dut.clk, dut.reset, delay=2))

    mem = [randint(0, 256) for _ in range(1024)]
    mem = {k: v for k, v in enumerate(mem)}

    fork(set_regs(dut.clk, dut, ["wb_s1_{}".format(n)
                                 for n in ["adr", "cyc", "we", "dat"]]))
    fork(set_regs(dut.clk, dut, ["wb_s0_{}".format(n)
                                 for n in ["adr", "cyc"]]))

    await triggers.FallingEdge(dut.reset)
    await triggers.RisingEdge(dut.clk)

    await set_regs(dut.clk, dut, ["wb_s1_{}".format(n) for n in ["cyc", "we"]], 1)
    for k, v in mem.items():
        dut.wb_s1_adr.value = k
        dut.wb_s1_dat.value = v
        await triggers.RisingEdge(dut.clk)
    await set_regs(dut.clk, dut, ["wb_s1_{}".format(n) for n in ["cyc", "we"]], 0)

    await triggers.RisingEdge(dut.clk)

    for k, v in mem.items():
        dut.wb_s0_cyc.value = 1
        dut.wb_s0_adr.value = k
        await triggers.RisingEdge(dut.clk if dut.wb_s0_ack.value else dut.wb_s0_ack)
        dut.wb_s0_cyc.value = 0

    await triggers.ClockCycles(dut.clk, 2)


@testbench(timeout_time=800,
           timeout_unit="ns",
           skip=("servio_mux" != os.getenv("TOPLEVEL")))
async def servio_mux_function(dut):
    fork(clock.Clock(dut.clk, 10, "ns").start())
    fork(set_reset(dut.clk, dut.reset, delay=3))

    fork(set_regs(dut.clk, dut, ["wb_s{}_adr".format(n)
                                 for n in range(4)]))
    fork(set_regs(dut.clk, dut, ["wb_s{}_cyc".format(n)
                                 for n in range(4)]))

    async def wb_wait_ack(dut, bus: str, cnt=1):
        obj = ["{}_{}".format(bus, n) for n in ["adr", "ack", "cyc"]]
        obj = [getattr(dut, n) for n in obj]
        for _ in range(cnt):
            obj[0].value = 0xfc & randint(0, 256)
            obj[2].value = 1
            await triggers.RisingEdge(obj[1])
            await triggers.ClockCycles(dut.clk, 1)
        obj[2].value = 0

    mem = AvalonMemory(dut, "avm_s4", dut.clk, readlatency_min=0,
                       readlatency_max=0, memory={k: 0 for k in range(dut.DATA_DEPTH.value)})

    for _ in range(2):
        for n in range(4):
            fork(wb_wait_ack(dut, "wb_s{}".format(n), 1))
        await triggers.RisingEdge(dut.wb_s3_ack)
        await triggers.ClockCycles(dut.clk, 1)

    await triggers.ClockCycles(dut.clk, 2)


def test_servio_rom_testcase():
    root_dir = os.path.dirname(__file__) + "/.."
    toplevel, files = "servio_rom", []
    includes, defines = [], []
    parameters = {"DATA_DEPTH": "1024", "DATA_WIDTH": "8"}

    files += ["{}/rtl/{}".format(root_dir, n)
              for n in ["servio_ram.v"]]
    # defines += ["SERVIO_ROM_SIM"]
    assert not False in [os.path.isdir(n) for n in includes]
    assert not False in [os.path.isfile(n) for n in files]

    simulator.run(
        verilog_sources=files,
        toplevel=toplevel,
        defines=defines,
        includes=includes,
        extra_env=parameters,
        parameters=parameters,
        # force_compile=True,
        compile_args=["-Wtimescale"],
        sim_build="sim_build/{}".format(toplevel),
        module="test_servio"
    )


def test_servio_mux_testcase():
    root_dir = os.path.dirname(__file__) + "/.."
    toplevel, files = "servio_mux", []
    includes, defines = [], []
    parameters = {"DATA_DEPTH": "1024"}

    files += ["{}/rtl/{}".format(root_dir, n)
              for n in ["servio_mux.v"]]
    defines += ["SERVIO_MUX_SIM"]
    assert not False in [os.path.isdir(n) for n in includes]
    assert not False in [os.path.isfile(n) for n in files]

    simulator.run(
        verilog_sources=files,
        toplevel=toplevel,
        defines=defines,
        includes=includes,
        extra_env=parameters,
        parameters=parameters,
        # force_compile=True,
        compile_args=["-Wtimescale"],
        sim_build="sim_build/{}".format(toplevel),
        module="test_servio"
    )


if __name__ == "__main__":
    test_servio_rom_testcase()
