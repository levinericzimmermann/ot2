sr     = 48000
ksmps  = 1
0dbfs  = 1
nchnls = 2


instr 1
    kcps = p4
    icontrolamp = p5
    iattack = p6
    isustain = p7
    irelease = p8

    kenvelopeamp linseg 0, iattack, 1 , isustain, 1, irelease, 0

    imode init 2
    ; kpw init 0.2

    krandfreq0 randomi 80, 1200, 3.64
    krandfreq1 randomi 80, 1000, 6

    krandAmp0 randomi 0.7, 1, 0.7
    krandAmp1 randomi 0.75, 1, 1.6

    asig0 vco2 icontrolamp * kenvelopeamp * krandAmp0, kcps, imode, 0.4, 0, 0.1
    asig1 vco2 icontrolamp * kenvelopeamp * krandAmp1, kcps, 0, 0.4, 0, 0.1

    ares0 butterlp asig0, krandfreq0
    ares1 butterlp asig1, krandfreq1

    out ares0, ares1
endin


instr 100
    kcps = p4
    icontrolamp = p5

    kenvelopeamp linseg 0, 5, 1 , p3 - 9, 1, 4, 0

    imode init 2
    ; kpw init 0.2

    krandfreq0 randomi 240, 10000, 3.64
    krandfreq1 randomi 240, 10000, 6

    krandAmp0 randomi 0.1, 1, 8
    krandAmp1 randomi 0.1, 1, 9.6

    asig0 vco2 icontrolamp * kenvelopeamp * krandAmp0, kcps, imode, 0.4, 0, 0.1
    asig1 vco2 icontrolamp * kenvelopeamp * krandAmp1, kcps, 0, 0.4, 0, 0.1

    ares0 butterlp asig0, krandfreq0
    ares1 butterlp asig1, krandfreq1

    out ares0, ares1
endin
