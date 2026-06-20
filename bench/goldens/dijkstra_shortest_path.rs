// Golden suite for spec `dijkstra_shortest_path` (schema_version 1).
// Signature:
//   pub fn dijkstra_shortest_path(graph: &[Vec<(usize, u32)>],
//                                 start: usize,
//                                 target: usize) -> Option<u32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::dijkstra_shortest_path;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::dijkstra_shortest_path;
#[test] fn self_is_zero() {
    let g: Vec<Vec<(usize, u32)>> = vec![vec![]];
    assert_eq!(dijkstra_shortest_path(&g, 0, 0), Some(0));
}
#[test] fn disconnected_is_none() {
    let g: Vec<Vec<(usize, u32)>> =
        vec![vec![(1, 1)], vec![], vec![]];
    assert_eq!(dijkstra_shortest_path(&g, 0, 2), None);
}
#[test] fn simple_chain() {
    // 0 -[1]-> 1 -[2]-> 2
    let g: Vec<Vec<(usize, u32)>> =
        vec![vec![(1, 1)], vec![(2, 2)], vec![]];
    assert_eq!(dijkstra_shortest_path(&g, 0, 2), Some(3));
}
#[test] fn shorter_via_cheap_edges() {
    // 0 -[1]-> 1 -[2]-> 2, plus 0 -[5]-> 2 direct
    // best = 1 + 2 = 3, beating the direct 5
    let g: Vec<Vec<(usize, u32)>> =
        vec![vec![(1, 1), (2, 5)], vec![(2, 2)], vec![]];
    assert_eq!(dijkstra_shortest_path(&g, 0, 2), Some(3));
}
#[test] fn diamond_picks_lighter() {
    // 0 -[1]-> 1 -[4]-> 3
    // 0 -[2]-> 2 -[1]-> 3
    // best = via 2: 2 + 1 = 3
    let g: Vec<Vec<(usize, u32)>> = vec![
        vec![(1, 1), (2, 2)],
        vec![(3, 4)],
        vec![(3, 1)],
        vec![],
    ];
    assert_eq!(dijkstra_shortest_path(&g, 0, 3), Some(3));
}
