// Golden suite for spec `max_in_slice` (schema_version 1).
// Signature: pub fn max_in_slice(xs: &[i32]) -> Option<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `max_in_slice` at the parent module.

#[cfg(test)]
mod tests {
    use super::max_in_slice;
    #[test] fn empty() { assert_eq!(max_in_slice(&[]), None); }
    #[test] fn single() { assert_eq!(max_in_slice(&[42]), Some(42)); }
    #[test] fn basic() { assert_eq!(max_in_slice(&[3, 1, 4, 1, 5, 9, 2, 6]), Some(9)); }
    #[test] fn all_negative() { assert_eq!(max_in_slice(&[-5, -1, -10]), Some(-1)); }
    #[test] fn duplicates_at_max() { assert_eq!(max_in_slice(&[7, 7, 7]), Some(7)); }
}
