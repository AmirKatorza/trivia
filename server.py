##############################################################################
# server.py
##############################################################################

import socket
import select
import random
import chatlib
import requests as r
import html


# GLOBALS
users = {}  # {user_name: {"password": , "score": , "questions_asked": []}}
questions = {}  # {qustion_key: ["question", "answer1", "answer2", "answer2", "answer4", "num_correct_answer"]}
logged_users = {}  # a dictionary of client hostnames to usernames - will be used later
messages_to_send  = []

ERROR_MSG = "Error!"
SERVER_PORT = 5678
SERVER_IP = "127.0.0.1"


# HELPER SOCKET METHODS

def print_client_sockets(client_sockets):
    for c in client_sockets:
        print("\t", c.getpeername())


def build_and_send_message(conn, code, msg):
    """
    Builds a new message using chatlib, wanted code and message. 
    Prints debug info, then sends it to the given socket.
    Parameters: conn (socket object), code (str), data (str)
    Returns: Nothing
    """
    global messages_to_send
    
    # Build the message using chatlib
    full_msg = chatlib.build_message(code, msg)

    # Check if the message was successfully built
    if full_msg is chatlib.ERROR_RETURN:
        print("Failed to build message. Exiting function.")
        return

    # Debug print
    print("[SERVER] ", full_msg) 
    
    messages_to_send.append((conn, full_msg))    


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

def load_questions_from_web():
    questions = {}
    
    try:
        response = r.get("https://opentdb.com/api.php?amount=50&type=multiple")
        response.raise_for_status()  # Will raise an HTTPError for bad responses

        data = response.json()  # This already returns a dictionary (or list)

        # Ensure we have results in the expected format
        if "results" not in data:
            print("Unexpected data structure from API")
            return questions

        for question_no, question in enumerate(data["results"], start=1):
            # Decode HTML entities in questions and answers
            question_text = html.unescape(question["question"])
            correct_answer = html.unescape(question["correct_answer"])
            incorrect_answers = [html.unescape(ans) for ans in question["incorrect_answers"]]

            # Combine correct and incorrect answers, and shuffle them
            all_answers = incorrect_answers + [correct_answer]
            random.shuffle(all_answers)

            # Find the index of the correct answer in the shuffled list
            correct_answer_index = all_answers.index(correct_answer) + 1  # Adding 1 to make it 1-based indexing

            # Store the question and answers in the desired format
            questions[question_no] = {
                "question": question_text,
                "answers": all_answers,
                "correct": correct_answer_index  # 1-based index of the correct answer
            }
        print("Question DB download was completed")
        
    except r.RequestException as e:
        print(f"Error fetching questions: {e}")
    except ValueError:
        print("Error parsing the response as JSON")
    
    return questions


def load_questions(file_path='questions.txt'):
    """
    Loads game questions from a text file into the questions dictionary.
    Format of each line in the text file:
    question|answer1|answer2|answer3|answer4|correct_answer_number
    
    :param file_path: path to the questions file
    :return: dictionary of questions
    """
    questions = {}
    try:
        with open(file_path, 'r') as f:
            for i, line in enumerate(f, start=1):
                # Remove whitespace and split the line by '|'
                parts = line.strip().split('|')
                if len(parts) != 6:
                    continue  # Skip invalid lines

                question, answer1, answer2, answer3, answer4, correct_answer = parts
                
                # Store data in the questions dictionary
                questions[i] = {
                    "question": question,
                    "answers": [answer1, answer2, answer3, answer4],
                    "correct": int(correct_answer)  # Convert the correct answer number to an integer
                }
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Creating new file with default questions...")
        
        # Create default questions with consistent IDs
        questions = {
            1: {
                "question": "How much is 2+2?", 
                "answers": ["3", "4", "2", "1"], 
                "correct": 2
            },
            2: {
                "question": "What is the capital of France?", 
                "answers": ["Lion", "Marseille", "Paris", "Montpellier"], 
                "correct": 3
            },
            3: {
                "question": "What is the capital of Israel?", 
                "answers": ["Jerusalem", "Tel-Aviv", "Beer-Sheva", "Haifa"], 
                "correct": 1
            },
            4: {
                "question": "What is the capital of England?", 
                "answers": ["Liverpool", "Bristol", "Manchester", "London"], 
                "correct": 4
            }
        }

        # Save default questions to file
        save_questions(questions, file_path)
    except Exception as e:
        print(f"Error loading questions file: {e}")
        
    return questions

