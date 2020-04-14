#!/usr/bin/env python3

import crcmod.predefined
import readline
import serial
import sys


class UICmd:
    def __init__(self, cmd, desc_cmd, desc_args="", args=0):
        self.desc_args = desc_args
        self.args = args
        self.cmd = cmd
        self.desc_cmd = desc_cmd

    @staticmethod
    def print_ok(addr, ui):
        ui.print_msg("reader " + hex(addr) + ": OK")

    def validate(self, args, ui):
        return True

    def get_usage(self):
        return (self.cmd + " " + self.desc_args).ljust(16) + self.desc_cmd


class UICmdInfo(UICmd):
    def __init__(self):
        super().__init__("info", "gets reader settings (freq, power, scantime)")

    def run(self, args, reader, ui):
        msg = reader.get_reader_info()
        ui.print_msg("address   : " + hex(msg[0]))
        ui.print_msg("low freq  : " + str(msg[1]) + " kHz")
        ui.print_msg("high freq : " + str(msg[2]) + " kHz")
        ui.print_msg("power     : " + str(msg[3]) + " dBm")
        ui.print_msg("scan time : " + str(int(msg[4]) * 100) + " ms")


class UICmdWorkMode(UICmd):
    def __init__(self):
        super().__init__("mode", "gets reader work mode ()")

    def run(self, args, reader, ui):
        msg = reader.get_work_mode()
        ui.print_msg("mode              : " + msg[1])
        ui.print_msg("protocol          : " + msg[2])
        ui.print_msg("buzzer            : " + msg[3])
        ui.print_msg("addr mode         : " + msg[4])
        ui.print_msg("interface         : " + msg[5])
        ui.print_msg("storage           : " + msg[6])
        ui.print_msg("offset            : " + hex(msg[7]))
        ui.print_msg("length            : " + str(msg[8]))
        ui.print_msg("filter time       : " + str(msg[9]) + " s")
        ui.print_msg("accuracy EAS      : " + str(msg[10]))
        ui.print_msg("offset time       : " + str(msg[11]) + " ms")
        ui.print_msg("W byte order      : " + msg[12])
        ui.print_msg("W mode            : " + msg[13])
        ui.print_msg("W output interval : " + str(msg[14] * 10) + " ms")
        ui.print_msg("W pulse width     : " + str(msg[15] * 10) + " us")
        ui.print_msg("W pulse period    : " + str(msg[16] * 100) + " us")


class UICmdSetFreq(UICmd):
    def __init__(self):
        super().__init__("freq", "set frequency range", "LOW HIGH", 2)

    @staticmethod
    def is_freq(f):
        if f.isdigit():
            if 902600 <= int(f) <= 927400:
                if (int(f) - 902600) % 400 == 0:
                    return True

    @staticmethod
    def to_freq(f):
        return int((int(f) - 902600) / 400)

    def validate(self, args, ui):
        return self.is_freq(args[0]) and self.is_freq(args[1]) and int(args[0]) <= int(args[1])

    def run(self, args, reader, ui):
        self.print_ok(reader.set_freq(self.to_freq(args[0]), self.to_freq(args[1])), ui)


class UICmdSetPower(UICmd):
    def __init__(self):
        super().__init__("power", "sets power in dBm", "0-30", 1)

    def validate(self, args, ui):
        return args[0].isdigit() and (0 <= int(args[0]) <= 30)

    def run(self, args, reader, ui):
        self.print_ok(reader.set_power(int(args[0])), ui)


class UICmdSetScanTime(UICmd):
    def __init__(self):
        super().__init__("scantime", "sets scan time in 100's of ms", "3-255", 1)

    def validate(self, args, ui):
        return args[0].isdigit() and (2 <= int(args[0]) <= 255)

    def run(self, args, reader, ui):
        self.print_ok(reader.set_scan_time(int(args[0])), ui)


class UICmdQuit(UICmd):
    def __init__(self):
        super().__init__("quit", "terminates this prompt")

    def run(self, args, reader, ui):
        ui.quit()


class UICmdHelp(UICmd):
    def __init__(self):
        super().__init__("help", "print commands and usage")

    def run(self, args, reader, ui):
        ui.puts(ui.get_help())


class UI:
    def __init__(self, reader):
        self.commands = dict()
        self.add_command(UICmdInfo())
        self.add_command(UICmdSetPower())
        self.add_command(UICmdHelp())
        self.add_command(UICmdQuit())
        self.add_command(UICmdSetFreq())
        self.add_command(UICmdSetScanTime())
        self.add_command(UICmdWorkMode())
        self.reader = reader

    #        readline.parse_and_bind('tab: complete')
    #        readline.parse_and_bind('set editing-mode vi')

    @staticmethod
    def puts(text):
        print(text, end='')

    @staticmethod
    def print_msg(msg):
        print(msg)

    def add_command(self, cmd):
        self.commands[cmd.cmd] = cmd

    def input(self, line):
        args = line.split(' ')
        if args[0] in self.commands:
            cmd = self.commands[args[0]]
            if len(args[1:]) == cmd.args and cmd.validate(args[1:], self):
                cmd.run(args[1:], self.reader, self)
            else:
                self.print_msg(cmd.get_usage())

    def get_help(self):
        usage = ""
        for k, v in sorted(self.commands.items()):
            usage = usage + v.get_usage() + "\n"
        return usage

    def quit(self):
        self.print_msg("bye")
        sys.exit(0)

    def run(self):
        while True:
            try:
                self.input(input('> ').strip())
            except EOFError:
                self.quit()
            except KeyboardInterrupt:
                self.print_msg('')


