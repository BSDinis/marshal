# marshal
Compiler for a DSL that makes marshaling and unmarshaling structs and commands easier in C.

## Purpose
Automatically marshaling and unmarshaling structs or passing commands between networked peers in C is unnecessarily complex.
One time-honored solution is using some form of RPC. However, there are a few issues with this approach.

  1. RPC is designed to make the call transparently, giving the illusion that there is a function being called locally. This is fine in some situations, but in others makes for a too high level abstraction. If you just want to send structs in a platform-independent fashion, you're out of luck with RPC.
  2. RPC's abstraction means a certain port is used, the connection is established for you. You may not want this. You could prefer to send the commands yourself.
  3. Given this model, RPC does not allow for assynchronous operations, which is **bad**. Or at least not a very nice thing to do.
  4. Last, and least, RPC is old. You know it is from another era when it optionally compiles for **K&R C**.

## Installation

### Requirements

`>=python3.7`

`pyinstaller`

To build, run
```zsh
$ make build;
$ mv marshal somewhere/in/your/path;
```

## Contributing
Spin up a PR

## More information
On the wiki
