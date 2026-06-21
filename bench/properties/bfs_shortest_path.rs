// Property suite for spec `bfs_shortest_path`.
// Signature: pub fn bfs_shortest_path(graph: &[Vec<usize>], start: usize, target: usize) -> Option<usize>

use model_solution::bfs_shortest_path;
use proptest::prelude::*;

/// A generator that produces a small directed graph: an adjacency list
/// of length `n`, where each vertex has 0..3 outgoing edges to vertices
/// in `0..n`. Self-loops + parallel edges allowed (BFS handles them).
fn small_graph() -> impl Strategy<Value = Vec<Vec<usize>>> {
    (1usize..8).prop_flat_map(|n| {
        proptest::collection::vec(
            proptest::collection::vec(0..n, 0..3),
            n..=n,
        )
    })
}

proptest! {
    /// Reflexive: bfs(g, v, v) == Some(0) for any valid v.
    #[test]
    fn self_is_zero(g in small_graph()) {
        for v in 0..g.len() {
            prop_assert_eq!(bfs_shortest_path(&g, v, v), Some(0));
        }
    }

    /// If reachable, the distance is at most n-1 (vertices in graph).
    /// A correct BFS never returns a longer path than the longest
    /// simple path possible in a graph of `n` vertices.
    #[test]
    fn reachable_distance_bounded(g in small_graph(), s in 0usize..8, t in 0usize..8) {
        if s < g.len() && t < g.len() {
            if let Some(d) = bfs_shortest_path(&g, s, t) {
                prop_assert!(d < g.len(), "distance {} >= |V| {}", d, g.len());
            }
        }
    }
}
