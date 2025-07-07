import struct
import numpy as np

def ROTATE(v, c):
    """
    Rotate a 32-bit integer v to the left by c bits.
    """
    return ((v << c) & 0xffffffff) | (v >> (32 - c))

def XOR(v, w):
    """
    Perform a bitwise XOR operation on two 32-bit integers.
    """
    return v ^ w

def PLUS(v, w):
    """
    Add two 32-bit integers mod 2^32.
    """
    return (v + w) & 0xffffffff

def PLUSONE(v):
    """
    Add one to a 32-bit integer mod 2^32.
    """
    return PLUS(v, 1)

def QUARTERROUND(x, a, b, c, d):
    """
    Perform a quarter round operation on the Salsa20/ChaCha20 state.
    """
    x[a] = PLUS(x[a], x[b])
    x[d] = ROTATE(XOR(x[d], x[a]), 16)
    x[c] = PLUS(x[c], x[d])
    x[b] = ROTATE(XOR(x[b], x[c]), 12)
    x[a] = PLUS(x[a], x[b])
    x[d] = ROTATE(XOR(x[d], x[a]), 8)
    x[c] = PLUS(x[c], x[d])
    x[b] = ROTATE(XOR(x[b], x[c]), 7)

def salsa20_wordtobyte(input, rounds=20):
    """
    Perform the Salsa20/ChaCha20 quarter rounds.

    Parameters:
        input (list): The input state (16 words).
        rounds (int): Number of rounds to perform (default is 20).

    Returns:
        list: The output state as an array of 32-bit integers.
    """
    x = input[:]
    if rounds == 1:
        # Perform only the first round
        QUARTERROUND(x, 0, 4, 8, 12)
        QUARTERROUND(x, 1, 5, 9, 13)
        QUARTERROUND(x, 2, 6, 10, 14)
        QUARTERROUND(x, 3, 7, 11, 15)
    else:
        # Perform the full set of rounds
        for i in range(rounds, 0, -2):
            # First round
            QUARTERROUND(x, 0, 4, 8, 12)
            QUARTERROUND(x, 1, 5, 9, 13)
            QUARTERROUND(x, 2, 6, 10, 14)
            QUARTERROUND(x, 3, 7, 11, 15)
            # Second round
            QUARTERROUND(x, 0, 5, 10, 15)
            QUARTERROUND(x, 1, 6, 11, 12)
            QUARTERROUND(x, 2, 7, 8, 13)
            QUARTERROUND(x, 3, 4, 9, 14)

    # Return the state as an array of 32-bit integers
    return [(x[i]) & 0xffffffff for i in range(16)]

def Chacha20(key, nonce, pt):
    """
    Encrypts a plaintext using the ChaCha20 stream cipher.
    Parameters:
        key (str): The encryption key as a hex string.
        nonce (str): The nonce as a hex string.
        pt (str): The plaintext to encrypt as a hex string.
    Returns:
        str: The encrypted ciphertext as a hex string.
    """
    def to_u32_list(data):
        return list(struct.unpack('<16I', data))

    def from_u32_list(data):
        return struct.pack('<16I', *data)

    def hex_to_bytes(hex_str):
        return bytes.fromhex(hex_str)

    key = hex_to_bytes(key)
    nonce = hex_to_bytes(nonce)
    pt = hex_to_bytes(pt)
    
    if len(key) != 32:
        raise ValueError("Key must be 32 bytes")
    if len(nonce) != 12:
        raise ValueError("Nonce must be 12 bytes")

    key = list(struct.unpack('<8I', key))
    nonce = list(struct.unpack('<3I', nonce))

    state = [
        0x61707865, 0x3320646e, 0x79622d32, 0x6b206574,
        key[0], key[1], key[2], key[3],
        key[4], key[5], key[6], key[7],
        0x00000000, nonce[0], nonce[1], nonce[2]
    ]

    output = salsa20_wordtobyte(state)
    keystream = from_u32_list(output)
    print(f"keystream: {keystream.hex()}")
    encrypted = bytes([p ^ k for p, k in zip(pt, keystream)])
    print(f"encrypted: {encrypted.hex()}")
    return encrypted.hex()


def Chacha20Keystream(key, nonce, rounds=20, swapped_bytes=False):
    """
    Generates a keystream using the Salsa20/ChaCha20 algorithm.
    Parameters:
        key (str or list): The encryption key as a hex string or a list of 8 32-bit integers.
        nonce (str or list): The nonce as a hex string or a list of 3 32-bit integers.
        rounds (int): Number of rounds to perform (default is 20).
        swapped_bytes (bool): If True, swap the bytes in each 32-bit word.
    Returns:
        list: The keystream as an array of 32-bit integers.
    """
    def hex_to_bytes(hex_str):
        return bytes.fromhex(hex_str)

    # Check if key and nonce are hex strings or integer arrays
    if isinstance(key, np.ndarray) and key.shape == (8,):
        pass
    elif isinstance(key, str):
        key = hex_to_bytes(key)
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes")
        key = list(struct.unpack('<8I', key))  # Convert to 8 32-bit integers
    elif isinstance(key, list) and len(key) == 8:
        # Key is already a list of 8 32-bit integers
        pass
    else:
        raise ValueError("Key must be a 32-byte hex string or a list of 8 32-bit integers")

    if isinstance(nonce, np.ndarray) and nonce.shape == (3,):
        pass
    elif isinstance(nonce, str):
        nonce = hex_to_bytes(nonce)
        if len(nonce) != 12:
            raise ValueError("Nonce must be 12 bytes")
        nonce = list(struct.unpack('<3I', nonce))  # Convert to 3 32-bit integers
    elif isinstance(nonce, list) and len(nonce) == 3:
        # Nonce is already a list of 3 32-bit integers
        pass
    else:
        raise ValueError("Nonce must be a 12-byte hex string or a list of 3 32-bit integers")


    state = [
        0x61707865, 0x3320646e, 0x79622d32, 0x6b206574,
        key[0], key[1], key[2], key[3],
        key[4], key[5], key[6], key[7],
        0x00000000, nonce[0], nonce[1], nonce[2]
    ]

    # Get the keystream as 32-bit integers
    keystream_32bit = salsa20_wordtobyte(state, rounds)

    if swapped_bytes:
        # Swap the bytes in each 32-bit word
        swapped_keystream = [(word & 0xFF) << 24 | (word & 0xFF00) << 8 | (word & 0xFF0000) >> 8 | (word >> 24) for word in keystream_32bit]
        return swapped_keystream
    else:
        # Keep the bytes in the original order
        return keystream_32bit