class UHFReader18:
    PROTO_6B = "ISO18000-6B"
    PROTO_6C = "ISO18000-6C"

    IFACE_WIEGAND = "wiegand"
    IFACE_SERIAL = "RS232/RS485"
    IFACE_SYRIS = "SYRIS485"

    MSB = "msb"
    LSB = "lsb"

    WIEGAND_26 = "wiegand26"
    WIEGAND_34 = "wiegand34"

    STORAGE_PASSWD = "password"
    STORAGE_EPC = "epc"
    STORAGE_TID = "tid"
    STORAGE_USER = "user"
    STORAGE_MULTI_QUERY = "multi query"
    STORAGE_ONE_QUERY = "one query"
    STORAGE_EAS = "eas"

    MODE_ANSWER = "answer"
    MODE_ACTIVE = "active"
    MODE_TRIG_LOW = "trigger low"
    MODE_TRIG_HIGH = "trigger high"

    ON = "on"
    OFF = "off"

    ADDR_BYTE = "byte"
    ADDR_WORD = "word"

    GET_READER_INFO = 0x21
    SET_FREQ = 0x22
    SET_SCAN_TIME = 0x25
    SET_POWER = 0x2f
    GET_WORK_MODE = 0x36
    ADDR_BROADCAST = 0xff

    @staticmethod
    def ret_addr(data):
        return data[0]

    def open_port(self, path, baud):
        self.port = path
        self.sr = serial.Serial()
        self.sr.baudrate = baud
        self.sr.port = path
        self.sr.open()
        self.crc = crcmod.predefined.Crc('crc-16-mcrf4xx')

    def get_crc(self, msg):
        crc = self.crc.new()
        crc.update(msg)
        return crc.digest()

    def send(self, addr, cmd, args=bytes([])):
        msg = bytes([addr, cmd]) + args
        msg = bytes([len(msg) + 2]) + msg
        crc = self.get_crc(msg)
        msg = msg + bytes([crc[1], crc[0]])
        self.sr.write(msg)

    def recv(self):
        count = self.sr.read(1)
        data = self.sr.read(count[0])
        crc = data[-2:]
        calcCrc = self.get_crc(count + data[:-2])
        if crc[0] != calcCrc[1] or crc[1] != calcCrc[0]:
            raise Exception("CRC failed: " + (count + data).hex())
        return data

    def get_reader_info(self):
        self.send(self.ADDR_BROADCAST, self.GET_READER_INFO)
        info = self.recv()
        return info[0], info[8] * 400 + 902600, info[7] * 400 + 902600, info[9], info[10]

    def set_freq(self, low, high):
        self.send(self.ADDR_BROADCAST, self.SET_FREQ, bytes([high, low]))
        return self.ret_addr(self.recv())

    def set_scan_time(self, time):
        self.send(self.ADDR_BROADCAST, self.SET_SCAN_TIME, bytes([time]))
        return self.ret_addr(self.recv())

    def set_power(self, power):
        self.send(self.ADDR_BROADCAST, self.SET_POWER, bytes([power]))
        return self.ret_addr(self.recv())

    def get_work_mode(self, addr=0xff):
        self.send(addr, self.GET_WORK_MODE)
        recv = self.recv()
        mode = [self.MODE_ANSWER, self.MODE_ACTIVE, self.MODE_TRIG_LOW, self.MODE_TRIG_HIGH][recv[7]]
        chaos = recv[8]
        proto = [self.PROTO_6C, self.PROTO_6B][chaos & 0x1]
        buzzer = [self.ON, self.OFF][(chaos & 0x4) >> 2]
        addr = [self.ADDR_WORD, self.ADDR_BYTE][(chaos & 0x8) >> 3]
        ifce = [self.IFACE_WIEGAND, self.IFACE_SERIAL, self.IFACE_SYRIS][((chaos & 0x10) >> 4) + ((chaos & 0x2) >> 1)]
        storage = [self.STORAGE_PASSWD, self.STORAGE_EPC, self.STORAGE_TID, self.STORAGE_USER, self.STORAGE_MULTI_QUERY,
                   self.STORAGE_ONE_QUERY, self.STORAGE_EAS][recv[9]]
        offset = recv[10]
        length = recv[11]
        filter_time = recv[12]
        acc_eas = recv[13]
        offset_time = recv[14]
        w_order = [self.MSB, self.LSB][(recv[3] & 0x2) >> 1]
        w_type = [self.WIEGAND_26, self.WIEGAND_34][recv[3] & 0x1]
        w_inter = recv[4]
        w_pulse_width = recv[5]
        w_pulse_int = recv[6]
        return (
            recv[0], mode, proto, buzzer, addr, ifce, storage, offset, length, filter_time, acc_eas, offset_time,
            w_order,
            w_type, w_inter, w_pulse_width, w_pulse_int)


if len(sys.argv) != 2:
    print("usage: uhf TTY_SERIAL")
    sys.exit(2)

if __name__ == '__main__':
    uhfr = UHFReader18()
    uhfr.open_port(sys.argv[1], 57600)
    UI(uhfr).run()
