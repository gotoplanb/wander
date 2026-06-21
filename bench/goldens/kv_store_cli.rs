// Golden suite for spec `kv_store_cli` (schema_version 1).
// Signature: pub fn process_commands(commands: &[&str], times: &[u64]) -> Vec<String>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::process_commands;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::process_commands;

#[test] fn set_then_get_returns_value() {
    let out = process_commands(
        &["set foo bar", "get foo"],
        &[100, 100],
    );
    assert_eq!(out, vec!["OK".to_string(), "bar".to_string()]);
}

#[test] fn get_absent_returns_nil() {
    let out = process_commands(&["get missing"], &[0]);
    assert_eq!(out, vec!["(nil)".to_string()]);
}

#[test] fn set_replaces_value() {
    let out = process_commands(
        &["set k v1", "set k v2", "get k"],
        &[0, 0, 0],
    );
    assert_eq!(out, vec!["OK".to_string(), "OK".to_string(), "v2".to_string()]);
}

#[test] fn ttl_expiry() {
    // set with ttl=5 at t=100, get at t=102 (alive), get at t=200 (expired)
    let out = process_commands(
        &["set foo bar 5", "get foo", "get foo"],
        &[100, 102, 200],
    );
    assert_eq!(out, vec!["OK".to_string(), "bar".to_string(), "(nil)".to_string()]);
}

#[test] fn set_without_ttl_clears_old_ttl() {
    // First set has ttl=5 at t=100; second set with no ttl at t=101
    // should clear the expiry. get at t=200 should still see the value.
    let out = process_commands(
        &["set foo a 5", "set foo b", "get foo"],
        &[100, 101, 200],
    );
    assert_eq!(out, vec!["OK".to_string(), "OK".to_string(), "b".to_string()]);
}

#[test] fn del_returns_one_when_present_zero_when_absent() {
    let out = process_commands(
        &["del missing", "set k v", "del k", "del k"],
        &[0, 0, 0, 0],
    );
    assert_eq!(
        out,
        vec!["0".to_string(), "OK".to_string(), "1".to_string(), "0".to_string()],
    );
}

#[test] fn del_returns_one_even_for_expired_key() {
    // Spec says del returns 1 if the key was present "regardless of
    // whether it was expired" — the key is technically still in the
    // store, just expired. del removes it.
    let out = process_commands(
        &["set foo bar 5", "del foo"],
        &[100, 200],  // foo is expired at t=200 (set at t=100 with ttl=5)
    );
    assert_eq!(out, vec!["OK".to_string(), "1".to_string()]);
}

#[test] fn list_sorted_ascending() {
    let out = process_commands(
        &["set b 2", "set a 1", "set c 3", "list"],
        &[0, 0, 0, 0],
    );
    assert_eq!(
        out,
        vec![
            "OK".to_string(),
            "OK".to_string(),
            "OK".to_string(),
            "a=1\nb=2\nc=3".to_string(),
        ],
    );
}

#[test] fn list_omits_expired_keys() {
    let out = process_commands(
        &["set live x", "set dying y 5", "list"],
        &[0, 0, 100],  // dying is expired at t=100
    );
    assert_eq!(
        out,
        vec!["OK".to_string(), "OK".to_string(), "live=x".to_string()],
    );
}

#[test] fn list_empty_store() {
    let out = process_commands(&["list"], &[0]);
    assert_eq!(out, vec!["(empty)".to_string()]);
}

#[test] fn unknown_command() {
    let out = process_commands(&["badcmd"], &[0]);
    assert_eq!(out, vec!["ERR unknown command".to_string()]);
}

#[test] fn bad_arg_count() {
    let out = process_commands(
        &["set foo", "get"],  // set missing value; get missing key
        &[0, 0],
    );
    assert_eq!(
        out,
        vec!["ERR bad arg count".to_string(), "ERR bad arg count".to_string()],
    );
}

#[test] fn bad_ttl() {
    // ttl=0 is not positive; non-integer is not parseable.
    let out = process_commands(
        &["set k v 0", "set k v notanumber"],
        &[0, 0],
    );
    assert_eq!(
        out,
        vec!["ERR bad ttl".to_string(), "ERR bad ttl".to_string()],
    );
}

#[test] fn expired_get_removes_key_as_side_effect() {
    // After an expired get, the key should not be findable by list either.
    let out = process_commands(
        &["set foo bar 5", "get foo", "list"],
        &[100, 200, 200],  // get at t=200 sees expired; list at t=200 sees nothing
    );
    assert_eq!(
        out,
        vec!["OK".to_string(), "(nil)".to_string(), "(empty)".to_string()],
    );
}
