from readplatemap import readsingleplatemaptxt
import struct, binascii, math


# generates stage file with same name as platemap, .stg extension
#def orbPM(pm, zstg, xoff=0, yoff=0):
def orbPM(pm, zstg, xtweak, a, ax, ay, b, bx, by, c, cx, cy, keepcodes=[0]):
#    xorg=100-xtweak #tweak the left edge origin (orbis motor can travel ~101mm +x)
    if not 0<=zstg<=100:
        print 'Invalid z-height'
    else:
        # assume pm in current working directory
        dlist=readsingleplatemaptxt(pm)
        
        #a, ax, ay, b, bx, by, c, cx, cy : sample, x-coord, y-coord (orbis convention +x left)
        #a=origin, b=+ydiff, c=+xdiff (a-b and a-c vectors must be orthogonal)
        slist=[i['Sample'] for i in dlist]
        aind=slist.index(a)
        bind=slist.index(b)
        cind=slist.index(c)
        
        #PM coords        
        pax=dlist[aind]['x']
        pay=dlist[aind]['y']
        pbx=dlist[bind]['x']
        pby=dlist[bind]['y']
        pcx=dlist[cind]['x']
        pcy=dlist[cind]['y']
        
        #PM x & y diffs (origin sample A)
        pabx=pbx-pax
        paby=pby-pay
        pab=(pabx**2+paby**2)**0.5
        pacx=pcx-pax
        pacy=pcy-pay
        pac=(pacx**2+pacy**2)**0.5
        
        #Orbis x & y diffs (origin sample A)
        sabx=ax-bx
        saby=by-ay
        sab=(sabx**2+saby**2)**0.5
        sacx=ax-cx
        sacy=cy-ay
        sac=(sacx**2+sacy**2)**0.5
        
        rac=math.atan(sacy/sacx)
        rab=math.atan(sabx/saby)
        rot=rac #epson printer has non-linear elongation in y, use x instead

        skx=sac/pac
        sky=sab/pab
        
        print('x_skew = ' + str(skx) + ', y_skew = ' + str(sky) + ' , rot = ' + str(rot))
			
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
            xn=d['x']-pax
            yn=d['y']-pay
            
            xr=xn*math.cos(rot)-yn*math.sin(rot) # rotate first
            yr=xn*math.sin(rot)+yn*math.cos(rot)
            
            xsk=xr*skx # skew rotated coord
            ysk=yr*sky
            
            xstg=ax-xsk+xtweak
            ystg=ay+ysk
            
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