# Banking System
![mongoDB_icon](assets/mongoDB2.png)
### [MongoDB documentation page](https://www.mongodb.com/docs/)
## Description
This project is an attempt at recreating banks' monetization and transaction systems. Using *mongoDB* in *python*, the user can easily connect to the server and start making some transactions between accounts and more.

## How to use
First of all, make sure you have all the required libraries installed by running `pip install -r requirements.txt` in your command line.
After the installation is over, you can go ahead and run *server.py* (either by running *run-server.bat* or typing `python server.py` in your command line). Do the same thing in order to run *client.py*. Now, you can type *help* in your *client* side to start using commands.

## Used Dependencies
- PyMongo(v4.6.0) -> Used for creating an easy accessed class that maintains the local MongoDB database;
- Socket -> For communicating over the internet with different computers;
- Threading -> To create threads of *clients* that run simultaneously, as well to create mutex locks that block people from using the same function at once (when more than 2 connections running that function can result in errors. [Read more](https://stackoverflow.com/questions/34524/what-is-a-mutex));
- Getpass -> To type hidden passwords;
- Hashlib -> To generate hashes for transaction ids, as well as to hash pins/passwords to send to the server;
- Colorama(v0.4.6) -> To add color for the *client* UI;
- Bson(v0.5.10) -> To make jsons into strings.


## Features
1. Due to `MongoDB's` speed and scalability, the program offers fast responses;
2. Although the program doesn't have a GUI, it is still easy to use because of the `help` command that gives you all the possible commands you can send;
3. Threads play a key role in making the server able to hold multiple users at once. `Threading` creates a thread for every connection and also handles mutexes;
## Examples
![example 1](assets/Screenshot_1.png)

## Help
Feel free to ask any questions, either on *github* or on my [moraru.matei24@gmail.com](mailto:moraru.matei24@gmail.com).