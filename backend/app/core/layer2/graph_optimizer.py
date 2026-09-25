"""
Sub-Module 2.3: Sub-Query Dependency Graph Optimizer
Research Basis: Q-DREAM SDOM (Subquestion Dependency Optimizer Module) - ACL 2025
Constructs and validates the Directed Acyclic Graph (DAG) of sub-query dependencies.
Groups sub-queries into concurrent parallel execution stages via topological sorting.
"""

from graphlib import TopologicalSorter, CycleError
from typing import List, Dict, Any, Tuple
from app.schemas.layer2 import SubQueryPlan


class GraphOptimizer:
    """Optimizes execution order into parallel DAG stages using Python graphlib."""

    def optimize_dag(self, subqueries: List[SubQueryPlan]) -> Tuple[List[List[str]], List[SubQueryPlan]]:
        """
        Organizes sub-queries into parallel execution stages:
        Stage 0: [sq_1, sq_2] (can be retrieved simultaneously)
        Stage 1: [sq_3]       (waits for stage 0 results)
        """
        if not subqueries:
            return [], []

        sq_map: Dict[str, SubQueryPlan] = {sq.id: sq for sq in subqueries}
        all_ids = set(sq_map.keys())

        # Clean dependencies: drop unknown IDs or self-references to prevent errors
        clean_graph: Dict[str, set[str]] = {}
        for sq in subqueries:
            valid_deps = set(d for d in sq.depends_on if d in all_ids and d != sq.id)
            sq.depends_on = list(valid_deps)
            clean_graph[sq.id] = valid_deps

        # Attempt topological sorting & stage assignment
        try:
            # Calculate in-degree / stage levels
            stages: List[List[str]] = self._compute_parallel_stages(clean_graph, sq_map)
        except CycleError:
            # In case of cyclic dependency, break cycles by falling back to sequential chain
            stages = [[sq.id] for sq in subqueries]
            for idx, sq in enumerate(subqueries):
                sq.stage_index = idx
                sq.depends_on = [subqueries[idx-1].id] if idx > 0 else []
            return stages, subqueries

        # Assign stage_index to each SubQueryPlan
        for stage_idx, stage_nodes in enumerate(stages):
            for node_id in stage_nodes:
                if node_id in sq_map:
                    sq_map[node_id].stage_index = stage_idx

        return stages, list(sq_map.values())

    def _compute_parallel_stages(
        self,
        graph: Dict[str, set[str]],
        sq_map: Dict[str, SubQueryPlan]
    ) -> List[List[str]]:
        """
        Group nodes into parallel stages using topological levels.
        A node's stage is max(stage(dep) for dep in graph[node]) + 1.
        """
        # Node -> stage level
        node_stages: Dict[str, int] = {}
        
        # Build forward edges: dep -> list of nodes waiting on dep
        ts = TopologicalSorter(graph)
        ts.prepare()
        
        stages: List[List[str]] = []
        while ts.is_active():
            ready_nodes = list(ts.get_ready())
            if not ready_nodes:
                break
            stages.append(ready_nodes)
            ts.done(*ready_nodes)

        return stages
