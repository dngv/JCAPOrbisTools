from pvdconv import *
pm='0033-04-0110-mp.txt'
keepcodes=[0, 1, 2]
smpmod=0
zstg=99.170
ax=26.487
ay=8.070
bx=6.533
by=27.320
cx=99.076
cy=51.220

orbPVD(pm, zstg, ax, ay, bx, by, cx, cy, keepcodes, smpmod)
#orbPVD(pm, zstg, ax, ay, bx, by, cx, cy, keepcodes)