// Golden suite for spec `insertion_sort` (schema_version 1).
// Signature: pub fn insertion_sort(xs: Vec<i32>) -> Vec<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::insertion_sort;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::insertion_sort;
#[test] fn empty() { assert_eq!(insertion_sort(vec![]), Vec::<i32>::new()); }
#[test] fn single() { assert_eq!(insertion_sort(vec![1]), vec![1]); }
#[test] fn already_sorted() { assert_eq!(insertion_sort(vec![1, 2, 3]), vec![1, 2, 3]); }
#[test] fn reverse_sorted() { assert_eq!(insertion_sort(vec![3, 2, 1]), vec![1, 2, 3]); }
#[test] fn duplicates() {
    assert_eq!(insertion_sort(vec![3, 1, 3, 2, 1]), vec![1, 1, 2, 3, 3]);
}
#[test] fn negatives() {
    assert_eq!(insertion_sort(vec![-3, -1, -2]), vec![-3, -2, -1]);
}
#[test] fn mixed() {
    assert_eq!(insertion_sort(vec![5, 2, 9, 1, 5, 6]), vec![1, 2, 5, 5, 6, 9]);
}
