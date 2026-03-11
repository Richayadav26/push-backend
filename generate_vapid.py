from cryptography.hazmat.primitives.asymmetric import ec
import base64

# Generate elliptic curve key
private_key = ec.generate_private_key(ec.SECP256R1())
public_key = private_key.public_key()

# Private key
private_bytes = private_key.private_numbers().private_value.to_bytes(32, "big")
private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode("utf-8")

# Public key
x = public_key.public_numbers().x.to_bytes(32, "big")
y = public_key.public_numbers().y.to_bytes(32, "big")
public_bytes = b"\x04" + x + y
public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode("utf-8")

print("Public Key:", public_key_b64)
print("Private Key:", private_key_b64)