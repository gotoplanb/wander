// Golden suite for spec `binary_search_sorted` (schema_version 1).
// Signature: pub fn binary_search_sorted(xs: &[i32], target: i32) -> Option<usize>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `binary_search_sorted` at the parent
// module.

#[cfg(test)]
mod tests {
    use super::binary_search_sorted;
    #[test] fn empty() { assert_eq!(binary_search_sorted(&[], 1), None); }
    #[test] fn single_found() { assert_eq!(binary_search_sorted(&[1], 1), Some(0)); }
    #[test] fn single_not_found() { assert_eq!(binary_search_sorted(&[1], 2), None); }
    #[test] fn first() {
        assert_eq!(binary_search_sorted(&[1, 3, 5, 7, 9], 1), Some(0));
    }
    #[test] fn last() {
        assert_eq!(binary_search_sorted(&[1, 3, 5, 7, 9], 9), Some(4));
    }
    #[test] fn middle() {
        assert_eq!(binary_search_sorted(&[1, 3, 5, 7, 9], 5), Some(2));
    }
    #[test] fn missing() {
        assert_eq!(binary_search_sorted(&[1, 3, 5, 7, 9], 4), None);
    }
}
