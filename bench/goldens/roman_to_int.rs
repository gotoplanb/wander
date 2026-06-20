// Golden suite for spec `roman_to_int` (schema_version 1).
// Signature: pub fn roman_to_int(s: &str) -> u32
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::roman_to_int;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::roman_to_int;
#[test] fn three_i() { assert_eq!(roman_to_int("III"), 3); }
#[test] fn iv_subtractive() { assert_eq!(roman_to_int("IV"), 4); }
#[test] fn ix_subtractive() { assert_eq!(roman_to_int("IX"), 9); }
#[test] fn lviii() { assert_eq!(roman_to_int("LVIII"), 58); }
#[test] fn mcmxciv() { assert_eq!(roman_to_int("MCMXCIV"), 1994); }
#[test] fn mmmcmxcix() { assert_eq!(roman_to_int("MMMCMXCIX"), 3999); }
#[test] fn xl_and_cd() { assert_eq!(roman_to_int("CDXLIV"), 444); }
