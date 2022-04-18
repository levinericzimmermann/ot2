sr     = 48000
ksmps  = 1
0dbfs  = 1
nchnls = 1


instr 1
    kcps = p4
    icontrolamp = p5
    iduration = p3
    iattack = p6 * iduration
    irelease = p7 * iduration
    isustain = iduration - iattack - irelease

    kenvelopeamp linseg 0, iattack, 1 , isustain, 1, irelease, 0

    asig poscil kenvelopeamp * icontrolamp, kcps

    out asig
endin


