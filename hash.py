from passlib.hash import pbkdf2_sha256

password = "password123"

hashed = pbkdf2_sha256.hash(password)

print(hashed)
