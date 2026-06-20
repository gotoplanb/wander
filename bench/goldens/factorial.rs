// Golden suite for spec `factorial` (schema_version 1).
// Signature: pub fn factorial(n: u32) -> u64
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::factorial;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::factorial;
#[test] fn zero() { assert_eq!(factorial(0), 1); }
#[test] fn one() { assert_eq!(factorial(1), 1); }
#[test] fn five() { assert_eq!(factorial(5), 120); }
#[test] fn ten() { assert_eq!(factorial(10), 3_628_800); }
#[test] fn twenty() { assert_eq!(factorial(20), 2_432_902_008_176_640_000); }
