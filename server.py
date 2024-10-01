##############################################################################
# server.py
##############################################################################

import socket
import chatlib
import select


# GLOBALS
users = {}  # {user_name: {"password": , "score": , "questions_asked": []}}
questions = {}  # {qustion_key: ["question", "answer1", "answer2", "answer2", "answer4", "num_correct_answer"]}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later

ERROR_MSG = "Error! "
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message. 
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    # Build the message using chatlib
    full_msg = chatlib.build_message(code, msg)

    # Check if the message was successfully built
    if full_msg is chatlib.ERROR_RETURN:
        print("Failed to build message. Exiting function.")
        return

    # Debug print
    print("[SERVER] ", full_msg) 
    
    try:
        # Send the encoded message to the connection
        conn.send(full_msg.encode())
    except Exception as e:
        print(f"Error sending message: {e}")


def recv_message_and_parse(conn):
    """
    Receives a new message from the given socket,
    then parses the message using chatlib.
    Parameters: conn (socket object)
    Returns: cmd (str) and data (str) of the received message.
    If an error occurs, returns chatlib.ERROR_RETURN, chatlib.ERROR_RETURN.
    """
    try:
        # Receive data from the socket
        full_msg = conn.recv(10021).decode()
        
        # If the connection is closed or empty message received
        if not full_msg:
            print("Connection closed or empty message received")
            return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN

        # Parse the message using chatlib
        cmd, data = chatlib.parse_message(full_msg)

        # Debug print
        print("[CLIENT] ", full_msg)  

        # Check if parsing failed
        if cmd is chatlib.ERROR_RETURN and data is chatlib.ERROR_RETURN:
            print("Failed to parse message")
            return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN
        
        return cmd, data

    except Exception as e:
        print(f"Error receiving or parsing message: {e}")
        return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN	


# Data Loaders #

def load_questions():
    """
    Loads questions bank from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: questions dictionary
    """
    questions = {
        2313: {"question": "How much is 2+2", "answers": ["3", "4", "2", "1"], "correct": 2},
        4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"], "correct": 3} 
    }
    
    return questions


def load_user_database():
    """
    Loads users list from file	## FILE SUPPORT TO BE ADDED LATER
    Recieves: -
    Returns: user dictionary
    """
    users = {
        "test": {"password": "test", "score": 0, "questions_asked": []},
        "yossi": {"password": "123", "score": 50, "questions_asked": []},
        "master": {"password": "master", "score": 200, "questions_asked": []}
    }
    return users


# SOCKET CREATOR

def setup_socket():
    """
    Creates new listening socket and returns it
    Recieves: -
    Returns: the socket object
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    sock.listen()
    print("Listening for clients...")
    
    return sock


def send_error(conn, error_msg):
    """
    Send error message with given message
    Recieves: socket, message error string from called function
    Returns: chatlib.ERROR_RETURN
    """
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["error_msg"], f"{ERROR_MSG} {error_msg}")


##### MESSAGE HANDLING

def handle_getscore_message(conn, username):
    global users
    # Implement this in later chapters


def handle_logout_message(conn):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: chatlib.ERROR_RETURN
    """
    global logged_users
    
    conn.close()


def handle_login_message(conn, data):
    """
    Gets socket and message data of login message. Checks if user and password exist and match.
    If not - sends error and finishes. If all ok, sends OK message and adds user to logged_users.
    Receives: conn (socket object), data (str) of the received message.
    Returns: chatlib.ERROR_RETURN (sends response to client).
    """
    global users  # Dictionary of users, with username as key and password stored in it
    global logged_users  # Dictionary to track logged-in users

    # Parse the incoming message
    cmd, msg = chatlib.parse_message(data)

    # Check if parsing failed or the command is not LOGIN
    if cmd is chatlib.ERROR_RETURN or cmd != chatlib.PROTOCOL_CLIENT["login_msg"]:
        print("Failed to parse message or invalid command received")
        send_error(conn, "Failed to parse message or invalid command")
        return

    # Split the message into username and password
    user_name, password = chatlib.split_data(msg, 2)

    # Validate the split data
    if user_name is chatlib.ERROR_RETURN or password is chatlib.ERROR_RETURN:  # Check for split errors
        send_error(conn, "Invalid login data format")
        return

    # Check if the username exists in the system
    if user_name not in users.keys():
        send_error(conn, "Username does not exist")
    elif users[user_name]["password"] != password:  # Check if the password matches
        send_error(conn, "Password does not match")
    else:
        # Login successful, add the user to logged_users and send LOGIN_OK
        logged_users[user_name] = conn  # Store the user and their connection
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
        print(f"User {user_name} logged in successfully")	


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: chatlib.ERROR_RETURN
    """
    global logged_users	 # To be used later
    
    if cmd not in chatlib.PROTOCOL_CLIENT.values():
        send_error(conn, f"The command {cmd} is not recognized")
    elif cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
        handle_login_message(conn, data)   


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions

    # Load the users and questions before starting the server
    users = load_user_database()   # Load user data
    questions = load_questions()   # Load questions

    print("Welcome to Trivia Server!")
    server_socket = setup_socket()
    
    while True:
        try:
            # Accept new client connections
            client_socket, client_address = server_socket.accept()
            print(f"New client joined! {client_address}")
            
            while True:
                try:
                    # Receive and parse client message
                    cmd, data = recv_message_and_parse(client_socket)
                    
                    # If client disconnects or sends an empty message
                    if cmd == chatlib.ERROR_RETURN:
                        print(f"Connection with {client_address} closed")
                        break
                    
                    # If the client logs out
                    if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                        handle_logout_message(client_socket)
                        break
                    
                    # Route the message to the appropriate handler
                    handle_client_message(client_socket, cmd, data)                
                
                except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                    # Handle the case where the client disconnected unexpectedly
                    print(f"Client {client_address} disconnected abruptly: {e}")
                    break
            
            client_socket.close()
        
        except KeyboardInterrupt:
            # Handle server shutdown (Ctrl+C on the server)
            print("\nServer is shutting down")
            break

    server_socket.close()

if __name__ == '__main__':
    main()