# Hot Take

Increasing agent autonomy did not improve reliability. Explicit recovery policies at tool boundaries did.

The important part is not that the mock tools are clever. They are intentionally boring. The useful experiment is the boundary around them: validation, classification, retry policy, fallback routing, schema adaptation, and safe aborts.

The most reliable behavior was not "try harder". It was knowing when to retry, when to switch tools, when to adapt, and when to stop.

An agent that keeps calling a broken tool is not resilient. An agent that knows when not to continue is.
