#!/usr/bin/env python3

import crcmod.predefined
import readline
import serial
import sys

class UICmd:
    def __init__(self):
        self.descArgs = ""
        self.args = 0

    def printOk(self, addr, ui):
        ui.printMsg("reader " + hex(addr) + ": OK")

    def validate(self, args, ui):
        return True

    def getUsage(self):
        return (self.cmd + " " + self.descArgs).ljust(16) + self.descCmd

class UICmdInfo(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "info"
        self.descCmd = "gets reader settings (freq, power, scantime)"

    def run(self, args, reader, ui):
        msg = reader.getReaderInfo()
        ui.printMsg("address   : " + hex(msg[0]))
        ui.printMsg("low freq  : " + str(msg[1]) + " kHz")
        ui.printMsg("high freq : " + str(msg[2]) + " kHz")
        ui.printMsg("power     : " + str(msg[3]) + " dBm")
        ui.printMsg("scan time : " + str(int(msg[4])*100) + " ms")

class UICmdWorkMode(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "mode"
        self.descCmd = "gets reader work mode ()"

    def run(self, args, reader, ui):
         msg = reader.getWorkMode()
         ui.printMsg("mode              : " + msg[1])
         ui.printMsg("protocol          : " + msg[2])
         ui.printMsg("buzzer            : " + msg[3])
         ui.printMsg("addr mode         : " + msg[4])
         ui.printMsg("interface         : " + msg[5])
         ui.printMsg("storage           : " + msg[6])
         ui.printMsg("offset            : " + hex(msg[7]))
         ui.printMsg("length            : " + str(msg[8]))
         ui.printMsg("filter time       : " + str(msg[9]) + " s")
         ui.printMsg("accuracy EAS      : " + str(msg[10]))
         ui.printMsg("offset time       : " + str(msg[11]) + " ms")
         ui.printMsg("W byte order      : " + msg[12])
         ui.printMsg("W mode            : " + msg[13])
         ui.printMsg("W output interval : " + str(msg[14] * 10) + " ms")
         ui.printMsg("W pulse width     : " + str(msg[15] * 10) + " us")
         ui.printMsg("W pulse period    : " + str(msg[16] * 100) + " us")

class UICmdSetFreq(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "freq"
        self.args = 2
        self.descArgs = "LOW HIGH"
        self.descCmd = "set frequency range"

    def isFreq(self, f):
        if f.isdigit():
            if int(f) >= 902600 and int(f) <= 927400:
                if (int(f) - 902600) % 400 == 0:
                    return True

    def toFreq(self, f):
        return int((int(f) - 902600) / 400)

    def validate(self, args, ui):
        return self.isFreq(args[0]) and self.isFreq(args[1]) and int(args[0]) <= int(args[1])

    def run(self, args, reader, ui):
        self.printOk(reader.setFreq(self.toFreq(args[0]), self.toFreq(args[1])), ui)

class UICmdSetPower(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "power"
        self.args = 1
        self.descArgs = "0-30"
        self.descCmd = "sets power in dBm"
        
    def validate(self, args, ui):
        return args[0].isdigit() and (int(args[0]) >= 0 and int(args[0]) <= 30)

    def run(self, args, reader, ui):
        self.printOk(reader.setPower(int(args[0])), ui)

class UICmdSetScanTime(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "scantime"
        self.args = 1
        self.descArgs = "3-255"
        self.descCmd = "sets scan time in 100's of ms"

    def validate(self, args, ui):
        return args[0].isdigit() and (int(args[0]) >= 2 and int(args[0]) <= 255)

    def run(self, args, reader, ui):
        self.printOk(reader.setScanTime(int(args[0])), ui)

class UICmdQuit(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "quit"
        self.descCmd = "terminates this prompt"

    def run(self, args, reader, ui):
        ui.quit()


class UICmdHelp(UICmd):
    def __init__(self):
        super().__init__()
        self.cmd = "help"
        self.descCmd = "print commands and usage"

    def run(self, args, reader, ui):
        ui.puts(ui.getHelp())
 

class UI:
    def __init__(self, reader):
        self.commands = dict()
        self.addCommand(UICmdInfo())
        self.addCommand(UICmdSetPower())
        self.addCommand(UICmdHelp())
        self.addCommand(UICmdQuit())
        self.addCommand(UICmdSetFreq())
        self.addCommand(UICmdSetScanTime())
        self.addCommand(UICmdWorkMode())
        self.reader = reader
#        readline.parse_and_bind('tab: complete')
#        readline.parse_and_bind('set editing-mode vi')

    def addCommand(self, cmd):
        self.commands[cmd.cmd] = cmd

    def input(self, line):
        args = line.split(' ')
        if args[0] in self.commands:
            cmd = self.commands[args[0]]
            if len(args[1:]) == cmd.args and cmd.validate(args[1:], self):
                cmd.run(args[1:], self.reader, self)
            else:
                self.printMsg(cmd.getUsage())

    def getHelp(self):
        usage = ""
        for k, v in sorted(self.commands.items()):
            usage = usage + v.getUsage() + "\n"
        return usage

    def quit(self):
        self.printMsg("bye")
        sys.exit(0)

    def puts(self, text):
        print(text, end='')

    def printMsg(self, msg):
        print(msg)

    def run(self):
        while True:
            try:
                self.input(input('> ').strip())
            except EOFError:
                self.quit()
            except KeyboardInterrupt:
                self.printMsg('')
        

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
    MODE_ACTIVE= "active"
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


    def openPort(self, path, baud):
        self.port = path
        self.sr = serial.Serial()
        self.sr.baudrate = baud 
        self.sr.port = path
        self.sr.open()
        self.crc = crcmod.predefined.Crc('crc-16-mcrf4xx')

    def getCrc(self, msg):
        crc = self.crc.new()
        crc.update(msg)
        return crc.digest()

    def send(self, addr, cmd, args=bytes([])):
        msg = bytes([addr, cmd]) + args
        msg = bytes([len(msg) + 2]) + msg
        crc = self.getCrc(msg)
        msg = msg + bytes([crc[1], crc[0]])
        self.sr.write(msg)

    def recv(self):
        count = self.sr.read(1)
        data = self.sr.read(count[0])
        crc = data[-2:]
        calcCrc = self.getCrc(count + data[:-2])
        if crc[0] != calcCrc[1] or crc[1] != calcCrc[0]:
            raise Exception("CRC failed: " + (count + data).hex())
        return data

    def getReaderInfo(self):
        self.send(self.ADDR_BROADCAST, self.GET_READER_INFO)
        info = self.recv()
        return (info[0], info[8] * 400 + 902600, info[7] * 400 + 902600, info[9], info[10])

    def retAddr(self, data):
        return data[0]

    def setFreq(self, low, high):
        self.send(self.ADDR_BROADCAST, self.SET_FREQ, bytes([high, low]))
        return self.retAddr(self.recv())

    def setScanTime(self, time):
        self.send(self.ADDR_BROADCAST, self.SET_SCAN_TIME, bytes([time]))
        return self.retAddr(self.recv())

    def setPower(self, power):
        self.send(self.ADDR_BROADCAST, self.SET_POWER, bytes([power]))
        return self.retAddr(self.recv())

    def getWorkMode(self, addr = 0xff):
        self.send(addr, self.GET_WORK_MODE)
        recv = self.recv()
        mode = [ self.MODE_ANSWER, self.MODE_ACTIVE, self.MODE_TRIG_LOW, self.MODE_TRIG_HIGH ][recv[7]]
        chaos = recv[8]
        proto = [ self.PROTO_6C, self.PROTO_6B ][chaos & 0x1]
        buzzer = [ self.ON, self.OFF ][(chaos & 0x4) >> 2]
        addr = [ self.ADDR_WORD, self.ADDR_BYTE][(chaos & 0x8) >> 3]
        ifce = [ self.IFACE_WIEGAND, self.IFACE_SERIAL, self.IFACE_SYRIS ][((chaos & 0x10) >> 4) + ((chaos & 0x2) >> 1)]
        storage = [ self.STORAGE_PASSWD, self.STORAGE_EPC, self.STORAGE_TID, self.STORAGE_USER, self.STORAGE_MULTI_QUERY, self.STORAGE_ONE_QUERY, self.STORAGE_EAS ][recv[9]]
        offset = recv[10]
        length = recv[11]
        filter_time = recv[12]
        acc_eas = recv[13]
        offset_time = recv[14]
        w_order = [ self.MSB, self.LSB ][(recv[3] & 0x2) >> 1]
        w_type = [ self.WIEGAND_26, self.WIEGAND_34 ][recv[3] & 0x1]
        w_inter = recv[4]
        w_pulse_width = recv[5]
        w_pulse_int = recv[6]
        return (recv[0], mode, proto, buzzer, addr, ifce, storage, offset, length, filter_time, acc_eas, offset_time, w_order, w_type, w_inter, w_pulse_width, w_pulse_int)


if len(sys.argv) != 2:
    print("usage: uhf TTY_SERIAL")
    sys.exit(2)
	

uhfr = UHFReader18()
uhfr.openPort(sys.argv[1], 57600)

UI(uhfr).run()
