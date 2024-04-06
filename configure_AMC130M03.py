# The imports
from machine import Pin
from machine import SPI
from bin_8 import bin_8, bin_16
import rp2
import time
from array import array

# Crystal is 12 MHz, so set to an integer clock mode for low jitter
machine.freq(192000000)

# The 8 MHz clock generator
@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def adc_8MHz():
    set(pins, 1)
    set(pins, 0)
    
# The PIO    
sm = rp2.StateMachine(0, adc_8MHz, freq = 16000000, set_base=Pin(20))
# Set to inactive
sm.active(0)

def read_AMC130M03(spi, cs):
    # This function will read the ADC values
    # spi - the spi object for the AMC130M03
    # cs - the chip select pin
    
    # Read register
    # At reset, default is 24 bit words, 16 bit value plus one byte of 0s, don't ask me why...
    txdata = bytearray([0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0])
    rxdata = bytearray(len(txdata))
    try:
        # Select the SPI device
        cs(0)
        # Simulateously write and read bytes
        spi.write_readinto(txdata, rxdata)
    finally:
        # Deselect the SPI device
        cs(1)
    
    # The RAW ADC data, return in a list
    temp = [(rxdata[3] << 8) + rxdata[4], (rxdata[6] << 8) + rxdata[7], (rxdata[9] << 8) + rxdata[10]]

    # Return the ADC values
    return temp
        
    
def read_reg_AMC130M03(spi, cs, reg_addr):
    # Read any register
    # spi - the spi object for the AMC130M03
    # cs - the chip select pin
    # reg_addr - expect an address from 0 to 63
    
    # Checks on the input address
    assert reg_addr >= 0
    assert reg_addr <= 63
    
    # Read register
    # At reset, default is 24 bit words, 16 bit value plus one byte of 0s, don't ask me why...
    txdata = bytearray([0b10100000 | (reg_addr >> 1), 0 | ((reg_addr & 1) << 7), 0, 0,0,0, 0,0,0, 0,0,0, 0,0,0])
    rxdata = bytearray(len(txdata))
    try:
        # Select the SPI device
        cs(0)
        # Simulateously write and read bytes
        spi.write_readinto(txdata, rxdata)
    finally:
        # Deselect the SPI device
        cs(1)
        
    # Send blank data next
    txdata2 = bytearray([0,0,0, 0,0,0, 0,0,0, 0,0,0, 0,0,0])
    rxdata2 = bytearray(len(txdata2))
    
    try:
        # Select SPI device
        cs(0)
        # Simultaneously write and read bytes
        spi.write_readinto(txdata2, rxdata2)
    finally:
        cs(1)
        
    return ((rxdata2[0] << 8) | rxdata2[1])

def write_reg_AMC130M03(spi, cs, reg_addr, reg_value):
    # Write any register
    # spi - the spi object for the AMC130M03
    # cs - the chip select pin
    # reg_addr - expect an address from 0 to 63
    # reg_value - the new value, expect 16 bit
    
    # Checks on the input address
    assert reg_addr >= 0
    assert reg_addr <= 63
    
    assert reg_value >= 0
    assert reg_value <= 65535
    
    # Write register
    # At reset, default is 24 bit words, 16 bit value plus one byte of 0s, don't ask me why...
    txdata = bytearray([0b01100000 | (reg_addr >> 1), 0 | ((reg_addr & 1) << 7), 0,  (reg_value >> 8),(reg_value & 255),0, 0,0,0, 0,0,0, 0,0,0]) #,0, 0,0,0, 0,0,0, 0,0,0])
    rxdata = bytearray(len(txdata))
    try:
        # Select the SPI device
        cs(0)
        # Simulateously write and read bytes
        spi.write_readinto(txdata, rxdata)
    finally:
        # Deselect the SPI device
        cs(1)

# Reset, active low
sync_reset = Pin(22, Pin.OUT, value = 1)

# Special ADC clock
#clk = Pin(20, Pin.OUT, value = 0)

# Chip select
cs = Pin(17, Pin.OUT, value = 0);

# SPI
spi = SPI(0, 400000, sck = Pin(18), mosi = Pin(19), miso = Pin(16), phase=1)

# Trigger a reset
time.sleep(0.001)
sync_reset.value(0)
time.sleep(0.001)
sync_reset.value(1)
time.sleep(0.001)

# Data ready pin
drdy = Pin(21, Pin.IN)
print("DRDY should be 1: " + str(drdy.value()))

# Read the ID - don't be surprised if it is different than what is reported in the datasheet
id_reg = read_reg_AMC130M03(spi, cs, 0x0)

status_reg = read_reg_AMC130M03(spi, cs, 0x1)

mode_reg = read_reg_AMC130M03(spi, cs, 0x2)

clock_reg = read_reg_AMC130M03(spi, cs, 0x3)
# print(bin_16(clock_reg))

gain_reg = read_reg_AMC130M03(spi, cs, 0x4)

cfg_reg = read_reg_AMC130M03(spi, cs, 0x6)

# Turn on the bit
write_reg_AMC130M03(spi, cs, 0x31, 1)
DCDC_ctrl_reg = read_reg_AMC130M03(spi, cs, 0x31)
print("DCDC_CTRL_REG " + bin_16(DCDC_ctrl_reg))

time.sleep(0.001)

# Enable the 8 MHz clock
sm.active(1)

# Wait a bit
time.sleep(0.005)

# Read and print the register
print(bin_16(read_reg_AMC130M03(spi, cs, 0x1)))
# The second read, bit 6 should have dropped to 0, DCDC up and running
print(bin_16(read_reg_AMC130M03(spi, cs, 0x1)))

# Grab some samples
NUM_SAMPLES = 64
wave0 = array("I", [0] * (NUM_SAMPLES))
wave1 = array("I", [0] * (NUM_SAMPLES))

for ii in range(NUM_SAMPLES):
    temp = read_AMC130M03(spi, cs)
    wave0[ii] = temp[0]
    wave1[ii] = temp[1]
    time.sleep(0.001)

# Print them out after scaling
for ii in range(NUM_SAMPLES):
    temp0 = wave0[ii]
    if temp0 > 32767:
        temp0 = temp0 - 65536
    
    temp0 = temp0 / 32768.0 * 1.2
    
    temp1 = wave1[ii]
    if temp1 > 32767:
        temp1 = temp1 - 65536
    
    temp1 = temp1 / 32768.0 * 1.2
    
    print(str(temp0) + ", " + str(temp1))
