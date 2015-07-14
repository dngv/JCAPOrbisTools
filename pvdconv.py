from readplatemap import readsingleplatemaptxt
import struct, binascii
import numpy as np


# generates stage file with same name as platemap, .stg extension
def orbPVD(pm, zstg, ax, ay, bx, by, cx, cy, keepcodes=[], smpmod=0):
    if not 0<=zstg<=100:
        print 'Invalid z-height'

    else:
        # assume pm in current working directory
        dlist=readsingleplatemaptxt(pm)

        # ax, ay, bx, by, cx, cy : x-coord, y-coord (orbis convention +x left)
        # a=point on left side of wafer flat, b=point on right side of wafer flat, c=leftmost point on wafer edge, cannot be on flat

        # correct x-axis mirror
        ax=np.float32(100-ax)
        bx=np.float32(100-bx)
        cx=np.float32(100-cx)

        # Orbis x & y diffs (origin sample A)
        sabx=np.float32(bx-ax)
        saby=np.float32(by-ay)

        # Si wafer diameter
        dia=99.5
        rad=np.float32(dia/2)
        flat=2.73
        pym=np.float32((dia-flat)/2)

        rot=np.arctan(saby/sabx)

        # stage rotation origin = (cx+rad, cy) -- because cy is leftmost point on wafer edge, should be at y=rad
        rox=np.float32(cx+rad)
        roy=np.float32(cy)

        # y-position of rotated A-B line parallel to x-axis, this is platemap y=0
        yoff=np.float32(roy+(ax-rox)*np.sin(-rot)+(ay-roy)*np.cos(-rot))
        xoff=np.float32(cx)
        

        print('rotation = ' + "{:.3f}".format(rot) + ', y-offset = ' + "{:.3f}".format(yoff))
        	
        # empty strings
        index=''
        positions=''

        # assemble long strings of bytes (as hex) then unhexlify and write to binary file                
        seperator='0000DD24664052B8884298AEC04285EBB140BE9F3A40486186422F1DC242C3F590400000'
        seperator=seperator+(struct.pack('x')*60).encode('hex')

        counter=0

        for d in dlist:
            if len(keepcodes)!=0:
                if d['code'] not in keepcodes:
                    continue
            if smpmod > 0 and d['Sample']%smpmod > 0:
                continue

            # rotate around platemap center
            xn=np.float32(d['x']-rad)
            yn=np.float32(d['y']-pym)
            xr=np.float32(xn*np.cos(rot)-yn*np.sin(rot)+rad)
            yr=np.float32(xn*np.sin(rot)+yn*np.cos(rot)+pym)

            # offset by rotated stage diffs
            xstg=np.float32(100-xr+xoff)
            ystg=np.float32(yr+yoff)

            checkx=0<=xstg<=100
            checky=0<=ystg<=100

            if checkx and checky:
                counter+=1
                i=struct.pack('<h', counter)# entry index (16-bit short?, 2 bytes), don't use sample number in case we remove out-of-range samples
                i+=struct.pack('<h', 0) # entry type (00 for point, 01 for line, 02 for matrix)
                i+=struct.pack('<h', 1)*2   # (1) num points to scan (01 for point, for line length, matrix width)
                                            # (2) num points to scan (01 for point & line, matrix height)
                l=str(int(d['Sample']))+' '*(16-len(str(int(d['Sample'])))) # use sample number for stage label, max 16 characters
                i=binascii.hexlify('Center  '+l)+i.encode('hex')
                x=struct.pack('<f', xstg)
                y=struct.pack('<f', ystg)
                z=struct.pack('<f', zstg)
                p=x+y+x+y+z+z # x start, y start, x end, y end, z start, z end
                p+=struct.pack('x')*4 # 4 byte padding (probably for rotation info but our stage doesn't have that)
                p=p.encode('hex')
                index+=i
                positions+=p

        # form header string, need to know # of in-range samples so this comes after for loop
        header=struct.pack('<b',15)
        header+=struct.pack('x')*15
        header+=struct.pack('x')*2
        header+=struct.pack('<h', counter)
        header+=struct.pack('x')*20
        header=header.encode('hex')

        # concatenate hex string and convert to byte code
        bytecode=binascii.unhexlify(header+index+seperator+positions)

        #os.chdir('/home/dan/code/orbisTools')
        stgout=pm[:-3]+'stg'
        f=open(stgout, mode='wb') # writing binary
        f.write(bytecode)
        f.close()
        print('Wrote ' + stgout + ' with ' + str(counter) + ' locations.')