# -*- coding: iso-8859-1 -*-

import socket
import botcommands
import threading
from threading import Timer
import serial
import sys
import sched, time
import sqlite3
from datetime import datetime, timedelta
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
        self.wisdomlimit = settings.wisdomlimit
        self.wisdomssaid = 0
        self.minutetimer = 0
        self.msgcount = 0
        self.privmsgcount = 0
        self.connected = False
        self.reconnectioninterval = timedelta(0, 0, 0, 0, 5) # 5 minutes
        self.lastconnection = datetime(2015, 1, 1) # Arbitrary date in the past

        # luodaan socket

        self.socket   = None

        # haetaan botille komennot

        self.commands = botcommands.command_dict

        # päälooppia toistettan kunnes done = 1

        self.done     = 0

        # kanava jolle botti halutaan

        self.channel  = settings.channel

        self.tmr = Timer(60, self.minuteTimer, ())
        self.tmr.start()

    #nollataan spämminestolaskuri + viisauslaskuri + yritetään ottaa nicki takas
    def minuteTimer(self):
        self.msgcount = 0
        self.privmsgcount = 0
        self.minutetimer += 1
        if self.minutetimer % 5 == 0 and not self.connected:
            self.connect()
        if self.minutetimer % 10 == 0:
            if self.connected and self.nick != settings.nick:
                self.send('NICK %s' % settings.nick)
        if (self.minutetimer >= 720):
            self.minutetimer = 0
            self.wisdomssaid = 0
        self.tmr = Timer(60, self.minuteTimer, ())
        self.tmr.start()

    def send( self, string ):

        if not self.socket is None:
            try:
                self.socket.send( (string + '\r\n'))
            except socket.error:
                print "Unable to send " + string

    def sendprivmsg(self, target, string):
    
        if self.privmsgcount < 10:
            self.privmsgcount += 1
            self.send(('PRIVMSG %s :' % target) + string)
        
    #lähettää viestin, jos lähetetty 6 viestiä minuutissa, ei tee mitään
    def sendmsg( self, string):

        if self.msgcount < 6:
            self.msgcount += 1
            self.send(('PRIVMSG %s :' % self.channel) + string)

    def sendnotice( self, string):

        self.send(('NOTICE %s :' % self.channel) + string)

    def connect( self ):

        if (self.lastconnection + self.reconnectioninterval) < datetime.now():
            try:
                self.lastconnection = datetime.now()
                self.socket = socket.socket()
                self.socket.connect( ( self.server, self.port ) )
                self.send( 'NICK %s' % self.nick )
                self.send( 'USER %s a a :%s' % ( self.username, self.realname ) )

                self.send( 'JOIN %s' % self.channel )
            
            except socket.error:
                print "Error connecting to " + self.server + ":" + str(self.port) + "!"

    def check( self, line ):

        print line
        line = line.split(' ')

        # vastataan pingiin muuten serveri katkaisee yhteyden

        if line[0] == 'PING':

             self.send( 'PONG :abc' )

        elif len(line) > 1:
            if (line[1] == '437' or line[1] == '433'):
                if self.connected == False:
                    if self.nick == settings.nick2:
                        # Try again later
                        self.send( 'QUIT' )
                        self.nick = settings.nick
                        print "Unable to use " + settings.nick + " or " + settings.nick2 + ", trying again later"
                    else:
                        self.nick = settings.nick2
                        self.send( 'NICK %s' % self.nick )
                        self.send( 'JOIN %s' % self.channel )
            elif (line[1] == '366'): # we've joined a channel
                self.connected = True
            elif line[1] == 'NICK':
                self.nick = line[2][1:]
            else:
                try:
                
                    if line[2] == self.nick:
                        target = line[0][1:line[0].find('!')]
                        self.commands[ line[3] ].main( self , line, target)
                        return
                    if line[2] == self.channel:
                        if line[3][1] != '!':
                            self.markov.learn(line[3:])

                        # suoritetaan komennot jos niitä on tullut

                        self.commands[ line[3] ].main( self , line , None)

                except:

                    pass

    def set_limit(self, limit):
        self.wisdomlimit = limit
    
    def wisdom(self, word1=None, word2=None, target=None):        
        if (target is None):
            if self.wisdomlimit > 0 and self.wisdomssaid > self.wisdomlimit:
                return
            self.wisdomssaid += 1
        textmessage = self.generate_markov(word1, word2)
        if (target is None):
            self.sendmsg(textmessage)
        else:
            self.sendprivmsg(target, textmessage)
        
            
    def generate_markov(self, word1=None, word2=None):        
        if self.markov is not None:
            textmessage = ""
            if word2 is not None:
                textmessage = self.markov.generate_starting_phrase(word1, word2)
            elif word1 is not None:
                textmessage = self.markov.generate_min_words_starting_with(word1)
            else:
                textmessage = self.markov.generate_min_words(8)
            print textmessage
            return textmessage
        else:
            print "No markov module initialized!\n"

            
    def mainloop( self ):

        buffer = ''

        while not self.done:
            
            # vastaanotetaan dataa
            try:
                if not self.socket is None:
                    newline = self.socket.recv( 4096 )
                    if len(newline) == 0:
                        if self.connected == True:
                            print "Disconnected from server!"
                        self.connected = False
                    else:
                        buffer += newline
                        buffer = buffer.split( '\r\n' )

                        for line in buffer[0:-1]:

                            self.check( line )

                        buffer = buffer[-1]
                
            except socket.error:
                
                if self.connected == True:
                    print "Disconnected from server!"
                self.connected = False

        print "Suljetaan botti..."
        self.tmr.cancel()

class Input():

    def __init__(self):
        self.irc = None

    def setBot(self, irc):
        self.irc = irc
    
    def read_keyboard(self):
        
        command = ""
        if self.irc is not None:
            while True:
                command = sys.stdin.readline().lower().rstrip().split(' ')
                if self.irc.connected:
                    if command[0] == 'quit':
                        self.irc.send( 'QUIT' )
                        self.irc.socket.close()
                        self.irc.done = 1
                        break;
                    elif command[0] == 'viisaus':
                        if len(command) == 1:
                            self.irc.wisdom()
                        elif len(command) == 2:
                            self.irc.wisdom(command[1])
                        else:
                            self.irc.wisdom(command[1], command[2])
                    elif command[0] == 'limit' and len(command) > 1:                    
                        try:
                            val = int(command[1])
                            self.irc.set_limit(val)
                            print "Limit is now " + command[1]
                        except ValueError:
                            print command[1] + " is not an integer!"
                    elif command[0] == 'say' and len(command) > 1:
                        self.irc.sendmsg(' '.join(command[1:]))
                    elif command[0] == 'cmd' and len(command) > 1:
                        self.irc.send(' '.join(command[1:]))

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
