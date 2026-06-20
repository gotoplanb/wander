// Golden suite for spec `max_in_slice` (schema_version 1).
// Signature: pub fn max_in_slice(xs: &[i32]) -> Option<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::max_in_slice;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::max_in_slice;
#[test] fn empty() { assert_eq!(max_in_slice(&[]), None); }
#[test] fn single() { assert_eq!(max_in_slice(&[42]), Some(42)); }
#[test] fn basic() { assert_eq!(max_in_slice(&[3, 1, 4, 1, 5, 9, 2, 6]), Some(9)); }
#[test] fn all_negative() { assert_eq!(max_in_slice(&[-5, -1, -10]), Some(-1)); }
#[test] fn duplicates_at_max() { assert_eq!(max_in_slice(&[7, 7, 7]), Some(7)); }
