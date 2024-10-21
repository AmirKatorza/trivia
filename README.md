# Trivia Game Client-Server

A multiplayer trivia game implemented in Python using socket programming. The server manages multiple concurrent players, tracks scores, and fetches trivia questions from the Open Trivia Database API. Players can compete against each other, view high scores, and see who else is currently playing.

## Features

- Multi-player support using `select` for concurrent connections
- Real-time score tracking and high-score board
- Questions fetched from Open Trivia Database
- User authentication system
- Persistent storage of user data and scores
- Custom protocol implementation for client-server communication

## Prerequisites

- Python 3.x
- `requests` library for fetching trivia questions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/trivia-game.git
cd trivia-game
```

2. Install required packages:
```bash
pip install requests
```

## How to Use

1. Start the server:
```bash
python server.py
```
The server will initialize and start listening for connections on localhost:5678.

2. Start one or more client instances:
```bash
python client.py
```

3. When the client starts, you can:
   - Log in using an existing account or use test accounts:
     - Username: `test`, Password: `test`
     - Username: `yossi`, Password: `123`
     - Username: `master`, Password: `master`
   
4. Available commands in the game:
   - `p` - Play a trivia question
   - `s` - Get your current score
   - `h` - View the high score board
   - `l` - See who else is currently playing
   - `q` - Quit the game

## Project Structure

- `server.py` - Main server implementation
- `client.py` - Client implementation
- `chatlib.py` - Protocol implementation and message handling
- `users.txt` - User database (automatically created)
- `questions.txt` - Local question database (optional)

## Protocol

The game uses a custom protocol for client-server communication. Messages are structured as:
```
cmd|length|data
```
Where:
- `cmd` is a 16-byte command name
- `length` is a 4-byte message length
- `data` contains the actual message payload

## Notes

- The server saves user data automatically when shutting down
- Questions are fetched from the Open Trivia Database API
- Multiple clients can connect and play simultaneously
- Each question can only be asked once per user

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available under the [MIT License](LICENSE).
