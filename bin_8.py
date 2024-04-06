def bin_8(in_val):
    # Format the 8 bit binary
    out_str = "0b" + str((in_val >> 7) & 0x1) \
                   + str((in_val >> 6) & 0x1) \
                   + str((in_val >> 5) & 0x1) \
                   + str((in_val >> 4) & 0x1) \
                   + str((in_val >> 3) & 0x1) \
                   + str((in_val >> 2) & 0x1) \
                   + str((in_val >> 1) & 0x1) \
                   + str((in_val >> 0) & 0x1)
    return out_str
    

def bin_16(in_val):
    # Format the 16 bit binary value, with a little space for ease of reading
    out_str = "0b"
    
    for ii in range(15, 7, -1):
        out_str = out_str + str((in_val >> ii) & 0x1)
                   
    out_str = out_str + " "
    
    for ii in range(7, -1, -1):
        out_str = out_str + str((in_val >> ii) & 0x1)
    
                   
    return out_str

