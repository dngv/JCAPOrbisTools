#import os
from readplatemap import readsingleplatemaptxt
import struct, binascii
# Read wafer platemap into dlist

# os.chdir('/home/dan/code/orbisTools/')

# pm='/media/work/data/platemaps/0027_flat2_y.txt'

def orbPM(pm, zstg, xoff=0, yoff=0):
    # assume pm in current working directory
    dlist=readsingleplatemaptxt(pm)
    
    # assemble long string of bytes (as hex) then unhexlify and write to file
    # form header string
    header=struct.pack('<b',15)
    header+=struct.pack('x')*15
    header+=struct.pack('x')*2
    header+=struct.pack('<h', dlist[-1]['Sample'])
    header+=struct.pack('x')*20
    header=header.encode('hex')
    
    # empty strings
    index=''
    positions=''
    seperator='0000DD24664052B8884298AEC04285EBB140BE9F3A40486186422F1DC242C3F59040'
    seperator+=seperator+(struct.pack('x')*4).encode('hex')
    
    
    for d in dlist:
        i=struct.pack('<h', d['Sample'])# entry index (16-bit short?, 2 bytes)
        i+=struct.pack('<h', 0) # entry type (00 for point, 01 for line, 02 for matrix)
        i+=struct.pack('<h', 1)*2   # (1) num points to scan (01 for point, for line length, matrix width)
                                    # (2) num points to scan (01 for point & line, matrix height)      
        i=binascii.hexlify('Center                  ')+i.encode('hex')
        x=struct.pack('<f', 100-d['x']-xoff)
        y=struct.pack('<f', d['y']+yoff)
        z=struct.pack('<f', zstg)
        p=x+y+x+y+z+z # x start, y start, x end, y end, z start, z end
        p+=struct.pack('x')*4 # 4 byte padding (probably for rotation info but our stage doesn't have that)
        p=p.encode('hex')
        index+=i
        positions+=p
    
    # concatenate hex string and convert to byte code    
    bytecode=binascii.unhexlify(header+index+seperator+positions)
    
    #os.chdir('/home/dan/code/orbisTools')
    stgout=pm[:-3]+'stg'
    f=open(stgout, mode='w')
    f.write(bytecode)
    f.close()