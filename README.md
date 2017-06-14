# logrotor
   
a lightweight log store with time-based rotation

## Why
The main purpose of this project is to connect [nginx](https://nginx.org/) and [goaccess](https://goaccess.io/) when both services are running as docker containers. It provides a nginx-compatible syslog endpoint to collect access log messages from nginx containers, handles log rotation and has some tweaks to work with goaccess.

## Quickstart

A minimal configuration would look like this:

```yaml:config.yml
---
rotate_every_seconds: 120
flush_every_seconds: 2
storage:
    path: ./test_storage
    size: 5

endpoints:
    - type: UdpEndpoint
      port: 1024
```

The logrotor docker container expects a config file under `/srv/config.yml`. To run with docker:

    docker run --volume $(pwd)/config.yml:/srv/config.yml --publish 1024:1024/udp --name test_logrotor reifenbt/logrotor
    
Run without docker (Python 3.6 required):

    pip install git+https://github.com/tom-mi/logrotor
    logrotor --config config.yml
    
Send a message:

    echo -n "Hello World!" | nc -u -c localhost 1024
    
Read the logs (when running with docker):

    docker exec test_logrotor cat ./test_storage/current
    docker exec test_logrotor /bin/sh -c 'cat /test_storage/data/*'
    
Read the logs (when running without docker):

    cat ./test_storage/current
    cat ./test_storage/data/*
    
## Running with nginx & goaccess docker containers

A simple example is contained in the repository.

    git clone https://github.com/tom-mi/logrotor
    cd logrotor
    cd examples/nginx_via_syslog
    docker-compose up
    
The nginx webserver is reachable under http://localhost:8080/. The goaccess reports are served under http://localhost:8080/report/.

## Advanced Configuration

Currently, UDP and syslog (UDP, according to RFC 3164) endpoints are supported. See the following example for all currently available configuration options:

```yaml
---
rotate_every_seconds: 30         # required
flush_every_seconds: 2           # required

storage:
    path: ./test_storage         # required
    size: 5                      # required
    rotate_delay_seconds: 0      # delay between deleting and re-creating a file during rotation
                                 # (used with goaccess)

endpoints:

    - type: UdpEndpoint          # required
      bind: 0.0.0.0
      port: 1024                 # required
      format: '{host} {message}' # available variables: host, port, message
      splitlines: False          # split multiline messages and apply format to each line

    - type: SyslogUdpEndpoint    # required
      bind: 0.0.0.0
      port: 514
      format: '{timestamp:%b %e %H:%M:%S} {hostname} {message}'
                                 # available variables: src_host, src_port, timestamp, level, facility,
                                 #                      hostname, tag, pid, message
```

    
