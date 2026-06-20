// Golden suite for spec `longest_common_subsequence` (schema_version 1).
// Signature: pub fn longest_common_subsequence(a: &str, b: &str) -> usize
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::longest_common_subsequence;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::longest_common_subsequence;
#[test] fn equal() { assert_eq!(longest_common_subsequence("abc", "abc"), 3); }
#[test] fn disjoint() { assert_eq!(longest_common_subsequence("abc", "def"), 0); }
#[test] fn either_empty() {
    assert_eq!(longest_common_subsequence("", "anything"), 0);
    assert_eq!(longest_common_subsequence("anything", ""), 0);
}
#[test] fn classic_abcde_ace() {
    assert_eq!(longest_common_subsequence("abcde", "ace"), 3);
}
#[test] fn classic_aggtab_gxtxayb() {
    assert_eq!(longest_common_subsequence("AGGTAB", "GXTXAYB"), 4);
}
#[test] fn case_sensitive() {
    assert_eq!(longest_common_subsequence("abc", "ABC"), 0);
}
