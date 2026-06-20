// Golden suite for spec `is_anagram` (schema_version 1).
// Signature: pub fn is_anagram(a: &str, b: &str) -> bool
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::is_anagram;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::is_anagram;
#[test] fn both_empty() { assert!(is_anagram("", "")); }
#[test] fn equal() { assert!(is_anagram("abc", "abc")); }
#[test] fn basic_true() { assert!(is_anagram("listen", "silent")); }
#[test] fn basic_false() { assert!(!is_anagram("hello", "world")); }
#[test] fn case_and_space() {
    assert!(is_anagram("Conversation", "voices rant on"));
}
#[test] fn length_mismatch() { assert!(!is_anagram("a", "ab")); }
