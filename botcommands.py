# -*- coding: iso-8859-1 -*-

import random

# tähän sanastoon lisätään komennot ja niitä vastaavat oliot

command_dict = {}


class Test:

    def main( self, irc, line ):

        irc.send( 'PRIVMSG %s :Hello world!' % line[2] )

command_dict[ ':!test' ] = Test()


class Join:

    def main( self, irc, line):

        irc.send( 'JOIN %s' % ( line[4] ) )

command_dict[ ':!join' ] = Join()


class Quit:

    def main( self, irc , line ):
        a = 1
        #irc.send( 'QUIT' )
        #irc.socket.close()
        #irc.done = 1

command_dict[ ':!quit' ] = Quit()


class Ovi:

    def main( self, irc, line):

        irc.ser.write("O")

command_dict[ ':!ovi' ] = Ovi()

class Valo:

    def main(self, irc, line):
        
        irc.ser.write("V")
        
command_dict[ ':!valo' ] = Valo()

class Lampo:

    def main( self, irc, line):

        irc.ser.write("L")

command_dict[ ':!lampo' ] = Lampo()

class Viisaus:

    def main(self, irc, line):

        if len(line) > 4:
            irc.generate_markov(line[4])
        else:
            irc.generate_markov()

command_dict[ ':!viisaus' ] = Viisaus()