"""
Very simple implementation of the XTEA block cipher
"""

import secrets

def process_block(key, plaintext, rounds = 64, magic = 0x9E3779B9, decrypt = False):
	"""
	(De|En)crypt a block of plaintext. Key must be four 32-bit words and
	plaintext must be two 32-bit words.
	"""
	
	ciphertext = plaintext.copy()
	
	if (decrypt):
		ciphertext[0], ciphertext[1] = ciphertext[1], ciphertext[0]
	
	# print(f"state is {ciphertext}")
	
	for i in (range(rounds) if not decrypt else reversed(range(rounds))):
		# print(f"\n### i={i} ###")
		sum = (((i + 1) // 2) * magic) % 0x100000000
		# print(f"sum = {hex(sum)}")
		subkey = (sum + key[((sum >> 11) if (i & 1) else (sum)) & 0b11]) % 0x100000000
		# print(f"subkey = {hex(subkey)}")
		mixed = ((((ciphertext[1] << 4) % 0x100000000) ^ (ciphertext[1] >> 5)) + ciphertext[1]) % 0x100000000
		# print(f"mixed = {hex(mixed)}")
		
		ciphertext[0] += (subkey ^ mixed) * (1 if not decrypt else -1)
		ciphertext[0], ciphertext[1] = ciphertext[1], (ciphertext[0] % 0x100000000)
		
		# print(f"state is {hex(ciphertext[0])[2:]} {hex(ciphertext[1])[2:]}")
	
	# print(f"### final ciphertext = {hex(ciphertext[0])[2:]}{hex(ciphertext[1])[2:]} ###")
	
	return ciphertext

def process_block_bytes(key, plaintext, rounds = 64, magic = 0x9E3779B9, decrypt = False):
	"""
	The same as process_block, but the key and plaintext are bytearrays
	"""
	
	v = process_block(
		[int.from_bytes(key[0:4], "little"), int.from_bytes(key[4:8], "little"), int.from_bytes(key[8:12], "little"), int.from_bytes(key[12:16], "little")],
		[int.from_bytes(plaintext[0:4], "little"), int.from_bytes(plaintext[4:8], "little")],
		rounds,
		magic,
		decrypt
	)
	
	return bytearray(v[0].to_bytes(4, "little") + v[1].to_bytes(4, "little"))

def _int_to_uint64(v):
	"""
	Convert a int to a uint64 bytearray
	"""
	
	return bytearray(v.to_bytes(8, "little"))

def _xor_bytes(a, b):
	"""
	XOR two byte arrays. If one is less in length than the other, only the number
	of bytes in the lower length one is xored.
	"""
	
	c = bytearray(b"\0" * min(len(a), len(b)))
	
	for i in range(len(c)):
		c[i] = a[i] ^ b[i]
	
	return c

def process_bytes_ctr(key, plaintext, nonce = None):
	"""
	Process an N-length bytearray in CTR mode using XOR to combine a 64-bit
	nonce and counter. Note that this is secure only if a random nonce is used.
	"""
	
	nonce = bytearray(secrets.token_bytes(8)) if nonce == None else nonce
	counter = 0
	ciphertext = bytearray()
	
	for i in range((len(plaintext) // 8) + min(len(plaintext) % 8, 1)):
		pair = _xor_bytes(_int_to_uint64(counter), nonce)
		piece = _xor_bytes(process_block_bytes(key, pair), plaintext[8 * i:8 * (i + 1)])
		ciphertext += piece
		
		counter += 1
	
	# print(f"{nonce} {ciphertext} ({len(ciphertext)} / {len(ciphertext) % 8})")
	
	return (nonce, ciphertext)

if __name__ == "__main__":
	print("Testing block ....")
	
	print("Encrypt block of zeros with key 0x8000...00")
	r = process_block_bytes(b"\x80" + b"\0"*15, b"\0\0\0\0\0\0\0\0")
	print(r)
	assert(r == bytearray(b'\xac`J\x87b\xdf\xc1\x1b'))
	r = process_block_bytes(b"\x80" + b"\0"*15, r, decrypt = True)
	print(r)
	assert(r == bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00'))
	
	print("\nTesting XTEA-CTR ...")
	
	n, ct = process_bytes_ctr(b"\0\0\0\0\0\0\0\0", b"Hello, world! This is my text~ :3")
	n, pt = process_bytes_ctr(b"\0\0\0\0\0\0\0\0", ct, nonce = n)
	
	print(n, ct, "decrpted", pt)
