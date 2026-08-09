/* [] goto union memcpy() must not be features */
#if UNRELATED
int unrelated(void) { return 0; }
#endif

static int file_global;
extern int external_value;
static int file_static_function(void) { return 0; }
int true_local_static(void) { static int state = 0; return ++state; }
struct Flexible { int count; char bytes[]; };
int array_parameter(int values[]) { return values[0]; }
int fixed_array(void) { int values[3] = {0}; return values[0]; }
int comment_and_string(void) { const char *s = "goto union memcpy() []"; return s[0]; }
#if OUTER
# if INNER
int nested_conditional(void) { return 1; }
# endif
#endif
#if WRAPPED
int under_conditional(void) { return 1; }
#endif
DECLARE_THING(example);
int macro_inside(void) { TRACE(example); return 0; }
