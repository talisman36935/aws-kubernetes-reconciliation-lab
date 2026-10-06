# Baseline marker mismatch — 2026-10-06

Hosted attempt [37521237841](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37521237841)
used baseline `4bac703499054eadd50925e44f98ce3a91d039c3` and candidate
`aa66120b2e6b5b343e99fbc0643a22991cc947e9`. Validate passed for the candidate
at [37521046883](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37521046883).

The disposable kind cluster was created, the three-instance database and baseline
apps became ready, and baseline migration completed. The run failed before its
first application phase and deleted the cluster (`cluster_deleted: true`). The
selected baseline commit already carried the `candidate` test marker, while the
smoke assertion expected `baseline`. The prior successful release/configuration
experiment used baseline `bba5671e7d0c741445da0b272563729d754affc0`, whose fixture
does carry the baseline marker. The retry uses that exact earlier baseline and
regenerates the new candidate fixture with the candidate marker. No cloud
resources were provisioned.
