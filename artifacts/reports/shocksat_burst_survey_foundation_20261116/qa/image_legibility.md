# Image legibility review (manual, by viewing the rendered PNGs)

fig1_pilot_frf_wall.png: first render had overlapping titles, a stray minor tick label and colliding tick labels in panel c; fixed. Final render: no clipped or overlapping text; curve labels direct; log axes stated; source and exploratory status in the footer. PASS.
fig2_burst_resolution.png: counts printed above each column; threshold labelled; source footer states no simulation. PASS.
tufte_lint: one INFO flag (dB). dB is used because the quantity compared is a ratio of FRF magnitudes and the project's reference metric (Card H) is in dB.
