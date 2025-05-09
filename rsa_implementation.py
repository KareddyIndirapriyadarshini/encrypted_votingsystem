import random
import math

#returns the greatest common divisor of a and b
def find_gcd(a, b):
    while b:
        a, b = b, a % b
    return a

#extended euclidean algorithm to find modular inverse of e modulo phi
def find_mod_inverse(e, phi):
    old_r, r = phi, e
    old_s, s = 1, 0
    old_t, t = 0, 1

    #iterate until remainder is 0
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t

    # old_t is the inverse of e modulo phi, if gcd is 1
    if old_r == 1:
        return old_t % phi
    return None  # no inverse if gcd != 1

# naive primality check
def is_prime(n):
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False
    limit = int(math.isqrt(n))
    for i in range(3, limit + 1, 2):
        if n % i == 0:
            return False
    return True

# generate a random prime within given bounds
def generate_random_prime(lower=100, upper=300):
    while True:
        candidate = random.randrange(lower, upper)
        if is_prime(candidate):
            return candidate

# main function to generate rsa keypair
def generate_rsa_keys():
    # pick two distinct primes
    p = generate_random_prime()
    q = generate_random_prime()
    while q == p:
        q = generate_random_prime()

    # compute modulus n and totient phi(n)
    n = p * q
    phi = (p - 1) * (q - 1)

    # choose public exponent e such that 1 < e < phi and gcd(e, phi) == 1
    e = random.randrange(2, phi)
    while find_gcd(e, phi) != 1:
        e = random.randrange(2, phi)

    # compute private exponent d
    d = find_mod_inverse(e, phi)
    if d is None:
        # unlikely but just in case, retry key generation
        return generate_rsa_keys()

    # return keypair as tuples
    public_key = (e, n)
    private_key = (d, n)
    return public_key, private_key

if __name__ == "__main__":
    # generate and display rsa public/private keys
    pub_key, priv_key = generate_rsa_keys()
    print(f"public key (e, n): {pub_key}")
    print(f"private key (d, n): {priv_key}")
