#!/usr/bin/python
"""
Convert an arbitrary string into asm push instructions

Copyright (C) 2010 st0w <st0w@st0w.com>

This is released under the MIT License... Do with this whatever the
hell you want, I don't care.

I started this in perl, but really, python is much better. I know what
my variable types are, why do you keep assuming you know better than
me, perl?
"""
# ---*< Standard imports >*---------------------------------------------------
import sys

# ---*< Initialization >*-----------------------------------------------------
def scrusage():
    sys.stderr.write("Usage %s 'string to convert to ASM push instructions.' "
                                    "string2\n (Separate strings with spaces, contain single "
                                    "strings with whitespace in quotes)\n" % sys.argv[0])
    sys.exit(1)

if len(sys.argv) < 2:
    scrusage()

# ---*< Code >*---------------------------------------------------------------
print "BITS 32"
print "; Push string \"" + sys.argv[1] + "\" on stack\n"
print "xor eax,eax\t; Clear EAX"
print "push eax\t; Place NULL terminator on stack\n"

strh = ''
strc = ''
strco = ''
print "; Little-Endian notation"
for i, v in enumerate(reversed(sys.argv[1])):
    strh += "%02x" % ord(v)
    if v == '\n':
        strc += "\\n"
        strco = "\\n" + strco
    else:
        strc += v
        strco = v + strco

    if (i == (len(sys.argv[1]) - 1)) and ((i % 4) != 3) :
        """If we're at the last byte, which is NOT a four byte boundary"""
        while len(strc) < 4:
            strc += '*'            # Pad with '*' chars to reach word boundary
            strco = '*' + strco
            strh += "%02x" % ord('*')

    if (i % 4) == 3 or (i == (len(sys.argv[1]) - 1)) :
        """If we're at the fourth byte, or the last byte which is also a four byte
        boundary
        """
        print "push 0x" + strh + "\t; " + strc + ' == ' + strco
        strh = ''
        strc = ''
        strco = ''

print

"""
Now also take into account that if the last word pushed was not four
even bytes that ESP does NOT refer to the start of the string.    
Instead, it refers to null bytes.    Which would somewhat defeat the
purpose of pushing a string onto the stack.    So if that's the case,
adjust ESP accordingly before copying the value into ECX.
"""
sys.stdout.write("mov ecx,esp\t; ECX now contains the address of the "
                                "string.    Have a nice day. :)\n")

if len(sys.argv[1]) % 4:
    sys.stdout.write("add cl,%s\t; Adjust ECX to point to the start of the "
                                    "string, past leading '*' pads @ ESP\n" %
                                    str(4 - len(sys.argv[1]) % 4))
