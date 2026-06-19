// Golden suite for spec `quicksort` (schema_version 1).
// Signature: pub fn quicksort(xs: Vec<i32>) -> Vec<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `quicksort` at the parent module.

#[cfg(test)]
mod tests {
    use super::quicksort;
    #[test] fn empty() { assert_eq!(quicksort(vec![]), Vec::<i32>::new()); }
    #[test] fn single() { assert_eq!(quicksort(vec![1]), vec![1]); }
    #[test] fn already_sorted() { assert_eq!(quicksort(vec![1, 2, 3]), vec![1, 2, 3]); }
    #[test] fn reverse_sorted() { assert_eq!(quicksort(vec![3, 2, 1]), vec![1, 2, 3]); }
    #[test] fn duplicates() {
        assert_eq!(quicksort(vec![3, 3, 3, 3]), vec![3, 3, 3, 3]);
    }
    #[test] fn negatives() {
        assert_eq!(quicksort(vec![-3, -1, -2]), vec![-3, -2, -1]);
    }
    #[test] fn mixed() {
        assert_eq!(
            quicksort(vec![3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]),
            vec![1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]
        );
    }
}
