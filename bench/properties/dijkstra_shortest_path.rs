// Property suite for spec `dijkstra_shortest_path`.
// Signature:
//   pub fn dijkstra_shortest_path(graph: &[Vec<(usize, u32)>], start: usize, target: usize) -> Option<u32>

use model_solution::dijkstra_shortest_path;
use proptest::prelude::*;

fn small_weighted_graph() -> impl Strategy<Value = Vec<Vec<(usize, u32)>>> {
    (1usize..6).prop_flat_map(|n| {
        proptest::collection::vec(
            proptest::collection::vec((0..n, 1u32..10), 0..3),
            n..=n,
        )
    })
}

proptest! {
    /// Reflexive: distance to self is Some(0).
    #[test]
    fn self_is_zero(g in small_weighted_graph()) {
        for v in 0..g.len() {
            prop_assert_eq!(dijkstra_shortest_path(&g, v, v), Some(0));
        }
    }

    /// If reachable, the distance is bounded by the sum of all edge weights
    /// (an over-approximation, but it catches "returned absurd value" bugs).
    #[test]
    fn distance_bounded_by_total_weight(g in small_weighted_graph(), s in 0usize..6, t in 0usize..6) {
        if s < g.len() && t < g.len() {
            if let Some(d) = dijkstra_shortest_path(&g, s, t) {
                let total: u32 = g.iter().flat_map(|adj| adj.iter().map(|(_, w)| *w)).sum();
                prop_assert!(d <= total, "distance {} > total edge weight {}", d, total);
            }
        }
    }
}
