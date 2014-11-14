# -*- coding: iso-8859-1 -*-

import socket
import botcommands
import threading
from threading import Timer
import serial
import sys
import sched, time
from datetime import datetime

#onkelmia: ctrl-c ei lopeta threadeja, eikä tajua reconnectata jos yhteys
#katkeaa. lisäksi ei tajua vaihtaa nikkiä jos nikki rekisteröity


#hoitaa AVR:n kanssa kommunikoinnin
class SerialReader:

    def __init__(self):
        self.connected = False
        self.portInUse = False
        port = '/dev/ttyS0'
        baud = 9600
        
        self.serial_port = serial.Serial(port, baud, parity=serial.PARITY_EVEN, timeout=None)
        
        Timer(60, self.readData, ()).start()
        
    
    #lukee datat 10min välein AVR:ltä
    def readData(self):
        print "reading"
        self.portInUse = True
        self.serial_port.write("A".encode())
        self.serial_port.write(datetime.now().strftime('%S%M%H%d%m%y\r\n'))
        self.serial_port.write("D".encode())
        
        Timer(600, self.readData, ()).start()
    
    def setBot(self, bot):
        self.bot = bot
    
    #katsotaan mitä sarjaportista tuli ja toimitaan sen mukaan
    def handle_data(self, data):
        data = data.strip('\n')
        data = data.strip('\r')
        #jostain syystä linuxilla sarjaportista luettuun dataan
        #tuli rivin alkuun jotain kakkaa, poistetaan se
        if ord(data[0]) > 128:
            data = data[1:]
        print data
        if data.startswith("auki"):
            self.bot.sendmsg("Ovi on auki.")
        elif data.startswith("kiinni"):
            self.bot.sendmsg("Ovi on kiinni.")
        elif data.startswith("ovi sulkeutui"):
            self.bot.sendmsg("Ovi sulkeutui.")
        elif data.startswith("ovi aukesi"):
            self.bot.sendmsg("Ovi aukesi.")
        elif data.startswith("valo pois"):
            self.bot.sendmsg("Valot ovat pois päältä.")
        elif data.startswith("valo"):
            self.bot.sendmsg("Valot ovat päällä.")
        elif data.isdigit() and len(data) < 5:
            self.bot.sendmsg("Kerhon lämpötila %s astetta." % data)
        elif data.startswith("REC"):
            with open('rawdata.csv', 'a') as f:
                data = data.split(',')
                if len(data) < 9:
                    self.serial_port.write("E".encode())
                    return
                f.write(data[1] + '-' + data[2] + '-' + data[3] + '-' + data[4] + '-' + data[5] +
                        ',' + data[6] + ',' + data[7] + ',' + data[8] + '\n')
                self.serial_port.write('K'.encode())
        #jos datan vastaanotto loppui, luodaan uusi csv webbikikkareelle
        elif data.startswith("empty"):
            self.portInUse = False
            data = []
            with open('rawdata.csv') as f:
                data = f.readlines()[1:][-10800::10]
            
            data
            with open('public_html/data.csv', 'w') as f:
                f.write('aika,lampo,ovi,valo\n')
                for row in data:
                    f.write(row)
            
        else:
            print "*prööt*"
    def read_from_port(self):
        print "reading\n"
        while not self.connected:
            self.connected = True
            
            while True:
                reading = self.serial_port.readline()
                self.handle_data(reading)
    def write(self, string):
        if not self.portInUse:
            self.serial_port.write(string)

class Ircbot:

    def __init__( self, serial ):

        self.ser = serial

        # välttämättömiä tietoja

        self.server   = 'irc.cc.tut.fi'
        self.port     = 6667
        self.username = 'Kerhotonttu'
        self.realname = 'Kerhotonttu'
        self.nick     = 'Kerhotonttu'
        self.msgcount = 0

        # luodaan socket

        self.socket   = socket.socket()

        # haetaan botille komennot

        self.commands = botcommands.command_dict

        # päälooppia toistettan kunnes done = 1

        self.done     = 0

        # kanava jolle botti halutaan

        self.channel  = '#xcalibur'
        
        Timer(60, self.clearCounter, ()).start()
        
    #nollataan spämminestolaskuri
    def clearCounter(self):
        self.msgcount = 0
        Timer(60, self.clearCounter, ()).start()

    def send( self, string ):

        self.socket.send( (string + '\r\n'))
    
    #lähettää viestin, jos lähetetty 6 viestiä minuutissa, ei tee mitään
    def sendmsg( self, string):
        
        if self.msgcount < 6:
            self.msgcount += 1
            self.send(('PRIVMSG %s :' % self.channel) + string)

    def connect( self ):

        self.socket.connect( ( self.server, self.port ) )
        self.send( 'NICK %s' % self.nick )
        self.send( 'USER %s a a :%s' % ( self.username, self.realname ) )

        self.send( 'JOIN %s' % self.channel )

    def check( self, line ):

        print line
        line = line.split(' ')

        # vastataan pingiin muuten serveri katkaisee yhteyden

        if line[0] == 'PING':

             self.send( 'PONG :abc' )

        try:

            if line[2][0] != '#':

                return

            # suoritetaan komennot jos niitä on tullut

            self.commands[ line[3] ].main( self , line )

        except:

            pass

    def mainloop( self ):

        buffer = ''

        while not self.done:

            # vastaanotetaan dataa

            buffer += self.socket.recv( 4096 )
            buffer = buffer.split( '\r\n' )

            for line in buffer[0:-1]:
                
                self.check( line )

            buffer = buffer[-1]

def main():

    serial = SerialReader()
    thread = threading.Thread(target=serial.read_from_port)

    irc = Ircbot(serial)
    serial.setBot(irc)
    irc.connect()
    thread.start()
    irc.mainloop()
    try:
        thread._Thread__stop()
    except:
        print(str(thread.getName()) + ' could not be terminated')
    
    sys.exit()
    
if __name__ == '__main__': main()