def save_questions(questions, file_path='questions.txt'):
    """
    Saves the questions dictionary to a text file.
    
    Args:
    questions (dict): Dictionary containing question data
    file_path (str): Path to the file where the data should be saved
    """
    try:
        with open(file_path, "w") as file:
            for q_id, data in questions.items():
                # Join answers with '|' and write the line in the correct format
                answers = "|".join(data["answers"])
                file.write(f"{q_id}|{data['question']}|{answers}|{data['correct']}\n")
    except Exception as e:
        print(f"Error saving questions file: {e}")



def load_user_database(file_path='users.txt'):
    """
    Loads user information from a text file into the users dictionary.
    Format of each line in the text file:
    username|password|score|question_id1,question_id2,...
    
    :param file_path: path to the users file
    :return: dictionary of users
    """
    users = {}
    try:
        with open(file_path, 'r') as f:
            for line in f:
                # Remove whitespace and split the line by '|'
                parts = line.strip().split('|')
                if len(parts) != 4:
                    continue  # Skip invalid lines

                username, password, score, questions_asked = parts
                
                # Parse questions_asked as a list
                questions_asked_list = questions_asked.split(',') if questions_asked else []
                
                # Store data in the users dictionary
                users[username] = {
                    "password": password,
                    "score": int(score),  # Convert score to an integer
                    "questions_asked": questions_asked_list  # Store the list of asked question IDs
                }
        
    except FileNotFoundError:
        print(f"File '{file_path}' not found. Creating new file with default users...")
        users = {
            "test": {"password": "test", "score": 0, "questions_asked": []},
            "yossi": {"password": "123", "score": 50, "questions_asked": []},
            "master": {"password": "master", "score": 200, "questions_asked": []}
            }
        # Save default users to file
        save_user_database(users)
    except Exception as e:
        print(f"Error loading users file: {e}")
                
    return users


def save_user_database(users, file_path='users.txt'):
    """
    Saves the users dictionary to a text file.
    
    Args:
    users (dict): Dictionary containing user data
    file_path (str): Path to the file where the data should be saved
    """
    try:
        with open(file_path, "w") as file:
            for username, data in users.items():
                # Convert the questions_asked list to a comma-separated string
                questions_asked_str = ','.join(data['questions_asked']) if data['questions_asked'] else ''
                # Write the data in the format 'username|password|score|questions_asked'
                file.write(f"{username}|{data['password']}|{data['score']}|{questions_asked_str}\n")
    except Exception as e:
        print(f"Error saving users file: {e}")


