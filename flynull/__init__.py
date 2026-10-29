"""flynull: null models and routing measures for the FlyWire connectome.

Modules
  data           load FlyWire v783 (neurons, synapse matrix, signs)
  nulls          randomised-brain generators, incl. inside-only (boundary-preserving)
  rate_operator  linear rate model: normalise, calibrate gain, routing profiles
  measures       gross dynamical signatures
  path_stats     hop counts and shortcut statistics
  routing        sensory channels, boundary masks, surrogates, Exp01 evaluation
  stmap          Stuerner et al. 2025 DN map and simulation-vs-map scoring
  flow           information-flow model (navis TraversalModel, exact fast form)
"""
__version__ = "0.1.0"
