

reflections on bayesian optimal experiment design and its applicability to aerospace design and analysis workflows:

far be it from me to poke holes in bayesian optimal experiment design, as it is now my "research specialty”.

  It’s OK though to make valid criticisms of it that will ultimately make you stronger.  The real criticism is the BGO and OED cannot do anything when you realize you’re asking the wrong question and is it good enough and creative enough to ask the right question and designed the correct experiment to study that question

but our chat last week (ilias and max transcript) got me wondering how applicable BOED can be outside of 
1 class of problems (ex: alphafold , materials research, drug discovery where there are these conditions (source: deepmind/demis):

What makes for a suitable problem for AI?
1. Massive combinatorial search space
2. Clear objective function (metric) to optimise against
3. Either lots of data and/or an accurate and efficient simulator

But what is the nature of the problem in aerospace design and analysis workflows?

The problem class in aersopace structural dynamics and design is: 
1.  models are large, expensive, take a long time to run (especially cfd, but also FEM/ coupled loads analysis)
2. Even still, these models carry large errors that remain uncharacterized.  
a.  sensor noise
b.  other aleatory randomness
c.  modeling error (big error)
d.  flight to flight varaibility (winds, trajectory, temperature)
e.  build to build variability
f.  design changes that are not in the model. 

(variance in material properties, variance in trajectory… temps… what else am i missing?)

1.  collection of data and updating with data is piecemeal, trial and error, far from standardized and automated.  Each of these error sources is poorly understood, and updating the model with new data, the ways new data is pursued and incorporated are not adequate to what we are now capable of in computational engineering.
4.  compounding all of this  is the coupled loops: where design informs loads, loads inform design, vehicle specs/objectives/gnc affect loads and design requirements.  COnstantly shifting design criteria where everything interacts leads to the only way to make progress is locking in extremely conservative assumptions for all design varaibles and uncertainty factors that all stack up (for the sake of not getting stuck in design analysis paralysis/pencil whipping), resulting in cases where the margins for a part on paper are thin (1.1)  and they break in tests (negative margins), but in the margins are consistently 10x or more.  Analysts should not settle for this as the reality!  we can do better.  


Can the idea of autonomous scientific research with agents and robotic laboratories apply to this class of problem?  At what scope?  just one part, or the whole challenge?




Advanced structural dynamics research lab 2.0-  search is for the best model for a variety of structures and uncertain forcing functions.  Autonomous lab quickly tests doffeeent structures and forcing functions and tests robustness of certain modeling schemes .  Acoustic, aero/buffet/ shock, random vibe, some sweep, fixed base, free free

- [ ] Pitch this in chatt/at mccallie.  20 year incremental buildout plan.  With branch technology KUKA robots, AM, WAAM, small 3d printers, Optimus, etc.  
- [ ] Fixed base like plum brook. 
- [ ] Cheap acoustic testing facility

autonomous scientific research project with branch. 