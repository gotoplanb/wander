// Golden suite for spec `fibonacci_nth` (schema_version 1).
// Signature: pub fn fibonacci_nth(n: u32) -> u64
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `fibonacci_nth` at the parent module.

#[cfg(test)]
mod tests {
    use super::fibonacci_nth;
    #[test] fn zero() { assert_eq!(fibonacci_nth(0), 0); }
    #[test] fn one() { assert_eq!(fibonacci_nth(1), 1); }
    #[test] fn two() { assert_eq!(fibonacci_nth(2), 1); }
    #[test] fn ten() { assert_eq!(fibonacci_nth(10), 55); }
    #[test] fn twenty() { assert_eq!(fibonacci_nth(20), 6765); }
    #[test] fn ninety() { assert_eq!(fibonacci_nth(90), 2_880_067_194_370_816_120); }
}
