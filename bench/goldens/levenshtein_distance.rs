// Golden suite for spec `levenshtein_distance` (schema_version 1).
// Signature: pub fn levenshtein_distance(a: &str, b: &str) -> usize
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::levenshtein_distance;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::levenshtein_distance;
#[test] fn equal_zero() { assert_eq!(levenshtein_distance("abc", "abc"), 0); }
#[test] fn empty_vs_nonempty() {
    assert_eq!(levenshtein_distance("", "abc"), 3);
    assert_eq!(levenshtein_distance("rust", ""), 4);
}
#[test] fn single_substitution() {
    assert_eq!(levenshtein_distance("cat", "bat"), 1);
}
#[test] fn classic_kitten_sitting() {
    assert_eq!(levenshtein_distance("kitten", "sitting"), 3);
}
#[test] fn classic_flaw_lawn() {
    assert_eq!(levenshtein_distance("flaw", "lawn"), 2);
}
#[test] fn transposition_costs_two() {
    // Levenshtein treats a transposition as two edits, not one
    // (Damerau-Levenshtein would treat it as one — that is NOT this
    // function).
    assert_eq!(levenshtein_distance("ab", "ba"), 2);
}
