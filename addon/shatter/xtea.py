"""
Very simple implementation of the XTEA block cipher
"""

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
	
	print(f"### final ciphertext = {hex(ciphertext[0])[2:]}{hex(ciphertext[1])[2:]} ###")
	
	return ciphertext

def process_block_bytes(key, plaintext, rounds = 64, magic = 0x9E3779B9, decrypt = False):
	"""
	The same as process_block, but the key and plaintext are bytearrays
	"""
	
	v = process_block([int.from_bytes(key[0:4], "little"), int.from_bytes(key[4:8], "little"), int.from_bytes(key[8:12], "little"), int.from_bytes(key[12:16], "little")], [int.from_bytes(plaintext[0:4], "little"), int.from_bytes(plaintext[4:8], "little")], rounds, magic, decrypt)
	
	return bytearray(v[0].to_bytes(4, "little") + v[1].to_bytes(4, "little"))

if __name__ == "__main__":
	# process_block([0x80, 0, 0, 0], [0, 0])
	# process_block([0x80, 0, 0, 0], [0x874a60ac, 0x1bc1df62], decrypt = True)
	r = process_block_bytes(b"\x80" + b"\0"*15, b"\0\0\0\0\0\0\0\0")
	process_block_bytes(b"\x80" + b"\0"*15, r, decrypt = True)
