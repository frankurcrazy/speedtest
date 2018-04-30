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

The client is not ready yet, please use `netcat` along with `dd` for now
```sh
dd if=/dev/zero bs=32k | nc [server ip] [server port] > /dev/null
```


