// Golden suite for spec `sum_to_n` (schema_version 1).
// Signature: pub fn sum_to_n(n: u64) -> u64
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `sum_to_n` at the parent module.

#[cfg(test)]
mod tests {
    use super::sum_to_n;
    #[test] fn zero() { assert_eq!(sum_to_n(0), 0); }
    #[test] fn one() { assert_eq!(sum_to_n(1), 1); }
    #[test] fn ten() { assert_eq!(sum_to_n(10), 55); }
    #[test] fn hundred() { assert_eq!(sum_to_n(100), 5050); }
    #[test] fn large() { assert_eq!(sum_to_n(1_000_000), 500_000_500_000); }
}
