sr     = 48000
ksmps  = 1
0dbfs  = 1
nchnls = 1


instr 1
    kcps = p4
    icontrolamp = p5
    iattack = p3 * p6
    irelease = p3 * p7
    isustain = p3 - iattack - irelease

    kenvelopeamp linseg 0, iattack, 1 , isustain, 1, irelease, 0

    asig poscil kenvelopeamp * icontrolamp, kcps
    asigHigh poscil kenvelopeamp * icontrolamp, kcps * 4

    out asig + (asigHigh * 0.2)
endin


