import os
import re
from cocotb import test as testbench
from cocotb import triggers, clock, fork
from cocotb_test import simulator


async def set_reset(clk, rst, delay=10, active=1):
    rst.value = 1 if active else 0
    await triggers.ClockCycles(clk, delay)
    rst.value = 0 if active else 1


async def set_regs(clk, obj, regs: list, value=0):
    for t in [getattr(obj, n) for n in regs]:
        t.value = value


async def exec_rom(clk, ra, rr, rd, rv, data=list):
    while True:
        await triggers.RisingEdge(clk)
        raddr, rread, rdatavalid = ra.value, rr.value, rv.value
        rv.value = 0 if not rread else 1 ^ rdatavalid
        rd.value = 0 if not rread else data[raddr//4]


@testbench(timeout_time=2,
           timeout_unit="us",
           skip=("serv_rf_top" != os.getenv("TOPLEVEL")))
async def serv_exec_blinky(dut):
    fork(clock.Clock(dut.clk, 10, "ns").start())
    fork(set_reset(dut.clk, dut.i_rst, delay=3))

    mem = {k: v for k, v in enumerate(
        [0x40000537,  0x00050513, 0x00100337, 0x00550023])}

    fork(exec_rom(dut.clk, dut.o_ibus_adr, dut.o_ibus_cyc,
                  dut.i_ibus_rdt, dut.i_ibus_ack, mem))
    fork(set_regs(dut.clk, dut, ["i_timer_irq", "i_dbus_ack"]))
    fork(set_regs(dut.clk, dut.cpu.genblk1.csr, ["o_new_irq", "timer_irq_r"]))
    fork(set_regs(dut.clk, dut.cpu.genblk1.csr, ["mstatus_mie", "mie_mtie"]))

    await triggers.RisingEdge(dut.o_dbus_cyc)
    assert dut.o_dbus_adr.value == 0x40000000
    assert dut.o_dbus_sel.value == 1


@testbench(timeout_time=2,
           timeout_unit="us",
           skip=("servant" != os.getenv("TOPLEVEL")))
async def servant_exec_zephyr_hello(dut):
    pass


@testbench(timeout_time=2,
           timeout_unit="us",
           skip=("servant" != os.getenv("TOPLEVEL")))
async def servant_exec_riscv_compliance(dut):
    pass


def test_serv_testcase():
    root_dir = os.path.dirname(__file__) + "/.."
    toplevel, files = "serv_rf_top", []
    includes, defines = [], ["SERV_CLEAR_RAM"]
    parameters = {"RESET_STRATEGY": "\"MINI\"",
                  "WITH_CSR": "1",
                  "RF_WIDTH": "2"}

    files += ["{}/rtl/{}".format(root_dir, n)
              for n in ["servio_ram.v"]]  # import timescale
    files += ["{}/modules/serv/rtl/{}".format(root_dir, n)
              for n in ["serv_alu.v",
                        "serv_csr.v",
                        "serv_decode.v",
                        "serv_mem_if.v",
                        "serv_rf_if.v",
                        "serv_rf_ram.v",
                        "serv_state.v",
                        "serv_bufreg.v",
                        "serv_ctrl.v",
                        "serv_immdec.v",
                        "serv_rf_ram_if.v",
                        "serv_rf_top.v",
                        "serv_top.v"]]
    includes += ["{}/modules/serv/rtl".format(root_dir)]
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
        module="test_serv"
    )


def test_servant_testcase():
    pass


if __name__ == "__main__":
    test_serv_testcase()
    test_servant_testcase()
