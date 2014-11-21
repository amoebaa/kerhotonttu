# -*- coding: iso-8859-1 -*-

import socket
import botcommands
import threading
from threading import Timer
import serial
import sys
import sched, time
import sqlite3
from datetime import datetime
from markovchain import Markov
import settings

#onkelmia: ctrl-c ei lopeta threadeja, eikä tajua reconnectata jos yhteys
#katkeaa. lisäksi ei tajua vaihtaa nikkiä jos nikki rekisteröity

# Onhan se aika perverssi
def perverse_format_datetime(orig):
    dt = datetime.strptime(orig, "%Y-%m-%d %H:%M");
    return dt.strftime("%M-%H-%d-%m-%y");

#hoitaa AVR:n kanssa kommunikoinnin
class SerialReader:

    def __init__(self):
        self.database = sqlite3.connect("rawdata.sqlite")
        self.connected = False
        self.portInUse = False
        self.done = False
        port = '/dev/ttyS0'
        baud = 9600

        self.database.execute(
            '''CREATE TABLE IF NOT EXISTS rawdata
               (aika TEXT, -- Vaatii tietyn formaatin
                lampo INTEGER, -- oispa kaljaa
                ovi INTEGER,
                valo INTEGER);''')
        self.database.commit()
        self.database.close()

        self.serial_port = serial.Serial(port, baud, parity=serial.PARITY_EVEN, timeout=None)

        self.tmr = Timer(60, self.readData, ())
        self.tmr.start()

    #lukee datat 10min välein AVR:ltä
    def readData(self):
        print "reading"
        self.portInUse = True
        self.serial_port.write("A".encode())
        self.serial_port.write(datetime.now().strftime('%S%M%H%d%m%y\r\n'))
        self.serial_port.write("D".encode())

        self.tmr = Timer(600, self.readData, ())
        self.tmr.start()

    def setBot(self, bot):
        self.bot = bot

    #katsotaan mitä sarjaportista tuli ja toimitaan sen mukaan
    def handle_data(self, data):
        self.database = sqlite3.connect("rawdata.sqlite")
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
            self.bot.sendnotice("Ovi sulkeutui.")
        elif data.startswith("ovi aukesi"):
            self.bot.sendnotice("Ovi aukesi.")
        elif data.startswith("valo pois"):
            self.bot.sendmsg("Valot ovat pois päältä.")
        elif data.startswith("valo"):
            self.bot.sendmsg("Valot ovat päällä.")
        elif data.isdigit() and len(data) < 5:
            self.bot.sendmsg("Kerhon lämpötila %s astetta." % data)
        elif data.startswith("REC"):
            c = self.database.cursor()
            data = data.split(',')
            if len(data) < 9:
                self.serial_port.write("E".encode())
                return
            try:
                c.execute('''INSERT INTO rawdata VALUES
                             (?,?,?,?);
                          ''', # konvertoidaan se oikeeks päivämääräks kantaan
                          ('20' + data[5] + '-' + data[4] + '-' + data[3] + ' ' + data[2] + ':' + data[1],
                           data[6],
                           data[7],
                           data[8]));
                self.database.commit()
                print "data inserted"
            except sqlite3.Error as e:
                    print e.message
            self.serial_port.write('K'.encode())
    #jos datan vastaanotto loppui, luodaan uusi csv webbikikkareelle
        elif data.startswith("empty"):
            self.portInUse = False
            data = []
            c = self.database.cursor()
            c.execute('''SELECT * FROM rawdata WHERE
                         aika > datetime('now','-7 days', 'localtime');''')
            data = c.fetchall()[0::10] # Slice alkaen 0:sta loppuen loppuun joka 10s

            data
            with open('public_html/data.csv', 'w') as f:
                f.write('aika,lampo,ovi,valo\n')
                print "generating csv"
                for row in data:
                    formatted_row = (
                        perverse_format_datetime(row[0]),
                        str(row[1]),
                        str(row[2]),
                        str(row[3]))
                    f.write(",".join(formatted_row) + "\n")

        else:
            print "*prööt*"

        self.database.close()

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

    def stopTimer(self):
        self.tmr.cancel()

class Ircbot:

    def __init__( self, serial, markov ):

        self.ser = serial

        self.markov = markov

        # välttämättömiä tietoja

        self.server   = settings.server
        self.port     = settings.port
        self.username = settings.name
        self.realname = settings.name
        self.nick     = settings.nick
        self.msgcount = 0

        # luodaan socket

        self.socket   = socket.socket()

        # haetaan botille komennot

        self.commands = botcommands.command_dict

        # päälooppia toistettan kunnes done = 1

        self.done     = 0

        # kanava jolle botti halutaan

        self.channel  = settings.channel

        self.tmr = Timer(60, self.clearCounter, ())
        self.tmr.start()

    #nollataan spämminestolaskuri
    def clearCounter(self):
        self.msgcount = 0
        self.tmr = Timer(60, self.clearCounter, ())
        self.tmr.start()

    def send( self, string ):

        self.socket.send( (string + '\r\n'))

    #lähettää viestin, jos lähetetty 6 viestiä minuutissa, ei tee mitään
    def sendmsg( self, string):

        if self.msgcount < 6:
            self.msgcount += 1
            self.send(('PRIVMSG %s :' % self.channel) + string)

    def sendnotice( self, string):

        if self.msgcount < 6:
            self.msgcount += 1
            self.send(('NOTICE %s :' % self.channel) + string)

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

    def generate_markov(self, word1=None, word2=None):
        if self.markov is not None:
            textmessage = ""
            if word2 is not None:
                textmessage = self.markov.generate_starting_phrase(word1, word2)
            elif word1 is not None:
                textmessage = self.markov.generate_starting_with(word1)
            else:
                textmessage = self.markov.generate_min_words(8)
            print textmessage
            self.sendmsg(textmessage)
        else:
            print "No markov module initialized!\n"

    def mainloop( self ):

        buffer = ''

        while not self.done:

            # vastaanotetaan dataa

            buffer += self.socket.recv( 4096 )
            buffer = buffer.split( '\r\n' )

            for line in buffer[0:-1]:

                self.check( line )

            buffer = buffer[-1]

        print "Suljetaan botti..."
        self.tmr.cancel()

class Input():

    def __init__(self):
        self.irc = None

    def setBot(self, irc):
        self.irc = irc
    
    def read_keyboard(self):
        
        key = ""
        if self.irc is not None:
            while True:
                key = sys.stdin.read(1)
                print key
                if key == 'q':
                    self.irc.send( 'QUIT' )
                    self.irc.socket.close()
                    self.irc.done = 1
                    break;

def main():

    serial = SerialReader()
    thread = threading.Thread(target=serial.read_from_port)
    input = Input()
    thread_input = threading.Thread(target=input.read_keyboard)
    logfile = "xcalibur.log"
    #logfile = None
    if logfile is None:
        markov = None
    else:
        markov = Markov(logfile)

    irc = Ircbot(serial, markov)
    serial.setBot(irc)
    input.setBot(irc)

    irc.connect()
    thread.start()
    thread_input.start()
    irc.mainloop()
    try:
        serial.stopTimer()
    except:
        print('serial timer could not be stopped')
    try:
        thread._Thread__stop()
    except:
        print(str(thread.getName()) + ' could not be terminated')
    try:
        thread_input._Thread__stop()
    except:
        print(str(thread_input.getName()) + ' could not be terminated')

    sys.exit()

if __name__ == '__main__': main()
