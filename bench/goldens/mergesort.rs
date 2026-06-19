// Golden suite for spec `mergesort` (schema_version 1).
// Signature: pub fn mergesort(xs: Vec<i32>) -> Vec<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `mergesort` at the parent module.

#[cfg(test)]
mod tests {
    use super::mergesort;
    #[test] fn empty() { assert_eq!(mergesort(vec![]), Vec::<i32>::new()); }
    #[test] fn single() { assert_eq!(mergesort(vec![1]), vec![1]); }
    #[test] fn already_sorted() { assert_eq!(mergesort(vec![1, 2, 3]), vec![1, 2, 3]); }
    #[test] fn reverse_sorted() { assert_eq!(mergesort(vec![3, 2, 1]), vec![1, 2, 3]); }
    #[test] fn duplicates() {
        assert_eq!(mergesort(vec![3, 1, 3, 2, 1]), vec![1, 1, 2, 3, 3]);
    }
    #[test] fn negatives() {
        assert_eq!(mergesort(vec![-3, -1, -4, -1, -5]), vec![-5, -4, -3, -1, -1]);
    }
    #[test] fn mixed() {
        assert_eq!(mergesort(vec![5, 2, 9, 1, 5, 6]), vec![1, 2, 5, 5, 6, 9]);
    }
}
