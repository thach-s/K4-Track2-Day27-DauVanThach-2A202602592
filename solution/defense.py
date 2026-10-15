"""Streaming checks using only the documented, metered toolkit."""
from api import Verdict


def register(ctx):
    ctx.on("data_batch", check_data_batch)
    ctx.on("contract_checkpoint", check_contract_checkpoint)
    ctx.on("lineage_run", check_lineage_run)
    ctx.on("feature_materialization", check_feature_materialization)
    ctx.on("embedding_batch", check_embedding_batch)


def verdict(alert, pillar):
    return Verdict(alert=bool(alert), pillar=pillar)


def check_data_batch(payload, ctx):
    p = ctx.tools.batch_profile(payload["batch_id"])
    if "error" in p:
        return verdict(False, "checks")
    b = ctx.baseline
    # Combine standardized two-sided signals without learning from faulty data.
    row_z = abs(p["row_count"] - (b["row_count_min"] + b["row_count_max"]) / 2) / ((b["row_count_max"] - b["row_count_min"]) / 6)
    amount_z = abs(p["mean_amount"] - (b["mean_amount_min"] + b["mean_amount_max"]) / 2) / ((b["mean_amount_max"] - b["mean_amount_min"]) / 6)
    alert = (row_z > 3 or amount_z > 3 or
             row_z * row_z + amount_z * amount_z > 13.82 or
             p["null_rate"]["customer_id"] > b["null_rate_max"] or
             p["staleness_min"] > b["staleness_min_max"])
    return verdict(alert, "checks")


def check_contract_checkpoint(payload, ctx):
    p = ctx.tools.contract_diff(payload["contract_id"], payload["checkpoint_batch_id"])
    return verdict("error" not in p and (bool(p["violations"]) or
                   p["freshness_delay_min"] > ctx.baseline["freshness_delay_max_min"]), "contracts")


def check_lineage_run(payload, ctx):
    p = ctx.tools.lineage_graph_slice(payload["run_id"])
    if "error" in p:
        return verdict(False, "lineage")
    expected = payload.get("expected_upstream")
    missing = expected is not None and bool(set(expected) - set(p["actual_upstream"]))
    # Learn recurring graph shapes online; a strict subset of a repeatedly
    # observed shape is evidence of a missing edge, without fixed source names.
    actual = frozenset(p["actual_upstream"])
    shapes = ctx.state.setdefault("lineage_shapes", {})
    if expected is None:
        missing = any(count >= 3 and actual < shape for shape, count in shapes.items())
    if not missing:
        shapes[actual] = shapes.get(actual, 0) + 1
    expected_count = payload.get("expected_downstream_count")
    orphan = (p["actual_downstream_count"] == 0 or
              (expected_count is not None and p["actual_downstream_count"] < expected_count))
    return verdict(missing or orphan or p["duration_ms"] > ctx.baseline["lineage_duration_ms_max"], "lineage")


def check_feature_materialization(payload, ctx):
    p = ctx.tools.feature_drift(payload["feature_view"], payload["batch_id"])
    return verdict("error" not in p and p["mean_shift_sigma"] > ctx.baseline["feature_mean_shift_sigma_max"], "ai_infra")


def check_embedding_batch(payload, ctx):
    p = ctx.tools.embedding_drift(payload["corpus"], payload["chunk_batch_id"])
    return verdict("error" not in p and (
        p["centroid_shift"] > ctx.baseline["embedding_centroid_shift_max"] or
        p["avg_doc_age_days"] > ctx.baseline["corpus_avg_doc_age_days_max"]), "ai_infra")
