// Golden suite for spec `count_vowels` (schema_version 1).
// Signature: pub fn count_vowels(s: &str) -> usize
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::count_vowels;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::count_vowels;
#[test] fn empty() { assert_eq!(count_vowels(""), 0); }
#[test] fn no_vowels() { assert_eq!(count_vowels("rhythm"), 0); }
#[test] fn all_vowels_upper() { assert_eq!(count_vowels("AEIOU"), 5); }
#[test] fn mixed_case() { assert_eq!(count_vowels("Hello"), 2); }
#[test] fn y_is_not_a_vowel() { assert_eq!(count_vowels("yyyy"), 0); }
