import os
import re
from cocotb import test as testbench
from cocotb import triggers, clock, fork
from cocotb_test import simulator
from tempfile import TemporaryDirectory
from struct import unpack


async def set_reset(clk, rst, delay=10, active=1):
    rst.value = 1 if active else 0
    await triggers.ClockCycles(clk, delay)
    rst.value = 0 if active else 1


async def set_regs(clk, obj, regs: list, value=0):
    for t in [getattr(obj, n) for n in regs]:
        t.value = value


async def exec_rom(clk, ra, rr, rd, rv, data: dict):
    while True:
        await triggers.RisingEdge(clk)
        raddr, rread, rdatavalid = ra.value, rr.value, rv.value
        rv.value = 0 if not rread else 1 ^ rdatavalid
        rd.value = 0 if not rread else data[raddr//4]


def build_target(files, target="verilog", cc="riscv64-elf-gcc", objcopy="riscv64-elf-objcopy"):
    with TemporaryDirectory() as d:
        t1, t2, t3, t4 = "", "", "{}/out.elf".format(d), "{}/out.mem".format(d)
        for k, v in files.items():
            with open("{}/{}".format(d, k), "w") as fp:
                fp.write(v)
            t1 = "{}/{}".format(d, k) if k.endswith(".ld") else t1
            t2 = "{}/{}".format(d, k) if k.endswith(".s") else t2

        command = "{} -nostartfiles -march=rv32i -mabi=ilp32".format(cc)
        command += " -T{} -o {} {}".format(t1, t3, t2)
        command += " && {}".format(objcopy)
        command += " --target={} {} {}".format(target, t3, t4)
        os.system(command)

        assert os.path.isfile(t4)

        with open(t4, "r") as fp:
            _ret = fp.read()

    return _ret


@testbench(timeout_time=2,
           timeout_unit="us",
           skip=("serv_rf_top" != os.getenv("TOPLEVEL")))
async def serv_exec_blinky(dut):
    fork(clock.Clock(dut.clk, 10, "ns").start())
    fork(set_reset(dut.clk, dut.i_rst, delay=3))

    files = {}
    files["blink.s"] = '''
        .globl _start
        _start:
            lui a0, %hi(0x40000000)
            addi a0, a0, %lo(0x40000000)
            li t1, 0x100000
        bl1:
            sb t0, 0(a0)
            xori t0, t0, 1
            and t2, zero, zero
        time1:
            addi t2, t2, 1
            bne t1, t2, time1
            j bl1
        '''
    files["link.ld"] = '''
        OUTPUT_ARCH( "riscv" )
        ENTRY(_start)
        SECTIONS
        {
            . = 0x00000000;
            .text : { *(.text) }
            .data : { *(.data) }
            .bss : { *(.bss) }
        }
        '''

    mem = build_target(files)
    mem = re.findall(r"\b[0-9A-Z]{2}\b", mem)
    mem = bytes([int(n, 16) for n in mem])
    mem = unpack("<{}I".format(len(mem)//4), mem)
    mem = {k: v for k, v in enumerate(mem)}

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
