pub fn safe_fn() {
    let label = "unsafe in string";
    println!("{label}");
}

pub unsafe fn declared_unsafe() {
    let _value = 1;
}

pub fn uses_unsafe() {
    // unsafe in comment
    let _bytes = unsafe {
        helper();
        helper_two();
        5usize
    };
}

pub fn multiple_unsafe_regions() {
    unsafe {
        helper();
    }
    unsafe {
        helper_two();
    }
}

pub fn nested_unsafe() {
    unsafe {
        if true {
            unsafe {
                helper();
            }
        }
    }
}

unsafe trait Marker {
    fn mark(&self);
}

struct Wrapper;

unsafe impl Marker for Wrapper {
    fn mark(&self) {}
}

fn helper() {}
fn helper_two() {}

/* unsafe in block comment
   still unsafe text only
*/
