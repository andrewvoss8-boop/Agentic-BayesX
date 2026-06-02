# Aerospace Vibration Data Candidates - 2026-05-29

Purpose: identify real aerospace vibration, modal, flight, FRF, FEM, or transfer-function data that can support Agentic BayesX replication and FBS/STATFEM experiments.

## Ranked shortlist

### 1. F-16 Aircraft Benchmark Based on Ground Vibration Test Data
- URL: https://data.4tu.nl/datasets/b6dc643b-ecc6-437c-8a8a-1681650ec3fe
- DOI: https://doi.org/10.4121/12954911
- Source: 4TU.ResearchData / Eindhoven University of Technology.
- Data type: ground vibration test time series in `.mat` and `.csv`; zip file about 148 MB.
- Structure: full-scale F-16 aircraft with two dummy payloads mounted at wing tips.
- Inputs/responses: one shaker under right wing; shaker reference voltage, force input, acceleration output channels.
- Frequency range noted in associated MDPI paper: 1-60 Hz excitation; first flexible wing bending near 5.2 Hz; important wing torsion/payload interface mode near 7.3 Hz.
- Project fit: best match for primary/secondary FBS. Primary is aircraft wing/airframe; secondary is wingtip dummy payload/pylon interface. It directly supports force-to-acceleration FRFs, nonlinear interface behavior, and model updating.
- Limitation: not a tank dome and not 75/110 Hz; nonlinear interface dominates, which is good later but may be too rich for the first clean linear STATFEM example.
- Recommended first action: download `F16GVT_Files.zip`, parse the lowest-amplitude case, create an H1/BLA FRF, and build a reduced 2DOF/3DOF pylon-interface surrogate.

### 2. Vibrationdata aerospace acceleration time histories
- URL: https://vibrationdata.com/data.htm
- Source: Tom Irvine / Vibrationdata.
- Data type: direct text acceleration time histories, time in seconds and acceleration in G.
- Relevant files listed:
  - `SR19_Fwd_Dome_ignition.txt`: SR-19 forward dome motor ignition static fire.
  - `talos_ignition.txt`: Talos motor ignition, suborbital rocket.
  - `drop.txt`: Pegasus drop transient.
  - `s2_tailoff.txt`: stage 2 tailoff anomaly / ACS pulses.
  - `rv_sep.txt`: re-entry vehicle separation.
- Project fit: best match for the "tank dome" flavor is SR-19 forward dome ignition. Pegasus drop transient is especially useful for payload-interface shock/vibration QOI work.
- Limitation: mostly single-channel time histories, not FRF/modal test matrices. Browser access to the individual `.txt` links was blocked by client policy during this search, but the index and descriptions are visible.
- Recommended first action: use the index links as source manifests, then fetch/download with an approved download route and convert to `time_sec, accel_g` CSV artifacts.

### 3. Pegasus drop transient from flight data
- URL: https://www.vibrationdata.com/tutorials_alt/Pegasus_Drop_Synthesis.pdf
- Source: Tom Irvine / Vibrationdata.
- Data type: paper with measured flight-data context and wavelet synthesis table.
- Structure: Pegasus launch vehicle mounted to L-1011 carrier aircraft; payload interface Z-axis drop transient.
- Key details: drop transient is described as a major payload event; fundamental vehicle/payload body-bending transient is typically 9-10 Hz; sample time history is normalized for proprietary reasons.
- Project fit: very good for a "flight QOI" benchmark and for synthesizing a shaker-test input from a measured payload-interface event.
- Limitation: normalized and reconstructed/synthesized rather than raw proprietary flight data.
- Recommended first action: implement the 40-wavelet table as a deterministic input generator, with explicit labeling as synthesized from published parameters.

### 4. NASA PIMS / ISS acceleration archives
- URLs:
  - https://gipoc.grc.nasa.gov/wp/pims/acceleration-archives/
  - https://gipoc.grc.nasa.gov/wp/acceleration/
- Source: NASA Glenn Principal Investigator Microgravity Services.
- Data type: public ISS acceleration archive, PAD binary format; includes SAMS/MAMS/MMA accelerometer data.
- Frequency range: SAMS vibratory data covers about 0.01-300 Hz per archive description; other NASA summaries mention SAMS to 400 Hz depending system/report.
- Project fit: real in-flight/operational acceleration response data. Useful for output-only modal/operational response, unknown forcing spectrum estimation, and "flight response QOI" examples.
- Limitation: not a controlled modal/vibe test. Need PAD binary reader and careful sensor/time-window selection. Inputs are not measured forcing functions.
- Recommended first action: implement a small PAD file reader and select one SAMS sensor/time window with known disturbance source from PIMS handbook/roadmap.

### 5. BAE T1A Hawk full-structure modal test
- URL: https://orda.shef.ac.uk/articles/dataset/BAE_T1A_Hawk_Full_Structure_Modal_Test/24948549
- DOI: https://doi.org/10.15131/shef.data.24948549
- Source: University of Sheffield ORDA/Figshare.
- Data type: HDF5 full-structure modal test data, force/acceleration/strain; total download all about 223 GB.
- Structure: decommissioned full BAE Systems Hawk T1A aircraft.
- Project fit: very strong full-aircraft modal/system-identification benchmark; useful when we graduate beyond 2DOF.
- Limitation: huge; likely too large for the first import. Needs metadata-first subset selection using provided package/docs.
- Recommended first action: download only metadata and usage docs, then use the Python package to pull a small subset.

