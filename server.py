import socket
import threading
import sqlite3
import hashlib
import random
import string
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

# generate rsa key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# convert public key to pem format to share with clients
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# connect to sqlite database (or create if not exists)
conn = sqlite3.connect("voting_system.db", check_same_thread=False)
cursor = conn.cursor()

# generate random token for each user
def generate_token(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# hash user id using sha256
def hash_id(id_number):
    return hashlib.sha256(id_number.encode()).hexdigest()

# store vote in database and mark user as voted
def store_vote(id_hash, vote, ip, token):
    time_cast = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO votes VALUES (?, ?, ?, ?, ?)", (id_hash, vote, ip, time_cast, token))
    cursor.execute("UPDATE users SET voted = 1 WHERE id_hash = ?", (id_hash,))
    conn.commit()

# decrypt vote using private key
def decrypt_vote(encrypted_vote_bytes):
    decrypted = private_key.decrypt(
        encrypted_vote_bytes,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(),
                     label=None)
    )
    return decrypted.decode()

# count votes and save result as graph
def tally_votes():
    cursor.execute("SELECT vote FROM votes")
    all_votes = cursor.fetchall()
    vote_count = {}
    for vote in all_votes:
        vote = vote[0]
        vote_count[vote] = vote_count.get(vote, 0) + 1

    import matplotlib
    matplotlib.use('Agg')  # use non-gui backend for headless environments
    plt.bar(vote_count.keys(), vote_count.values(), color='skyblue')
    plt.xlabel("Candidates")
    plt.ylabel("Number of Votes")
    plt.title("Voting Results")
    plt.savefig('vote_tally.png')
    plt.close()
    print("Tally plot saved as 'vote_tally.png'.")

# handle each connected client
def handle_client(client_socket, client_address):
    try:
        client_socket.send("Welcome to Voting Server!\nType 'register' or 'vote' or 'tally': ".encode())
        option = client_socket.recv(1024).decode().strip().lower()

        if option == "register":
            client_socket.send("Enter your 10-digit ID: ".encode())
            id_input = client_socket.recv(1024).decode().strip()

            if len(id_input) != 10 or not id_input.isdigit():
                client_socket.send("Invalid ID. Must be 10 digits.\n".encode())
                return

            id_hash = hash_id(id_input)
            last4 = id_input[-4:]

            cursor.execute("SELECT * FROM users WHERE id_hash = ?", (id_hash,))
            if cursor.fetchone():
                client_socket.send("ID already registered.\n".encode())
                return

            token = generate_token()
            expiry = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (id_hash, last4, token, expiry, 0))
            conn.commit()

            client_socket.send(f"Registration successful. Your token is: {token}\n".encode())

        elif option == "vote":
            client_socket.send("Enter your 10-digit ID: ".encode())
            id_input = client_socket.recv(1024).decode().strip()
            id_hash = hash_id(id_input)

            cursor.execute("SELECT token, token_expiry, voted FROM users WHERE id_hash = ?", (id_hash,))
            row = cursor.fetchone()

            if not row:
                client_socket.send("You are not registered.\n".encode())
                return

            token_db, expiry_str, voted = row
            expiry_time = datetime.strptime(expiry_str, "%Y-%m-%d %H:%M:%S")

            if datetime.now() > expiry_time:
                client_socket.send("Token expired. Please register again.\n".encode())
                return

            if voted:
                client_socket.send("You have already voted!\n".encode())
                return

            client_socket.send("Enter your assigned token: ".encode())
            token_input = client_socket.recv(1024).decode().strip()

            if token_input != token_db:
                client_socket.send("Invalid token!\n".encode())
                return

            client_socket.send("Send your vote (encrypted using the public key). Size limit: 256 bytes\n".encode())
            encrypted_vote = client_socket.recv(256)
            try:
                vote = decrypt_vote(encrypted_vote)
                ip = client_address[0]
                store_vote(id_hash, vote, ip, token_input)
                client_socket.send(f"Vote for '{vote}' recorded successfully!\n".encode())
            except Exception as e:
                client_socket.send(f"Error decrypting vote: {e}\n".encode())

        elif option == "tally":
            tally_votes()
            client_socket.send("Tally complete. Graph shown.\n".encode())

        else:
            client_socket.send("Invalid option.\n".encode())

    except Exception as e:
        print(f"Error with client {client_address}: {e}")
    finally:
        client_socket.close()

# create tcp server socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 5555))  # listen on all interfaces
server.listen(5)  # allow 5 pending connections
print("Voting Server started on port 5555")

# show public key to client
print("\nPublic Key (share this with clients):\n")
print(public_pem)

# accept connections and start thread for each client
while True:
    client_sock, addr = server.accept()
    thread = threading.Thread(target=handle_client, args=(client_sock, addr))
    thread.start()
