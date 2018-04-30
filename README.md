SpeedTest
=========

## What is this?
This is a realy simple speed testing utilites that help you find out the maximum speed in your network enviroment.

## How to use it?
Currently only the server side is provided.
To launch the server:
```sh
python server.py
```

The server will listen on port 9487 and waiting for client to connect. ***What about client?***
As mentioned earlier, at current stage, only the server side is provided. In order to connect to the server, we can use `netcat` along with `dd` and `pv`.
