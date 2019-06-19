# marshal
Compiler for a DSL that makes marshaling and unmarshaling structs and commands easier in C.

## Purpose
Automatically marshaling and unmarshaling structs or passing commands between networked peers in C is unnecessarily complex.
One time-honored solution is using some form of RPC. However, there are a few issues with this approach.

  1. RPC is designed to make the call transparently, giving the illusion that there is a function being called locally. This is fine in some situations, but in others makes for a too high level abstraction. If you just want to send structs in a platform-independent fashion, you're out of luck with RPC.
  2. RPC's abstraction means a certain port is used, the connection is established for you. You may not want this. You could prefer to send the commands yourself. You may want a non-blocking connection, to establish a TLS channel.
  3. Last, and least, RPC is old. You know it is from another era when it optionally compiles for **K&R C**.

## Aim
To make a compiler for a C-like DSL that allows the definition of structs and functions and generates the corresponding C code for marshaling and unmarshaling.

The files will have an `.m` extension.

As an example, the following `marshal` source file:

```C
struct fancy_struct {
  int a;
  double b;
};
```

Will generate the following header file:

```C
// headers ommitted
typedef struct fancy_struct {
  int a;
  double b;
} fancy_struct;

// note: you have to pass an array with least sizeof(fancy_struct) B
int fancy_struct_marshal(fancy_struct *, uint8_t *);

/* note: fancy struct must have been allocd previously
 * pass the size of the buffer to make sure it is valid
 * will return -1 on unsuccessful unmarshalling */
int fancy_struct_unmarshal(fancy_struct *, uint8_t *, ssize_t);
```


Now, you can also define a function-based API.

```C
T f(X b, Y c);
```

Which will in turn generate the following header file (besides the struct marshaling and unmarshaling).

```C
// get necessary size for the response based on the code
inline ssize_t func_resp_sz(uint8_t code);

// parse and exec
int func_parse_exec(uint8_t * cmd, ssize_t, uint8_t *resp, ssize_t );

// generate nice function handlers
typedef T (func_f_handler_t *)(X, Y);
typedef int (resp_f__handler_t *)(T);

ssize_t const func_f_sz = XXX;

// again, the buffer and the struct must be must be  allocd
// these are for the caller
int func_f_marshal(uint8_t *, int);


// this is for the receiver
int func_f_register(func_f_t);
int exec_cmd(filename_cmd_t *, filename_resp_t *);
```

And the corresponding source code. In there, a function to specifically parse and exec function `f`:
```C
int func_f_parse_exec(uint8_t * cmd, ssize_t, uint8_t *resp, ssize_t)
```
