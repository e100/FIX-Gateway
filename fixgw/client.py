#!/usr/bin/env python3

#  Copyright (c) 2018 Phil Birkelbach
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

# This module is a FIX-Net client for FIX-Gateway

from __future__ import print_function

import argparse
import threading
import socket
import readline
import cmd
import sys
import logging
logging.basicConfig()

import fixgw.netfix as netfix

# Used to print to stderr
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)



class Command(cmd.Cmd):
    def __init__(self, client):
        cmd.Cmd.__init__(self)
        self.client = client

    def do_read(self, line):
        """read [key] [value]\nRead the value from the database given the key"""
        args = line.split(" ")
        x = self.client.read(args[0])
        flags = ""
        if x[2]: # Do we have any flags?
            if 'a' in x[2]: flags += " Annuc"
            if 'o' in x[2]: flags += " Old"
            if 'f' in x[2]: flags += " Fail"
            if 'b' in x[2]: flags += " Bad"

        print(x[1]+flags)

    def do_write(self, line):
        """write [key] [value]\nWrite Value into Database with given key"""
        args = line.split(" ")
        if len(args) < 2:
            print("Missing Argument")
        else:
            self.client.write(*args)

    def do_list(self, line):
        """list\nList Database Keys"""
        print("List")

    def do_report(self, line):
        """Report [key]\nDetailed item information report"""
        args = line.split(" ")
        print("Report({})".format(str(args)))
        # try:
        #     x = self.plugin.db_get_item(args[0])
        #     print(x.description)
        #     print("Type:  {0}".format(x.typestring))
        #     print("Value: {0}".format(str(x.value[0])))
        #     print("Q:     {0}".format(str(x.value[1:])))
        #     print("Min:   {0}".format(str(x.min)))
        #     print("Max:   {0}".format(str(x.max)))
        #     print("Units: {0}".format(x.units))
        #     print("TOL:   {0}".format(str(x.tol)))
        #     print("Auxillary Data:")
        #     for each in x.aux:
        #         if each: print("  {0} = {1}".format(each,str(x.aux[each])))
        #     for each in x.callbacks:
        #         print("Callback function defined: {0}".format(each[0]))
        # except KeyError:
        #     print(("Unknown Key " + args[0]))

    def do_poll(self, line):
        """Poll\nContinuously prints updates to the given key"""
        args = line.split(" ")
        print("Subscribe({})".format(str(args)))
        # try:
        #     self.plugin.db_callback_add(args[0], self.callback_function)
        # except KeyError:
        #     print(("Unknown Key " + args[0]))

    # def do_unsub(self, line):
    #     """Unsubscribe\nRemove subscription to updates"""
    #     args = line.split(" ")
    #     print("Unsubscribe({})".format(str(args)))
    #     # try:
        #     self.plugin.db_callback_del(args[0])
        # except KeyError:
        #     print(("Unknown Key " + args[0]))

    def do_stop(self, line):
        """Stop\nStop polling the item"""
        args = line.split(" ")
        print("Stop({})".format(str(args)))


    def do_flag(self, line):
        """flag [key] [abfs] [true/false]\nSet or clear quality flags"""
        args = line.split(" ")
        print("flag({})".format(str(args)))
        # if len(args) < 3:
        #     print("Not Enough Arguments") # TODO print usage??
        #     return
        # try:
        #     x = self.plugin.db_get_item(args[0])
        # except KeyError:
        #     print("Unknown Key " + args[0])
        # bit = True if args[2].lower() in ["true", "high", "1", "yes"] else False
        # if args[1].lower()[0] == 'b':
        #     x.bad = bit
        # elif args[1].lower()[0] == 'f':
        #     x.fail = bit
        # elif args[1].lower()[0] == 'a':
        #     x.annunciate = bit
        # elif args[1].lower()[0] == 's':
        #     x.secondary = bit

    def do_status(self, line):
        """status\nRead status information"""
        # print(status.get_string())
        print("Status")

    def do_quit(self, line):
        """quit\nExit Plugin"""
        return True

    def do_exit(self, line):
        """exit\nExit Plugin"""
        return self.do_quit(line)

    def do_EOF(self, line):
        return True


def main():
    parser = argparse.ArgumentParser(description='FIX Gateway')
    parser.add_argument('--debug', action='store_true',
                        help='Run in debug mode')
    parser.add_argument('--host', '-H', default='localhost',
                        help="IP address or hostname of the FIX-Gateway Server")
    parser.add_argument('--port', '-P', type=int, default=3490,
                        help="Port number to use for FIX-Gateway Server connection")
    parser.add_argument('--prompt', '-p', default='FIX: ',
                        help="Command line prompt")
    parser.add_argument('--file', '-f', nargs=1, metavar='FILENAME',
                        help="Execute commands within file")
    parser.add_argument('--execute','-x', nargs='+', help='Execute command')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Keep running after commands are executed')
    args, unknown_args = parser.parse_known_args()

    if args.debug:
        log.level = logging.DEBUG

    c = netfix.Client(args.host, args.port)
    c.connect()

    cmd = Command(c)
    # If commands are beign redirected or piped we set the prompt to nothing
    if sys.stdin.isatty():
        cmd.prompt = args.prompt
    else:
        cmd.prompt = ""
    cmd.cmdloop()

    c.disconnect()


if __name__ == '__main__':
    main()