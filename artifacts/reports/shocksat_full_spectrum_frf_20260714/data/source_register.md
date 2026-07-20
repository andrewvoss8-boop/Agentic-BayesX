# Source register — raw modal-hammer zips (card §4)

Resolution mechanism: direct mediaex URLs (documented in
`shocksat_statfem_runner_20260609/source_manifest.md`; the nescacademy page posts a hidden `url` field →
`mediaex-server.larc.nasa.gov`; HEAD + byte ranges supported — verified again this run for all five zips).
Protocol: one zip at a time; SHA-256 recorded at completion; zip DELETED after its drive's wide cache
passes overlap validation.

| zip | final URL | bytes | SHA-256 | status |
|---|---|---:|---|---|
| Test03_ModalHammer_990y.zip | https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/Test03_ModalHammer_990y.zip | 676070160 | `0abfc7989758b66307d94d5718c93adedccddda7adf919346f6aae8185d34648` | distilled + validated (corr 1.0, dlog 0.0); zip deleted |
| Test06_ModalHammer_900z.zip | https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/Test06_ModalHammer_900z.zip | 923723571 | `85deec14d91b1194ccc3a4965ea41fcae8238e66c04512313b175d56d6294d8f` | distilled + validated (corr 1.0, dlog 0.0); zip deleted |
| Test02_ModalHammer_990z.zip | https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/Test02_ModalHammer_990z.zip | 952326672 | `da32a8447b384eb467669805be888b351e9c121222f273c1a9a503eb4d0ebdfa` | distilled + validated (corr 1.0, dlog 0.0); zip deleted |
| Test04_ModalHammer_990xy.zip (VAULT) | https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/Test04_ModalHammer_990xy.zip | 967685959 | `0a38850eaf589c0f67d4025075f02ba05ff51f064608a1eb987be75a9587f0de` | distilled + validated at build (corr 1.0, dlog 0.0); VAULT_FREEZE.sha256 written; zip deleted |
| Test01_ModalHammer_990x.zip | https://mediaex-server.larc.nasa.gov/shocksat/Test_Data_Impact/Test01_ModalHammer_990x.zip | 1069342844 | `3730fab5d1e5d9d3470bae4e0d4939067fbe16c4c714ec98ad9f1d1c5901092b` | distilled + validated (corr 1.0, dlog 0.0); zip deleted |

**Data phase complete 2026-07-14: all 5 drives wide-distilled (45–3000 Hz kept band), every overlap
bit-identical to the existing caches (per-channel corr 1.0, med |Δlog10H| 0.0, same hits), every drive's
force channel LIVE (peak forces 207–1083 lbf). This closes the raw-vs-cache verification (the resolution
run's Gate W) WITH live force, for all five drives.**