### 6. Processed Hawk modal analysis support data on Zenodo
- URL: https://zenodo.org/records/14173403
- DOI: https://doi.org/10.5281/zenodo.14173403
- Source: Zenodo / Universidad Carlos III de Madrid.
- Data type: small processed files plus large mode-shape figures. Includes `beam_data.mat` about 3.3 MB and `HAWK_modalParam.xlsx` about 73.7 kB.
- Project fit: good low-friction way to start with real full-aircraft modal data without the 223 GB ORDA payload.
- Limitation: processed/support dataset, not necessarily raw FRFs/time histories for the whole aircraft.
- Recommended first action: download `beam_data.mat` and `HAWK_modalParam.xlsx`, inspect variables, and decide whether they can seed an MDOF modal-reduction example.

### 7. Flexible Diana 2 scaled glider UAV GVT dataset
- URL: https://research.tudelft.nl/en/datasets/flexible-diana-2-scaled-glider-uav-ground-vibration-test-results/
- DOI: https://doi.org/10.4121/2C7EF9A5-D749-4B82-A63E-BDE7D15D213E
- Source: TU Delft / 4TU.ResearchData.
- Data type: ground vibration test FRFs and modal estimates in Siemens `.lms` and standard `.unv`; includes accelerometer, gyro, strain-gauge, and IMU channels.
- Structure: 1:3 scaled Diana 2 glider UAV, free-free suspension with modal hammer excitation.
- Project fit: excellent for testing UNV import, FRF parsing, modal reduction, and strain/acceleration multimodal STATFEM.
- Limitation: small UAV/glider, not a tank skin or heavy secondary appendage.
- Recommended first action: download `.unv` files and build an importer/plotter before attempting full inference.

### 8. NASA Common Research Model FEM/modal files
- URL: https://commonresearchmodel.larc.nasa.gov/fem-file/
- Source: NASA Common Research Model.
- Data type: FEM files and modal analysis for first 30 modes for some CRM configurations.
- Structure: aircraft wind-tunnel model configurations, including nacelle/pylon/tail options and wingbox FEMs.
- Project fit: best public NASA source found for aerospace FEM/modal starting geometry. Useful for the MDOF/FEM side, not for measured vibration time histories.
- Limitation: primarily analytical/computational FEM and aerodynamic validation context; not direct measured FRF data for our STATFEM observation channels.
- Recommended first action: download the simplest wing/body or wingbox FEM and create an automated modal extraction/FRF synthesis harness.

### 9. Vibrationdata FEM/NASTRAN examples
- URL: https://www.vibrationdata.com/StructuralFE.htm
- Source: Vibrationdata.
- Data type: Matlab scripts, Nastran input files, transfer-function-from-modes tutorial, plate/shell/beam examples, Craig-Bampton scripts.
- Particularly relevant items:
  - transfer functions from modes tutorial/scripts.
  - `rplate.nas`, `conical_shell3.nas`, `sdof_m6_base.nas`.
  - conical shell modal test and finite element analysis.
- Project fit: very useful for building our FEM-to-transfer-function harness and verifying against known structural dynamics examples.
- Limitation: mostly instructional examples rather than real aerospace flight/test data. Conical shell may be a useful stand-in for tank-like geometry.
- Recommended first action: import one `.nas` file and regenerate modal frequencies/FRFs in Python.

### 10. Modified US Army U-8F ground vibration test
- URL: https://ntrs.nasa.gov/citations/19860021251
- Source: NASA NTRS.
- Data type: technical memorandum PDF with frequency-response plots, modal frequencies, damping, and mode shapes.
- Structure: modified U.S. Army U-8F airplane; modifications include engines, propellers, and engine-mounted truss assemblies.
- Project fit: useful for literature comparison and possible plot digitization of FRFs/modes.
- Limitation: appears to be plots/tables in a PDF, not raw downloadable data.
- Recommended first action: keep as a validation/reference report, not as first ingestion target.

## Best next move for Agentic BayesX
1. Start with the F-16 GVT benchmark as the first real primary/secondary dataset.
2. In parallel, use Vibrationdata SR-19/Pegasus time histories as flight/static-fire response QOI examples.
3. Use Vibrationdata FEM scripts or NASA CRM FEM files to harden the MDOF transfer-function harness.
4. Defer the full Hawk dataset until we have a metadata-first data ingestion pattern; use the small Zenodo Hawk support files first.

## Open cautions
- Many aerospace flight/modal datasets are either proprietary, huge, PDF-only, or processed rather than raw.
- The best-fitting public dataset by physics is F-16 GVT, but its frequencies are much lower than the toy 75/110 Hz tray/dome example.
- Vibrationdata time histories are ideal for signal processing and QOI examples, but they are mostly not collocated input-output FRFs.
- The ISS/PIMS archive is real operational data, but without measured forcing it belongs to output-only/unknown-input workflows.
