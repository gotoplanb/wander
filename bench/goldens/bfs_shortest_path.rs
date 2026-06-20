// Golden suite for spec `bfs_shortest_path` (schema_version 1).
// Signature: pub fn bfs_shortest_path(graph: &[Vec<usize>], start: usize, target: usize) -> Option<usize>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::bfs_shortest_path;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::bfs_shortest_path;
#[test] fn self_is_zero() {
    let g: Vec<Vec<usize>> = vec![vec![]];
    assert_eq!(bfs_shortest_path(&g, 0, 0), Some(0));
}
#[test] fn disconnected_is_none() {
    let g: Vec<Vec<usize>> = vec![vec![1], vec![], vec![]];
    assert_eq!(bfs_shortest_path(&g, 0, 2), None);
}
#[test] fn linear_chain() {
    let g: Vec<Vec<usize>> =
        vec![vec![1], vec![2], vec![3], vec![4], vec![]];
    assert_eq!(bfs_shortest_path(&g, 0, 4), Some(4));
}
#[test] fn branching_picks_shortest() {
    // 0 -> 1 -> 2 -> 3, plus a direct 0 -> 3 edge
    let g: Vec<Vec<usize>> =
        vec![vec![1, 3], vec![2], vec![3], vec![]];
    assert_eq!(bfs_shortest_path(&g, 0, 3), Some(1));
}
#[test] fn cycle_doesnt_loop() {
    // 0 -> 1 -> 2 -> {0, 3}: revisiting 0 must not loop forever
    let g: Vec<Vec<usize>> = vec![vec![1], vec![2], vec![0, 3], vec![]];
    assert_eq!(bfs_shortest_path(&g, 0, 3), Some(3));
}
