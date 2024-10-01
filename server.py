##############################################################################
# server.py
##############################################################################

import socket
import select
import random
import chatlib



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
        4122: {"question": "What is the capital of France?", "answers": ["Lion", "Marseille", "Paris", "Montpellier"], "correct": 3},
        4232: {"question": "What is the capital of Israel?", "answers": ["Jerusalem", "Tel-Aviv", "Beer-Sheva", "Haifa"], "correct": 1},
        3465: {"question": "What is the capital of England?", "answers": ["Liverpool", "Bristol", "Manchester", "London"], "correct": 4}
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
    if username not in users.keys():
        send_error(conn, f"User {username} is not found!")
    else:
        user_score = users.get(username, {}).get("score", 0)  # Use get() to safely retrieve the score
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_score_msg"], str(user_score))

def handle_highscore_message(conn):
    global users
    users_score = {user: info.get("score", 0) for user, info in users.items()}  # Use get() to handle missing scores
    sorted_dict = {key: value for key, value in sorted(users_score.items(), key=lambda item: item[1], reverse=True)}
    full_msg = []
    full_msg = "\n".join([f"{user}: {score}" for user, score in sorted_dict.items()])
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["all_score_msg"], full_msg)

def handle_logged_message(conn):
    global logged_users
    logged_users_list = ",".join(logged_users.values())
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["logged_answer_msg"], logged_users_list)


def handle_logout_message(conn):
    """
    Closes the given socket (in later chapters, also remove user from logged_users dictioary)
    Recieves: socket
    Returns: chatlib.ERROR_RETURN
    """
    global logged_users
    logged_users.pop(conn.getpeername(), None)  # Safely remove client    
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
    if not users.get(user_name):  # Use get() to check if the user exists
        send_error(conn, "Username does not exist")
    elif users.get(user_name, {}).get("password") != password:  # Use get() to safely retrieve the password
        send_error(conn, "Password does not match")
    else:
        # Login successful, add the user to logged_users and send LOGIN_OK
        # Get the client's address using getpeername()
        client_address = conn.getpeername()

        # Add the client's address and username to the logged_users dictionary
        logged_users[client_address] = user_name

        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["login_ok_msg"], "")
        print(f"User {user_name} logged in successfully")


def create_random_question():
    global questions

    # Get a list of question IDs from the questions dictionary
    question_ids = list(questions.keys())
    
    # Choose a random question ID from the list
    random_question_id = random.choice(question_ids)

    # Get question text and answers
    question_text = questions[random_question_id]["question"]
    question_answers = questions[random_question_id]["answers"]
    
    # Create the full question data
    question_data = chatlib.join_data([str(random_question_id), question_text] + question_answers)
    
    return question_data    


def handle_question_message(conn):
    question_data = create_random_question()
    build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_question_msg"], question_data)    


def handle_answer_message(conn, username, answer_data):
    global questions
    
    # Extract the question ID and user's answer using split_data
    split_result = chatlib.split_data(answer_data, 2)

    # Check if split_data returned an error
    if split_result == [chatlib.ERROR_RETURN]:
        send_error(conn, "Invalid answer format")
        return
    
    # Unpack the split_result safely after validation
    question_id, user_answer = split_result

    # Convert question_id to int for comparison
    try:
        question_id = int(question_id)
    except ValueError:
        send_error(conn, "Invalid question ID format")
        return

    # Check if the question exists
    if question_id not in questions:
        send_error(conn, "Question ID not found.")
        return

    # Check if the user's answer matches the correct one
    if int(user_answer) == questions[question_id]["correct"]:
        users[username]["score"] += 5  # Update score if correct
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["correct_answer_msg"], "")
    else:
        # Send back the correct answer if the user is wrong
        correct_answer = str(questions[question_id]["correct"])
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["wrong_answer_msg"], correct_answer)


def handle_client_message(conn, cmd, data):
    """
    Gets message code and data and calls the right function to handle command
    Recieves: socket, message code and data
    Returns: None
    """
    global logged_users
    
    # Validate command
    if cmd not in chatlib.PROTOCOL_CLIENT.values():
        send_error(conn, f"The command {cmd} is not recognized")
        return 
    
    # Check if the user is logged in
    user = logged_users.get(conn.getpeername())
    if user is None:
        if cmd == chatlib.PROTOCOL_CLIENT["login_msg"]:
            handle_login_message(conn, data)
        else:
            send_error(conn, "Please log in first")
    else:
        # Handle commands once logged in
        if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
            handle_logout_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["my_score_msg"]:
            handle_getscore_message(conn, user)
        elif cmd == chatlib.PROTOCOL_CLIENT["highscore_msg"]:
            handle_highscore_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["logged_msg"]:
            handle_logged_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["get_question_msg"]:
            handle_question_message(conn)
        elif cmd == chatlib.PROTOCOL_CLIENT["send_answer_msg"]:
            handle_answer_message(conn, user, data)
        else:
            send_error(conn, "Unknown command after login")


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