from readplatemap import readsingleplatemaptxt
import struct, binascii, math


# generates stage file with same name as platemap, .stg extension
#def orbPM(pm, zstg, xoff=0, yoff=0):
def orbPVD(pm, zstg, ax, ay, bx, by, cx, cy, keepcodes=[0], smpmod=0):
    if not 0<=zstg<=100:
        print 'Invalid z-height'
        
    else:
        # assume pm in current working directory
        dlist=readsingleplatemaptxt(pm)
        
        #ax, ay, bx, by, cx, dy : x-coord, y-coord (orbis convention +x left)
        #a=point on left side of wafer flat, b=point on right side of wafer flat, c=leftmost point on wafer edge, cannot be on flat
        
        #Orbis x & y diffs (origin sample A)
        sbax=ax-bx
        sbay=by-ay
        
        # Si wafer height/2
        hh=47.3
        # Si wafer width/2
        hw=50
        
        rab=math.atan(sbay/sbax)
        rot=rab
        yoff=cy-hh

        print('rotation = ' + "{:.3f}".format(rot) + ', y-offset = ' + "{:.3f}".format(yoff))
			
        # empty strings
        index=''
        positions=''
        
        # assemble long strings of bytes (as hex) then unhexlify and write to binary file                
        seperator='0000DD24664052B8884298AEC04285EBB140BE9F3A40486186422F1DC242C3F590400000'
        seperator=seperator+(struct.pack('x')*60).encode('hex')
        
        counter=0
        
        for d in dlist:
            if d['code'] not in keepcodes:
              continue
            if smpmod > 0 and d['Sample']%smpmod > 0:
              continue
            
            # # rotate around pm center
            xn=d['x']-hw
            yn=d['y']-hh
            xr=xn*math.cos(rot)-yn*math.sin(rot)+hw # rotate first
            yr=xn*math.sin(rot)+yn*math.cos(rot)+hh

            # # offset pm by point C coord
            xstg=cx-xr
            ystg=yoff+yr
            
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