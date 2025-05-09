import socket
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend

# ------------------ rsa encryption function -------------------

# encrypts the vote using the public key received from server
def encrypt_vote(vote_str, public_key_pem):
    # load the public key from pem format
    public_key = serialization.load_pem_public_key(public_key_pem.encode(), backend=default_backend())
    # encrypt the vote string using oaep padding
    encrypted = public_key.encrypt(
        vote_str.encode(),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                     algorithm=hashes.SHA256(),
                     label=None)
    )
    return encrypted

# ------------------ client side socket setup -------------------

def main():
    host = "172.25.191.65"  # ip address of the server (should be on same network)
    port = 5555  # port number server is listening on

    # create a tcp socket and connect to the server
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))

    # receive welcome message and available options
    print(client.recv(1024).decode())  
    option = input().strip()  # user enters register, vote, or tally
    client.send(option.encode())  # send the option to the server

    if option == "register":
        # receive prompt for id
        print(client.recv(1024).decode())
        id_number = input().strip()
        client.send(id_number.encode())  # send id to server
        # receive and print the registration confirmation or error
        print(client.recv(1024).decode())

    elif option == "vote":
        # ask for id
        print(client.recv(1024).decode())
        id_number = input().strip()
        client.send(id_number.encode())

        # get server's response (could be error or token prompt)
        response = client.recv(1024).decode()
        if "not registered" in response or "already voted" in response or "expired" in response:
            print(response)
            client.close()
            return  # stop if user can't vote

        print(response)  # prompt to enter token
        token = input().strip()
        client.send(token.encode())

        # check if token is valid
        response = client.recv(1024).decode()
        if "Invalid token" in response:
            print(response)
            client.close()
            return  # stop if token is wrong

        print(response)  # prompt to enter vote
        vote = input("Enter your vote: ").strip()

        # get the public key from the server console (manually paste)
        print("\nPaste the public key (from server):")
        public_key_pem = ""
        while True:
            line = input()
            public_key_pem += line + "\n"
            if "-----END PUBLIC KEY-----" in line:
                break  # done collecting the pem key

        # encrypt the vote using the provided public key
        encrypted_vote = encrypt_vote(vote, public_key_pem)
        client.send(encrypted_vote)  # send encrypted vote to server
        # receive confirmation message from server
        print(client.recv(1024).decode())

    elif option == "tally":
        # show tally result if user requested tally
        print(client.recv(1024).decode())

    else:
        # if input is invalid
        print(client.recv(1024).decode())

    client.close()  # close the socket connection

# run the client
if __name__ == "__main__":
    main()
