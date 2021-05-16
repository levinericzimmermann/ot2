sr     = 48000
ksmps  = 1
0dbfs  = 1
nchnls = 1


instr 1
    asig0, asig1 diskin2 p4, 1, 0
    out (asig0 + asig1) * 0.5 * p5
endin
