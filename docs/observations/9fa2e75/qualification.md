# Source-promotion preflight rejection — 2026-10-06

Attempt [37520307121](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37520307121)
compared baseline `4bac703499054eadd50925e44f98ce3a91d039c3` with candidate
`9fa2e75f4efaad2c01a25a102ca61be222829619`. AWS Validate for the candidate
passed as [37520099449](https://github.com/talisman36935/aws-kubernetes-reconciliation-lab/actions/runs/37520099449).

The hosted qualification stopped at its preflight because the original harness
only allowed configuration rollback when source/image locks were identical. No
kind cluster was created: rejection occurred before the create-cluster stage.
No cloud resources were used. The harness is being extended to distinguish
configuration-only changes from a pinned application source/image promotion,
and to record exact source/image identity for every phase.