def save_all_data():
    """
    Saves both users and questions data to their respective files
    """
    save_user_database(users)
    save_questions(questions)


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
    Closes the given socket (in later chapters, also remove user from logged_users dictionary)
    Receives: socket
    Returns: chatlib.ERROR_RETURN
    """
    global logged_users
    
    # Check if the client is in logged_users to avoid KeyError
    client_address = conn.getpeername()
    if client_address in logged_users:
        print(f"User {logged_users[client_address]} has left the game!")
        logged_users.pop(client_address, None)  # Safely remove client
    else:
        print(f"Unknown user from {client_address} disconnected.")
    
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

    # Split the message into username and password
    user_name, password = chatlib.split_data(data, 2)

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


def create_random_question(username):
    """
    Returns a random question that the user has not been asked before.
    If all questions have been asked, returns None.
    
    :param username: the user requesting the question
    :return: a tuple (question_data, question_id) or None if no new questions available
    """
    global users
    global questions
    
    # Get the set of question IDs the user has been asked
    asked_questions = set(users[username]["questions_asked"])
    
    # Get the set of all question IDs
    all_question_ids = set(questions.keys())
    
    # Get the set of remaining questions by subtracting asked questions from all questions
    remaining_questions = all_question_ids - asked_questions
    
    # If no remaining questions, return None
    if not remaining_questions:
        return None
    
    # Choose a random question from the remaining ones
    random_question_id = random.choice(list(remaining_questions))
    
    # Get question text and answers
    question_text = questions[random_question_id]["question"]
    question_answers = questions[random_question_id]["answers"]
    
    # Create the full question data
    question_data = chatlib.join_data([str(random_question_id), question_text] + question_answers)
    
    return question_data, random_question_id    


def handle_question_message(conn, username):
    """
    Sends a random question to the user, ensuring the user has not been asked the question before.
    If no new questions are available, sends a message indicating all questions have been asked.
    
    :param conn: socket connection
    :param username: the user requesting the question
    """
    global users
    
    # Get a new random question for the user
    result = create_random_question(username)
    
    if result is None:
        # No new questions available, send appropriate message
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["no_questions_msg"], "")
    else:
        # Extract question data and question ID
        question_data, question_id = result
        
        # Add the question ID to the list of questions the user has been asked
        users[username]["questions_asked"].append(question_id)
        
        # Send the question to the user
        build_and_send_message(conn, chatlib.PROTOCOL_SERVER["your_question_msg"], question_data)    


def handle_answer_message(conn, username, answer_data):
    global questions
    global users
    
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
        save_user_database(users)
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
            handle_question_message(conn, user)
        elif cmd == chatlib.PROTOCOL_CLIENT["send_answer_msg"]:
            handle_answer_message(conn, user, data)
        else:
            send_error(conn, "Unknown command after login")


def main():
    # Initializes global users and questions dicionaries using load functions, will be used later
    global users
    global questions
    global messages_to_send
    
    # Load users and questions from text files
    users = load_user_database()   # Load users from users.txt
    questions = load_questions_from_web()   # Load questions from the web

    print("Welcome to Trivia Server!")
    
    # Set up the server socket
    server_socket = setup_socket()

    # Keep track of client sockets and messages to send
    client_sockets = []
    
    while True:
        try:
            ready_to_read, ready_to_write, in_error = select.select([server_socket] + client_sockets, client_sockets, [])

            # Handle ready_to_read sockes
            for current_socket in ready_to_read:
                if current_socket is server_socket:
                    # Accept new client connections
                    client_socket, client_address = server_socket.accept()
                    client_sockets.append(client_socket)
                    print(f"New client joined! Address: {client_address}, Total clients: {len(client_sockets)}")
                    print_client_sockets(client_sockets)
                else:
                     # Handle data from an existing client
                     print("New data from client")
                     try:
                        # Receive and parse client message
                        cmd, data = recv_message_and_parse(current_socket)
                    
                        # If client disconnects or sends an empty message
                        if cmd == chatlib.ERROR_RETURN:
                            print(f"Connection with {current_socket.getpeername()} closed")
                            handle_logout_message(current_socket)
                            client_sockets.remove(current_socket)
                            print(f"Total clients: {len(client_sockets)}")
                            print_client_sockets(client_sockets)
                            continue
                    
                        # If the client logs out
                        if cmd == chatlib.PROTOCOL_CLIENT["logout_msg"]:
                            handle_logout_message(current_socket)
                            client_sockets.remove(current_socket)
                            print(f"Total clients: {len(client_sockets)}")
                            print_client_sockets(client_sockets)
                            continue
                    
                        # Route the message to the appropriate handler
                        handle_client_message(current_socket, cmd, data)                
                
                     except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
                        # Handle the case where the client disconnected unexpectedly
                        print(f"Client {current_socket.getpeername()} disconnected abruptly: {e}")
                        handle_logout_message(current_socket)
                        client_sockets.remove(current_socket) 
                        print(f"Total clients: {len(client_sockets)}")                       
                        print_client_sockets(client_sockets)
                        continue
            
            # Handle messages waiting to be sent
            
            msg_to_remove = []
            
            for message in messages_to_send:
                current_socket, data = message
                if current_socket in ready_to_write:
                    try:
                        current_socket.send(data.encode())
                        msg_to_remove.append(message)
                    except OSError as e:
                        print(f"Error sending message to {current_socket.getpeername()}: {e}")
                        handle_logout_message(current_socket)
                        client_sockets.remove(current_socket)                        
                        print(f"Total clients: {len(client_sockets)}")                       
                        print_client_sockets(client_sockets)
            
            # Remove successfully sent messages
            for message in msg_to_remove:
                messages_to_send.remove(message)
            
        
        except KeyboardInterrupt:
            # Handle server shutdown (Ctrl+C on the server)
            print("\nServer is shutting down")
            save_all_data()  # Save data before shutting down

            # Notify connected clients about the shutdown
            for client_socket in client_sockets:
                try:
                    client_socket.send("Server is shutting down...".encode())
                    client_socket.close()
                except OSError:
                    pass

            break

    server_socket.close()

if __name__ == '__main__':
    main()
