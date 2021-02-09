import os
import re
from random import randint
from cocotb import test as testbench
from cocotb import triggers, clock, fork
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


if __name__ == "__main__":
    test_servio_rom_testcase()
