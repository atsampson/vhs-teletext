#!/usr/bin/env python

# * Copyright 2011 Alistair Buxton <a.j.buxton@gmail.com>
# *
# * License: This program is free software; you can redistribute it and/or
# * modify it under the terms of the GNU General Public License as published
# * by the Free Software Foundation; either version 3 of the License, or (at
# * your option) any later version. This program is distributed in the hope
# * that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# * warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# * GNU General Public License for more details.

import sys
import numpy as np

from util import *

class Finder(object):
    def __init__(self, match1, match2, name="", pagepos=-1, row=-1):
        self.match1 = np.fromstring(match1, dtype = np.uint8)
        self.match2 = np.fromstring(match2, dtype = np.uint8)
        self.passrank = (5+self.calculaterank(self.match1))*0.5
        self.pagepos = pagepos
        self.row = row
        self.possible_bytes = []
        self.name = name

        for n in range(42):
            c = self.match2[n]
            if c == ord('e'):
                self.possible_bytes.append([makeparity(self.match1[n])])
            elif c == ord('u'):
                self.possible_bytes.append(upperbytes)
            elif c == ord('l'):
                self.possible_bytes.append(lowerbytes)
            elif c == ord('h'):
                self.possible_bytes.append(hexbytes)
            elif c == ord('m'):
                self.possible_bytes.append(numberbytes[1:9])
            elif c >= ord('0') and c <= ord('9'):
                self.possible_bytes.append(numberbytes[:1+c-ord('0')])
            elif c == ord('D'):
                self.possible_bytes.append(day1bytes)
            elif c == ord('A'):
                self.possible_bytes.append(day2bytes)
            elif c == ord('Y'):
                self.possible_bytes.append(day3bytes)
            elif c == ord('M'):
                self.possible_bytes.append(month1bytes)
            elif c == ord('O'):
                self.possible_bytes.append(month2bytes)
            elif c == ord('N'):
                self.possible_bytes.append(month3bytes)
            elif c == ord('H'):
                self.possible_bytes.append(hammbytes)
            elif c == ord('d'):
                self.possible_bytes.append(dcbytes)
            elif c == ord('p'):
                self.possible_bytes.append(paritybytes)
            else:
                self.possible_bytes.append(allbytes)

    def findexact(self, visual):
        return ((self.match2 == ord('e')) & 
                (visual == self.match1)).sum()

    def findupper(self, visual):
        return ((self.match2 == ord('u')) & 
                (visual >= ord('A')) &
                (visual <= ord('Z'))).sum()

    def findlower(self, visual):
        return ((self.match2 == ord('l')) & 
                (visual >= ord('a')) &
                (visual <= ord('z'))).sum()

    def findnumber(self, visual):
        return ((self.match2 >= ord('0')) & 
                (self.match2 <= ord('9')) &
                (visual >= ord('0')) &
                (visual <= self.match2)).sum()

    def findmag(self, visual):
        return ((self.match2 == ord('m')) & 
                (visual >= ord('1')) &
                (visual <= ord('8'))).sum()

    def findhex(self, visual):
        return ((self.match2 == ord('h')) & 
                (((visual >= ord('0')) & (visual <= ord('9'))) |
                 ((visual >= ord('A')) & (visual <= ord('F'))) |
                 ((visual >= ord('a')) & (visual <= ord('f'))))).sum()

    def calculaterank(self, visual):
        rank = 0
        rank += self.findexact(visual)
        rank += self.findupper(visual)*0.1
        rank += self.findlower(visual)*0.1
        rank += self.findnumber(visual)*0.2
        rank += self.findmag(visual)*0.2
        rank += self.findhex(visual)*0.1
        return rank

    def find(self, packet):
        rank = 0
        self.packet = np.fromstring(packet, dtype=np.uint8)
        (self.m,self.r),e = mrag(self.packet[:2])
        if self.r == self.row:
            rank += 5
        rank += self.calculaterank(self.packet&0x7f)
        return (rank > self.passrank)

    def fixup(self):
        self.packet[0:2] = makemrag(self.m, self.row)
        for n in range(0, 42):
            if self.match2[n] == ord('e'):
                self.packet[n] = makeparity(self.match1[n])
        return "".join([chr(x) for x in self.packet])


   
BBC1 = Finder("          CEEFAX 1 217 Wed 25 Dec\x0318:29/53",
              "HHHHHHHHHHeeeeeeeeemhheDAYe39eMONe"+"29e59e59", 
              name="BBC1 Packet 0", pagepos=9, row=0)

# there are two types of broadcast packet. one has 8/4 PDC data and the other
# has no encoding (not even parity). the latter is almost impossible to 
# deconvolve so we try for the former to speed up the finder.
BBC1_BSD = Finder("\x15\xea \x15\x15\xea\xea\xea\x5e              BBC1 CEEFAX        ",
                  "e"+"e"+"de"+"e"+"e"+"e"+"e"+"e"+"HHHHHHHHHHHHHeeeeeeeeeeeeeeeeeeee", 
                  name="BBC1 Broadcast Service Data", row=30)

Generic_BSD = Finder("                       BBC1 CEEFAX        ",
                     "HHdHHHHHH             pppppppppppppppppppp", 
                     name="Broadcast Service Data", row=30)

if __name__=='__main__':

    F = BBC1

    while(True):
        tt = sys.stdin.read(42)
        if len(tt) < 42:
            exit(0)
        if F.find(tt):
            sys.stdout.write(F.fixup())
            sys.stdout.flush()