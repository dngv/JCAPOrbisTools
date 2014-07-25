from readplatemap import readsingleplatemaptxt
import struct, binascii


# generates stage file with same name as platemap, .stg extension
def orbPM(pm, zstg, xoff=0, yoff=0):
    if not 0<=zstg<=100:
        print 'Invalid z-height'
    else:
        # assume pm in current working directory
        dlist=readsingleplatemaptxt(pm)
        
        # empty strings
        index=''
        positions=''
        
        # assemble long strings of bytes (as hex) then unhexlify and write to binary file                
        seperator='0000DD24664052B8884298AEC04285EBB140BE9F3A40486186422F1DC242C3F590400000'
        seperator=seperator+(struct.pack('x')*60).encode('hex')
        
        counter=0
        
        for d in dlist:
            xstg=100-d['x']-xoff
            ystg=d['y']+yoff
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