// Golden suite for spec `fizzbuzz` (schema_version 1).
// Signature: pub fn fizzbuzz(n: u32) -> Vec<String>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::fizzbuzz;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::fizzbuzz;
#[test] fn zero_returns_empty() { assert_eq!(fizzbuzz(0), Vec::<String>::new()); }
#[test] fn one_returns_one() { assert_eq!(fizzbuzz(1), vec!["1".to_string()]); }
#[test] fn three_returns_fizz_at_end() {
    assert_eq!(fizzbuzz(3), vec!["1", "2", "Fizz"]);
}
#[test] fn five_returns_buzz_at_end() {
    assert_eq!(fizzbuzz(5), vec!["1", "2", "Fizz", "4", "Buzz"]);
}
#[test] fn fifteen_ends_with_fizzbuzz() {
    let out = fizzbuzz(15);
    assert_eq!(out.len(), 15);
    assert_eq!(out[14], "FizzBuzz");
    assert_eq!(out[2], "Fizz");
    assert_eq!(out[4], "Buzz");
}
