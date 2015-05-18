# -*- coding: iso-8859-1 -*-

import random

# tähän sanastoon lisätään komennot ja niitä vastaavat oliot

command_dict = {}


class Test:

    def main( self, irc, line, target ):

        irc.send( 'PRIVMSG %s :Hello world!' % line[2] )

command_dict[ ':!test' ] = Test()


class Join:

    def main( self, irc, line, target):

        irc.send( 'JOIN %s' % ( line[4] ) )

command_dict[ ':!join' ] = Join()


class Quit:

    def main( self, irc , line, target):
        if irc.connected:
            irc.send( 'QUIT' )
        try:
            irc.socket.close()
        except:
            print "Error closing connection"
        irc.done = 1

command_dict[ ':!quit' ] = Quit()


class Ovi:

    def main( self, irc, line, target):

        if target is None:
            irc.ser.write("O")

command_dict[ ':!ovi' ] = Ovi()


class Stats:
    
    def main(self, irc, line, target):
        irc.sendprivmsg(target, "Tilastoja löytyy osoitteesta http://xcalibur.cc.tut.fi/~mikael/stats.html")
    
command_dict[ ':!stats'] = Stats()

class Valo:

    def main(self, irc, line, target):
        if target is None:
            irc.ser.write("V")
        
command_dict[ ':!valo' ] = Valo()

class Lampo:

    def main( self, irc, line, target):
        if target is None:
            irc.ser.write("L")

command_dict[ ':!lampo' ] = Lampo()

class Viisaus:
    
    def main(self, irc, line, target):

        if len(line) > 5 and len(line[5]) > 0:
            irc.wisdom(line[4], line[5], target=target)
        elif len(line) > 4 and len(line[4]) > 0:
            irc.wisdom(line[4], target=target)
        else:
            irc.wisdom(target=target)

command_dict[ ':!viisaus' ] = Viisaus()
