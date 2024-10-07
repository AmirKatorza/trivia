import socket
import chatlib  # To use chatlib functions or consts, use chatlib.****
import sys


SERVER_IP = "127.0.0.1"  # Our server will run on same computer as client
SERVER_PORT = 5678

# HELPER SOCKET METHODS


def connect():
     client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     client_socket.connect((SERVER_IP, SERVER_PORT))
     return client_socket


def error_and_exit(error_msg):
    """
    Prints an error message and exits the program.
    
    :param error_msg: The error message to display before exiting.
    """
    print(f"Error: {error_msg}")
    sys.exit(1)


def login(conn):
    while True:
        username = input("Please enter username: ")
        password = input("Please enter password: ")
        
        # Create and send login message
        login_data = chatlib.join_data([username, password])
        build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["login_msg"], login_data)
        
        # Receive server response
        cmd, data = recv_message_and_parse(conn)
        
        if cmd == chatlib.PROTOCOL_SERVER["login_ok_msg"]:
            print("Login successful!")
            return
        elif cmd == chatlib.PROTOCOL_SERVER["error_msg"]:
            print("Login failed. Please try again.")
        else:
            print(f"Received unexpected response from server: {cmd}")	


def build_and_send_message(conn, code, data):
    """
    Builds a new message using chatlib, wanted code and message. 
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    # Build the message using chatlib
    full_msg = chatlib.build_message(code, data)

    # Check if the message was successfully built
    if full_msg is chatlib.ERROR_RETURN:
        print("Failed to build message. Exiting function.")
        return

    # Debug print
    # print("[CLIENT] ", full_msg)
    
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

        # Debug print
        # print("[SERVER] ", full_msg)

        # Parse the message using chatlib
        cmd, data = chatlib.parse_message(full_msg)        

        # Check if parsing failed
        if cmd is chatlib.ERROR_RETURN and data is chatlib.ERROR_RETURN:
            print("Failed to parse message")
            return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN
        
        return cmd, data

    except Exception as e:
        print(f"Error receiving or parsing message: {e}")
        return chatlib.ERROR_RETURN, chatlib.ERROR_RETURN	
    

def build_send_recv_parse(conn, cmd, data):
    build_and_send_message(conn, cmd, data)
    msg_code, data = recv_message_and_parse(conn)
    return msg_code, data


def get_score(conn):
    msg_code, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["my_score_msg"], "")
    
    if msg_code == chatlib.PROTOCOL_SERVER["your_score_msg"]:
        print(f"Your current score is: {data}")
    else:
        print(f"Error getting score. Server replied with message code: {msg_code}")

def get_highscore(conn):
    msg_code, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["highscore_msg"], "")
    
    if msg_code == chatlib.PROTOCOL_SERVER["all_score_msg"]:
        print("High-Score table:")
        print(data)
    else:
        print(f"Error getting high scores. Server replied with message code: {msg_code}")


def play_question(conn):
    # Ask for a question
    msg_code, question_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["get_question_msg"], "")
    
    if msg_code == chatlib.PROTOCOL_SERVER["no_questions_msg"]:
        print("No more questions. Game over!")
        return
    if msg_code != chatlib.PROTOCOL_SERVER["your_question_msg"]:
        print(f"Unexpected response from server: {msg_code}")
        return

    # Parse and print the question
    question_parts = chatlib.split_data(question_data, 6)  # Expecting 6 parts: id + question + 4 answers
    if question_parts == [chatlib.ERROR_RETURN]:
        print("Error: Invalid question format received from server.")
        return

    q_id, question, *answers = question_parts
    print(f"Q: {question}")
    for i, answer in enumerate(answers, 1):
        print(f"\t{i}. {answer}")

    # Get user's answer
    while True:
        try:
            user_answer = int(input("Please choose an answer [1-4]: "))
            if 1 <= user_answer <= 4:
                break
            print("Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Send the answer and get feedback
    msg_code, data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["send_answer_msg"], chatlib.join_data([q_id, str(user_answer)]))
    
    if msg_code == chatlib.PROTOCOL_SERVER["correct_answer_msg"]:
        print("Correct answer!")
    elif msg_code == chatlib.PROTOCOL_SERVER["wrong_answer_msg"]:
        print(f"Wrong answer. The correct answer is: {data}")
    else:
        print(f"Unexpected response from server: {msg_code}")    
    

def get_logged_users(conn):
    msg_code, users_data = build_send_recv_parse(conn, chatlib.PROTOCOL_CLIENT["logged_msg"], "")
    if msg_code == chatlib.PROTOCOL_SERVER["logged_answer_msg"]:
        print(f"Logged users:\n{users_data}")
    else:
        print(f"Unexpected response from server: {msg_code}")


def logout(conn):
    build_and_send_message(conn, chatlib.PROTOCOL_CLIENT["logout_msg"], "")

	

def main():
    conn = connect()
    login(conn)

    while True:
        print("\np        Play a trivia question"
              "\ns        Get my score"
              "\nh        Get high score"
              "\nl        Get logged users"
              "\nq        Quit")
        user_choice = input("Please enter your choice: ").lower()
        
        if user_choice == "p":
            play_question(conn)
        elif user_choice == "s":
            get_score(conn)
        elif user_choice == "h":
            get_highscore(conn)
        elif user_choice == "l":
            get_logged_users(conn)
        elif user_choice == "q":
            logout(conn)
            print("Goodbye!")
            break
        else:
            print("Invalid input, please try again!")
    
    conn.close()


if __name__ == '__main__':
    main()
