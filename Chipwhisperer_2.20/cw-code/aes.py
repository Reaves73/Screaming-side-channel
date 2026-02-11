#import chipwhisperer.analyzer.attacks.models.aes.funcs as aes_funcs
#import chipwhisperer.analyzer.attacks.models.aes.key_schedule as aes_ks
import aes_funcs
import aes_key_schedule as aes_ks
import numpy as np


def add_round_key(state, round_key):
    return [s ^ k for s, k in zip(state, round_key)]


def expand_key(key):
    return [aes_ks.key_schedule_rounds(key, 0, r) for r in range(11)]


def schedule_key(key, r):
    key = list(key)
    round_key = aes_ks.key_schedule_rounds(key, 0, r)
    return np.array(round_key, dtype=np.uint8)

schedule_key = np.vectorize(schedule_key, signature="(n),()->(n)")


def aes_round(state, round_key, final=False):
    state = aes_funcs.subbytes(state)
    state = aes_funcs.shiftrows(state)
    if not final:
        state = aes_funcs.mixcolumns(state)
    state = add_round_key(state, round_key)
    return state


def aes128_encrypt(plaintext, key):
    assert(len(plaintext.shape) == 1)
    assert(len(key.shape) == 1)
    assert(plaintext.shape[-1] == 16)
    assert(key.shape[-1] == 16)
    
    plaintext = list(plaintext)
    key = list(key)

    round_keys = expand_key(key)

    # Initial AddRoundKey
    state = add_round_key(plaintext, round_keys[0])

    # Rounds 1..9
    for r in range(1, 10):
        state = aes_round(state, round_keys[r])

    # Final round (no MixColumns)
    state = aes_round(state, round_keys[10], final=True)

    return np.array(state, dtype=np.uint8)


aes128_encrypt = np.vectorize(aes128_encrypt, signature="(n),(n)->(n)")


def get_last_state_from_ciphertext(ciphertext, key):
    assert(len(ciphertext.shape) == 1)
    assert(len(key.shape) == 1)
    assert(ciphertext.shape[-1] == 16)
    assert(key.shape[-1] == 16)
    
    ciphertext = list(ciphertext)
    key = list(key)
    
    last_round_key = aes_ks.key_schedule_rounds(key, 0, 10)
    last_state = add_round_key(ciphertext, last_round_key)
    return np.array(last_state, dtype=np.uint8)


def get_first_sbox_output(plaintext, key):
    assert(len(plaintext.shape) == 1)
    assert(len(key.shape) == 1)
    assert(plaintext.shape[-1] == 16)
    assert(key.shape[-1] == 16)
    
    plaintext = list(plaintext)
    key = list(key)
    
    first_round_key = aes_ks.key_schedule_rounds(key, 0, 0)
    state = add_round_key(plaintext, first_round_key)
    #state = aes_funcs.subbytes(state)
    
    return np.array(state, dtype=np.uint8)

get_first_sbox_output = np.vectorize(get_first_sbox_output, signature="(n),(n)->(n)")

get_last_state_from_ciphertext = np.vectorize(get_last_state_from_ciphertext, signature="(n),(n)->(n)")


if __name__ == "__main__":
    test_input = np.array([
        0x14, 0x0f, 0x0f, 0x10,
        0x11, 0xb5, 0x22, 0x3d,
        0x79, 0x58, 0x77, 0x17,
        0xff, 0xd9, 0xec, 0x3a
    ], dtype=np.uint8)

    correct_output = np.zeros(16, dtype=np.uint8)

    correct_last_state = np.array([
        0xb4, 0xef, 0x5b, 0xcb,
        0x3e, 0x92, 0xe2, 0x11,
        0x23, 0xe9, 0x51, 0xcf,
        0x6f, 0x8f, 0x18, 0x8e
    ], dtype=np.uint8)
    
    test_key = np.zeros(16, dtype=np.uint8)
    
    test_output = aes128_encrypt(test_input, test_key)
    last_state = get_last_state_from_ciphertext(test_output, test_key)

    if np.any(test_output != correct_output):
        print("Test output is incorrect!")

    if np.any(last_state != correct_last_state):
        print("Last state is incorrect!")

    print("Test successful.")
        
        
    


    
