## How to use

```bash
$ docker build -t masterdata-generatoer:0.1 .
$ docker run --rm masterdata-generatoer python main.py

$ python3 main.py -h
usage: main.py [-h] [-t TARGET] [-p PORT] [-l LINE] [-v VERSION] [--https HTTPS]

importer master data for stress test

optional arguments:
  -h, --help            show this help message and exit
  -t TARGET, --target TARGET
                        target host
  -p PORT, --port PORT  target port
  -l LINE, --line LINE  number of master data
  -v VERSION, --version VERSION
                        target api version
```