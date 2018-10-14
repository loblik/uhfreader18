#!/usr/bin/env python3

import crcmod.predefined
import readline
import serial
import sys

class UICmd:
    def __init__(self):
        self.descArgs = ""
        self.args = 0

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
        ui.printMsg("addres    : " + hex(msg[0]))
        ui.printMsg("low freq  : " + str(msg[1]) + " MHz") 
        ui.printMsg("high freq : " + str(msg[2]) + " MHz")
        ui.printMsg("power     : " + str(msg[3]) + " dBm")
        ui.printMsg("scan time : " + str(msg[4]) + " s")

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
        reader.setPower(int(args[0]))
        return

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
        self.reader = reader

        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')

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
        for k, v in self.commands.items():
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
                self.input(input('> '))
            except EOFError:
                self.quit()
        

class UHFReader18:
    GET_READER_INFO = 0x21
    SET_POWER = 0x2f
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
        # TODO: check CRC and reply status (byte 3)
        return data

    def getReaderInfo(self):
        self.send(self.ADDR_BROADCAST, self.GET_READER_INFO)
        info = self.recv()
        return (info[0], info[8] * 0.4 + 902.6, info[7] * 0.4 + 902.6, info[9], info[10])

    def setPower(self, power):
        self.send(self.ADDR_BROADCAST, self.SET_POWER, bytes([power]))
        reply = self.recv()
        #print(reply.hex())
        return


uhfr = UHFReader18()

uhfr.openPort("/dev/ttyUSB1", 57600)

UI(uhfr).run()

