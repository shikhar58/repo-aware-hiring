# Example: a posting for an engineer on Ollama's inference engine

> **Unofficial example.** Drafted by repo-aware-hiring from the public
> [Ollama](https://github.com/ollama/ollama) repository (commit d63b702) to show what the tool produces on a large,
> real codebase: about 380,000 lines of Go plus native GPU code. **It is not a real job opening**, and it is not
> affiliated with or endorsed by Ollama. Only the posting is shown: the internal codebase map, which lists the
> codebase's risks, is never published.

How it was made: the hiring manager picked the area (the inference engine), the title, a one-line focus ("adding
support for new model architectures") and what success looks like in a year ("new open models run well in Ollama soon
after release"). Pay, location and employment type were skipped, so they are `[insert: …]` placeholders. The leak
checker found nothing to block, and the stack is hinted through the work and the requirements, never listed.

---

## Senior Software Engineer, Inference Engine
[insert: location and working model] · [insert: employment type] · [insert: salary range]


### About the role
Ollama lets anyone run open language models on their own machine. When a new open model is released, people want to
run it right away, and run it well. You'll own how new model architectures come to our inference engine, so that new
open models run well in Ollama soon after their release, on Apple Silicon and NVIDIA GPUs alike.

### What you'll work on
- Implement new model architectures in our Go inference engine, from attention variants and mixture-of-experts
  routing to hybrid models with recurrent, state-space layers, and prove each one matches its reference
  implementation.
- Take each model the whole way: tokenizer, prompt format, tool-call and reasoning output, quantised weights and the
  right cache strategy, so it doesn't just run but behaves the way its authors intended.
- Bring vision and audio models into the engine, and draft models that make generation faster.
- Keep models consistent across our two engines, including the one built on llama.cpp.
- Build the tests and tooling that tell us quickly and reliably that a new model is correct, without a GPU farm for
  every change.

### Must-haves
- You've implemented transformer models from a paper or a reference implementation (for example in PyTorch, JAX, MLX
  or llama.cpp) and can show how you verified the output matched.
- You understand modern architectures in depth: attention and positional-encoding variants such as RoPE scaling,
  mixture-of-experts, and recurrent or state-space layers.
- You write production systems code in Go, C, C++ or Rust, and you're happy to work mostly in Go.
- You can debug numerical problems: tracing a quality regression to a layer, a tokenizer or a quantisation choice.

### Nice-to-haves
- GPU programming on Apple Metal or NVIDIA CUDA, or experience with MLX.
- Quantisation formats and their quality trade-offs.
- Multimodal models: vision or audio encoders.
- Contributions to open-source model runtimes or inference engines.

### How we hire
[insert: interview steps and how long they take]

[insert: how AI-assisted screening is used and how to ask for adjustments or a human-only review; required when AI helps screen (Anthropic's Usage Policy, and the law in some places)]

### What we offer
[insert: benefits]

[insert: equal opportunity statement]
