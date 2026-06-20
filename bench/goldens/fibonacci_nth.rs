// Golden suite for spec `fibonacci_nth` (schema_version 1).
// Signature: pub fn fibonacci_nth(n: u32) -> u64
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::fibonacci_nth;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::fibonacci_nth;
#[test] fn zero() { assert_eq!(fibonacci_nth(0), 0); }
#[test] fn one() { assert_eq!(fibonacci_nth(1), 1); }
#[test] fn two() { assert_eq!(fibonacci_nth(2), 1); }
#[test] fn ten() { assert_eq!(fibonacci_nth(10), 55); }
#[test] fn twenty() { assert_eq!(fibonacci_nth(20), 6765); }
#[test] fn ninety() { assert_eq!(fibonacci_nth(90), 2_880_067_194_370_816_120); }
