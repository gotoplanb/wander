// Golden suite for spec `sum_to_n` (schema_version 1).
// Signature: pub fn sum_to_n(n: u64) -> u64
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::sum_to_n;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::sum_to_n;
#[test] fn zero() { assert_eq!(sum_to_n(0), 0); }
#[test] fn one() { assert_eq!(sum_to_n(1), 1); }
#[test] fn ten() { assert_eq!(sum_to_n(10), 55); }
#[test] fn hundred() { assert_eq!(sum_to_n(100), 5050); }
#[test] fn large() { assert_eq!(sum_to_n(1_000_000), 500_000_500_000); }
