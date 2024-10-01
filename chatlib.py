# Protocol Constants

CMD_FIELD_LENGTH = 16	# Exact length of cmd field (in bytes)
LENGTH_FIELD_LENGTH = 4   # Exact length of length field (in bytes)
MAX_DATA_LENGTH = 10**LENGTH_FIELD_LENGTH-1  # Max size of data field according to protocol
MSG_HEADER_LENGTH = CMD_FIELD_LENGTH + 1 + LENGTH_FIELD_LENGTH + 1  # Exact size of header (CMD+LENGTH fields)
MAX_MSG_LENGTH = MSG_HEADER_LENGTH + MAX_DATA_LENGTH  # Max size of total message
DELIMITER = "|"  # Delimiter character in protocol
DATA_DELIMITER = "#"  # Delimiter in the data part of the message

# Protocol Messages 
# In this dictionary we will have all the client and server command names

PROTOCOL_CLIENT = {
"login_msg" : "LOGIN",
"logout_msg" : "LOGOUT",
"logged_msg": "LOGGED",
"get_question_msg": "GET_QUESTION",
"send_answer_msg": "SEND_ANSWER",
"my_score_msg": "MY_SCORE",
"highscore_msg": "HIGHSCORE"
} # .. Add more commands if needed


PROTOCOL_SERVER = {
"login_ok_msg" : "LOGIN_OK",
"logged_answer_msg": "LOGGED_ANSWER",
"your_question_msg": "YOUR_QUESTION",
"correct_answer_msg": "CORRECT_ANSWER",
"wrong_answer_msg": "WRONG_ANSWER",
"your_score_msg": "YOUR_SCORE",
"all_score_msg": "ALL_SCORE",
"error_msg" : "ERROR",
"no_questions_msg": "NO_QUESTIONS"
} # ..  Add more commands if needed


# Other constants

ERROR_RETURN = None  # What is returned in case of an error


def build_message(cmd, data):
	"""
	Gets command name (str) and data field (str) and creates a valid protocol message
	Returns: str, or None if error occured
	"""
    
	if len(cmd) > CMD_FIELD_LENGTH or len(data) > MAX_DATA_LENGTH:
		return ERROR_RETURN
    
    # Pad the command to exactly CMD_FIELD_LENGTH
	cmd_padded = cmd + " " * (CMD_FIELD_LENGTH - len(cmd))
    
    # Get the length of the data as a string, and pad it to LENGTH_FIELD_LENGTH
	data_length = str(len(data))
	length_field_padded = str(len(data)).zfill(LENGTH_FIELD_LENGTH)
    
    # Join everything together with the DELIMITER
	full_msg = DELIMITER.join([cmd_padded, length_field_padded, data])
    
	return full_msg


def parse_message(data):
	"""
	Parses protocol message and returns command name and data field
	Returns: cmd (str), data (str). If some error occured, returns None, None
	"""
    
	# Split the data using the DELIMITER
	data_splitted = data.split(DELIMITER)
	
	# Check if the data splits into exactly 3 parts (cmd, length, and message)
	if len(data_splitted) != 3:
		return (ERROR_RETURN, ERROR_RETURN)
	
	cmd = data_splitted[0]	
	
	# Check if command length is exactly 16
	if (len(cmd) != CMD_FIELD_LENGTH):
		return (ERROR_RETURN, ERROR_RETURN)
	
	 # Strip any extra spaces from the command
	cmd = cmd.strip()

	length_field = data_splitted[1]
	
	if len(length_field) != LENGTH_FIELD_LENGTH or not length_field.strip().isdigit():
		return (ERROR_RETURN, ERROR_RETURN)	

	length_field_int = int(length_field)
	
	msg = data_splitted[2]
    
    # Check if the actual length of the message matches the length field
	if len(msg) != length_field_int or len(msg) > MAX_DATA_LENGTH:
		return (ERROR_RETURN, ERROR_RETURN)	
		
    # The function should return 2 values
	return cmd, msg

	
def split_data(msg, expected_fields):
	"""
	Helper method. gets a string and number of expected fields in it. Splits the string 
	using protocol's data field delimiter (|#) and validates that there are correct number of fields.
	Returns: list of fields if all ok. If some error occured, returns None
	"""
	
	count = msg.count(DATA_DELIMITER)
	if count == expected_fields:
		return msg.split(DATA_DELIMITER)
	
	return [ERROR_RETURN]


def join_data(msg_fields):
	"""
	Helper method. Gets a list, joins all of it's fields to one string divided by the data delimiter. 
	Returns: string that looks like cell1#cell2#cell3
	"""
	
	return DATA_DELIMITER.join(msg_fields)


# Testing block
if __name__ == "__main__":
	# Test cases for split_data
	print(split_data("username#password", 1))  # Expected: ['username', 'password']
	print(split_data("user#name#pass#word", 2))  # Expected: [None] (too many fields)
	print(split_data("username", 2))  # Expected: [None] (not enough fields)

	# Test cases for join_data
	print(join_data(['username', 'password']))  # Expected: "username#password"
	print(join_data(['user', 'name', 'pass', 'word']))  # Expected: "user#name#pass#word"

	# Test cases for join_data
	print(build_message("LOGIN", "aaaa#bbbb"))
	print(build_message("LOGIN", "aaaabbbb"))
	print(build_message("LOGIN", ""))
	print(build_message("0123456789ABCDEFGH", ""))
	print(build_message("A", "A"*(MAX_DATA_LENGTH+1)))

	# Test cases
	print(parse_message("LOGIN           |   9|aaaa#bbbb"))  # Expected: ('LOGIN', 'aaaa#bbbb')
	print(parse_message("LOGIN           |  09|aaaa#bbbb"))  # Expected: ('LOGIN', 'aaaa#bbbb')
	print(parse_message("LOGIN           |0009|aaaa#bbbb"))  # Expected: ('LOGIN', 'aaaa#bbbb')
	print(parse_message("LOGIN           |   4|data"))       # Expected: ('LOGIN', 'data')
