// Golden suite for spec `reverse_string` (schema_version 1).
// Signature: pub fn reverse_string(s: &str) -> String
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::reverse_string;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::reverse_string;
#[test] fn empty() { assert_eq!(reverse_string(""), ""); }
#[test] fn single_char() { assert_eq!(reverse_string("a"), "a"); }
#[test] fn basic() { assert_eq!(reverse_string("hello"), "olleh"); }
#[test] fn even_length() { assert_eq!(reverse_string("abcd"), "dcba"); }
#[test] fn unicode_multibyte() { assert_eq!(reverse_string("héllo"), "olléh"); }
