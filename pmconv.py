from readplatemap import readsingleplatemaptxt
import struct, binascii, math


# generates stage file with same name as platemap, .stg extension
#def orbPM(pm, zstg, xoff=0, yoff=0):
def orbPM(pm, zstg, xtweak, a, ax, ay, b, bx, by, c, cx, cy):
    #xorg=100-xtweak #tweak the left edge origin (orbis motor can travel ~101mm +x)
    if not 0<=zstg<=100:
        print 'Invalid z-height'
    else:
        # assume pm in current working directory
        dlist=readsingleplatemaptxt(pm)
        
        #a, ax, ay, b, bx, by, c, cx, cy : sample, x-coord, y-coord (orbis convention +x left)
        
        #PM coords        
        pax=dlist[a-1]['x']
        pay=dlist[a-1]['y']
        pbx=dlist[b-1]['x']
        pby=dlist[b-1]['y']
        pcx=dlist[c-1]['x']
        pcy=dlist[c-1]['y']
        
        #PM x & y diffs (origin sample A)
        pabx=pbx-pax
        paby=pby-pay
        pab=(pabx**2+paby**2)**0.5
        pacx=pcx-pax
        pacy=pcy-pay
        pac=(pacx**2+pacy**2)**0.5
        
        #Orbis x & y diffs (origin sample A)
        #sabx=(xorg-bx)-(xorg-ax)
        sabx=ax-bx
        saby=by-ay
        sab=(sabx**2+saby**2)**0.5
        #sacx=(xorg-cx)-(xorg-ax)
        sacx=ax-cx
        sacy=cy-ay
        sac=(sacx**2+sacy**2)**0.5
        
        # calc rotations first SAS
        psab=((pabx-sabx)**2+(paby-saby)**2)**0.5
        psac=((pacx-sacx)**2+(pacy-sacy)**2)**0.5
        
        abangle=(pab**2+sab**2-psab**2)/(2*pab*sab)
        #signrab=math.asin(saby/sab)-math.asin(paby/pab)
        rab=math.acos(abangle)
        
        acangle=(pac**2+sac**2-psac**2)/(2*pac*sac)
        #signrac=math.asin(sacy/sac)-math.asin(pacy/pac)
        rac=math.acos(acangle)
        
        if sabx*(saby-paby)>=0:
            rotsign=1
        else:
            rotsign=-1
        
        #rot=(rab+rac)/2
        rot=min(rab,rac)*rotsign
        
        #if signrab+signrac>0:
          #rot=(rab+rac)/2
          #rot=min(rab,rac)
        #else:
          #rot=-(rab+rac)/2
          #rot=-min(rab,rac)
        
        # calc skews on rotated platemap
        skxab=sabx/(pabx*math.cos(rot)-paby*math.sin(rot))
        skyab=saby/(pabx*math.sin(rot)+paby*math.cos(rot))
        
        skxac=(pacx*math.cos(rot)-pacy*math.sin(rot))/sacx
        skyac=(pacx*math.sin(rot)+pacy*math.cos(rot))/sacy

        if abs(sabx)>abs(sacx):
            skx=skxab
        else:
            skx=skxac

        if abs(saby)>abs(sacy):
            sky=skyab
        else:
            sky=skyac
        
        print(str(skx) + ',' + str(sky))
			
        # empty strings
        index=''
        positions=''
        
        # assemble long strings of bytes (as hex) then unhexlify and write to binary file                
        seperator='0000DD24664052B8884298AEC04285EBB140BE9F3A40486186422F1DC242C3F590400000'
        seperator=seperator+(struct.pack('x')*60).encode('hex')
        
        counter=0
        
        for d in dlist:
            if d['code']==1:
              continue
            xn=d['x']-pax
            yn=d['y']-pay
            
            xr=xn*math.cos(rot)-yn*math.sin(rot) # rotate first
            yr=xn*math.sin(rot)+yn*math.cos(rot)
            
            xsk=xr*skx # skew rotated coord
            ysk=yr*sky
            
            xstg=ax-xsk-xtweak
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