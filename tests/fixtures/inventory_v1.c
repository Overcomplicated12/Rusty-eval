#include <stdarg.h>
#define DECLARE(name) int name(void) { return 0; }

int global_value;
struct Packet { int count; char bytes[]; };
union Value { int number; void *pointer; };
enum Color { RED, BLUE };
struct Bits { unsigned enabled:1; };
typedef int Count;

int simple(int value) { return value + 1; }
int use_global(void) { global_value += 1; return global_value; }
int pointer_ok(const char *text) { return text != 0; }
int pointer_math(char *p) { p += 1; return *p; }
int double_pointer(char **out) { return out != 0; }
void *void_ptr(void *value) { return value; }
void copy(char *out, const char *in) { memcpy(out, in, 3); }
void allocate(void) { void *p = malloc(4); free(p); }
int array(void) { int values[3] = {0}; return values[0]; }
int callback(int (*fn)(int), int value) { return fn(value); }
int jump(int value) { if (value) goto done; return 0; done: return 1; }
int varargs(const char *format, ...) { va_list args; va_start(args, format); va_end(args); return 0; }
int static_state(void) { static int count; return ++count; }
#if FEATURE
int conditional(void) { return 1; }
#endif
