HANDOVER — ADP-013 Routing UI (Sprint 11)
================================================================================
Date: 2026-08-23
Repo: KiCad_AI_Integration

SUMMARY
-------
Routing tab added to the Assistant shell (Ctrl+7). Freerouting autoroute workflow
with approve-before-run, checkpoint accept/reject, live DRC quality report, and
optional post-route AI review. Phase 1.5/3 work remains on main from prior sprint.

WHAT WAS DONE
-------------
1. **Routing tab** — [[routing_tab.py]], [[routing_shell.py]] (Ctrl+7)
2. **Workflow** — policy summary, approve-before-route, background `run_routing()`,
   accept/reject checkpoint, post-route DRC via shared `run_live_drc()`
3. **Post-route AI review** — `run_post_route_review()` in `inference/audit.py`
4. **CLI** — `--ui-routing` opens shell on Routing tab
5. **Tests** — ui/routing_*, integration/test_routing_e2e.py (@pytest.mark.kicad)
6. **380 tests passing**

PREREQUISITES (manual E2E — Freerouting KiCad plugin NOT required)
------------------------------------------------------------------
- KiCad AI Integration plugin or Scripting Console (pcbnew for DSN/SES)
- Standalone Freerouting JAR or CLI + `routing_enabled: true`
- Open `.kicad_pcb` in PCB Editor; optional `kicad-cli` for post-route DRC

STILL OPEN (ADP-013)
--------------------
- ~~Human architecture review approval~~ — approved 2026-08-24
- ~~Routing policy persistence~~ — [[routing_policy.json]] via [[policy_store.py]]
- ~~Phase 4: parse AI policy JSON into RoutingPolicy~~ — Routing tab **Generate policy from AI**
- Phase 5: compare candidates, re-route loop

PRIOR — Phase 1.5 + Phase 3
---------------------------
Live KiCad context, one-click audits, ReviewReport JSON under kicad_ai/reviews/.

AUTHORITATIVE STATUS
--------------------
- [[tasks/MASTER_TASK_LIST.md]] (Track E — Routing Abstraction)
- [[docs/Specifications/Freerouting_Integration.md]]
- [[docs/Architecture/ADP-013-Routing-Abstraction.md]]
