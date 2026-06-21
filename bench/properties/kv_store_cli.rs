// Property suite for spec `kv_store_cli`.
// Signature: pub fn process_commands(commands: &[&str], times: &[u64]) -> Vec<String>

use model_solution::process_commands;
use proptest::prelude::*;

/// Generator: a single ASCII alphanumeric+underscore identifier
/// (used for both keys and values per the spec).
fn ident() -> impl Strategy<Value = String> {
    "[a-zA-Z0-9_]{1,8}"
}

proptest! {
    /// set-then-get round trip: any value you set, you can get back
    /// (with no TTL, at the same time).
    #[test]
    fn set_then_get_round_trip(k in ident(), v in ident()) {
        let set_cmd = format!("set {} {}", k, v);
        let get_cmd = format!("get {}", k);
        let out = process_commands(&[&set_cmd, &get_cmd], &[0, 0]);
        prop_assert_eq!(out.len(), 2);
        prop_assert_eq!(&out[0], "OK");
        prop_assert_eq!(&out[1], &v);
    }

    /// set-then-del-then-get: after delete, key is absent.
    #[test]
    fn set_then_del_then_get_is_nil(k in ident(), v in ident()) {
        let set_cmd = format!("set {} {}", k, v);
        let del_cmd = format!("del {}", k);
        let get_cmd = format!("get {}", k);
        let out = process_commands(&[&set_cmd, &del_cmd, &get_cmd], &[0, 0, 0]);
        prop_assert_eq!(&out[0], "OK");
        prop_assert_eq!(&out[1], "1");
        prop_assert_eq!(&out[2], "(nil)");
    }

    /// TTL monotonicity: a key set with `ttl_secs` at time `t0` is
    /// alive at any `t <= t0 + ttl_secs - 1` and absent at any
    /// `t >= t0 + ttl_secs`.
    #[test]
    fn ttl_monotone_at_threshold(
        k in ident(),
        v in ident(),
        ttl in 1u64..50,
    ) {
        let t0: u64 = 1000;
        let set_cmd = format!("set {} {} {}", k, v, ttl);
        let get_cmd = format!("get {}", k);
        // Alive at t0 + ttl - 1 (because expiry is `>` strict per the
        // spec — expiry time itself triggers expiration).
        let out_alive = process_commands(&[&set_cmd, &get_cmd], &[t0, t0 + ttl - 1]);
        prop_assert_eq!(&out_alive[1], &v, "expected alive at t0+ttl-1");
        // Absent at t0 + ttl.
        let out_dead = process_commands(&[&set_cmd, &get_cmd], &[t0, t0 + ttl]);
        prop_assert_eq!(&out_dead[1], "(nil)", "expected expired at t0+ttl");
    }

    /// Set is idempotent on value: setting twice with the same value
    /// has the same observable state as setting once.
    #[test]
    fn set_twice_same_value_is_idempotent(k in ident(), v in ident()) {
        let set_cmd = format!("set {} {}", k, v);
        let get_cmd = format!("get {}", k);
        let out1 = process_commands(&[&set_cmd, &get_cmd], &[0, 0]);
        let out2 = process_commands(&[&set_cmd, &set_cmd, &get_cmd], &[0, 0, 0]);
        prop_assert_eq!(&out1[1], &out2[2]);  // get returns the same thing
    }

    /// Output vector length always matches command count.
    /// (Catches: missing output, dropped command, extra output.)
    #[test]
    fn output_length_matches_command_count(
        commands in proptest::collection::vec(
            prop_oneof![
                ident().prop_map(|k| format!("get {}", k)),
                (ident(), ident()).prop_map(|(k, v)| format!("set {} {}", k, v)),
                ident().prop_map(|k| format!("del {}", k)),
                Just("list".to_string()),
            ],
            0..16,
        ),
    ) {
        let times: Vec<u64> = vec![0; commands.len()];
        let cmd_refs: Vec<&str> = commands.iter().map(|s| s.as_str()).collect();
        let out = process_commands(&cmd_refs, &times);
        prop_assert_eq!(out.len(), commands.len());
    }

    /// `list` output, if non-empty, is sorted ascending by key.
    /// (Validates the "ascending sort order" requirement.)
    #[test]
    fn list_output_is_sorted(
        kvs in proptest::collection::vec((ident(), ident()), 1..6),
    ) {
        let mut cmds: Vec<String> = kvs.iter().map(|(k, v)| format!("set {} {}", k, v)).collect();
        cmds.push("list".to_string());
        let times: Vec<u64> = vec![0; cmds.len()];
        let cmd_refs: Vec<&str> = cmds.iter().map(|s| s.as_str()).collect();
        let out = process_commands(&cmd_refs, &times);
        let list_output = out.last().unwrap();
        if list_output != "(empty)" {
            let lines: Vec<&str> = list_output.split('\n').collect();
            for window in lines.windows(2) {
                let a = window[0].split('=').next().unwrap();
                let b = window[1].split('=').next().unwrap();
                prop_assert!(a <= b, "list not sorted at {:?} > {:?}", a, b);
            }
        }
    }
}
