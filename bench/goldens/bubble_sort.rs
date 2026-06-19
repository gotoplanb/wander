// Golden suite for spec `bubble_sort` (schema_version 1).
// Signature: pub fn bubble_sort(xs: Vec<i32>) -> Vec<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `bubble_sort` at the parent module.

#[cfg(test)]
mod tests {
    use super::bubble_sort;
    #[test] fn empty() { assert_eq!(bubble_sort(vec![]), Vec::<i32>::new()); }
    #[test] fn single() { assert_eq!(bubble_sort(vec![1]), vec![1]); }
    #[test] fn already_sorted() { assert_eq!(bubble_sort(vec![1, 2, 3]), vec![1, 2, 3]); }
    #[test] fn reverse_sorted() { assert_eq!(bubble_sort(vec![3, 2, 1]), vec![1, 2, 3]); }
    #[test] fn duplicates() {
        assert_eq!(bubble_sort(vec![3, 1, 3, 2, 1]), vec![1, 1, 2, 3, 3]);
    }
    #[test] fn negatives() {
        assert_eq!(bubble_sort(vec![-3, -1, -2]), vec![-3, -2, -1]);
    }
    #[test] fn mixed() {
        assert_eq!(bubble_sort(vec![5, 2, 9, 1, 5, 6]), vec![1, 2, 5, 5, 6, 9]);
    }
}
