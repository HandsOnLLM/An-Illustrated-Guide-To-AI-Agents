Throughout this book, we are iteratively going to build up our `TinyAgent` using each chapter as a theoretical background for understanding why these particular components are needed and what they can do. This time around, we decided that we wanted to separate the code from the theory a bit more so that we can have more flexibility regarding the code and potential updates that we might do in the upcoming months/years. 

That said, the `TinyAgent` that we will be building throughout this book requires a very minimal set of dependencies. All we want to do is call an LLM and build up our Agent using that. Therefore, we decided on two main options for running your models, `LiteLLM` for all your cloud models and `Ollama` for your local offering. Together, they allow you to run any proprietary model and local model. With `LiteLLM`, you can also run more local models using frameworks like [`llama.cpp`](https://docs.litellm.ai/docs/providers/openai_compatible), [`LMStudio`](https://docs.litellm.ai/docs/providers/lm_studio), and [`vLLM`](https://docs.litellm.ai/docs/providers/vllm).

> [!NOTE]
> Although `LiteLLM` can also run local models, we decided to use `Ollama` as the main solution throughout the codebase since it allows you to easily turn on and off the reasoning of models. We need this to explain how you can create agentic behavior yourself even when a model was not trained to reason.

# Setting up your environment

There are various methods for setting up your environment (uncomment the one that works best for you):

### pip

If you already have a Python environment (with Python 3.9 or newer), you can install the dependencies with:

```bash
pip install illustrated-agents

# If you plan on using Jupyter notebooks
pip install illustrated-agents[jupyter]
```

You can also install the package directly using:

```bash
pip install git+https://github.com/HandsOnLLM/Illustrated-Agents.git
```

### uv

Our preferred method for creating and managing environments is [`uv`](https://github.com/astral-sh/uv) which can be [installed like so](https://docs.astral.sh/uv/getting-started/installation/). Usage is straightforward:

```bash
uv add illustrated-agents

# If you plan on using Jupyter notebooks
uv add illustrated-agents --extra jupyter
```

or if you cloned the repo:

```bash
uv sync

# If you plan on using Jupyter notebooks
uv sync --extra jupyter
```

# Chapters

Each chapter can be run with the following options:

* `Google Colab` -- This is a cloud environment which simplifies setup significantly
* `Jupyter Lab` -- A local coding environment using notebooks
* `Terminal` -- For running a full example

### Google Colab

This is a cloud environment that uses notebooks (much like Jupyter Lab) to run the examples for each chapter. All `.ipynb` in the book can run both locally and through Google Colab. Simply click the [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](...) button to open and run the notebook.

### **Jupyter Lab**

The notebooks are the primary source of tutorials in each chapter and will guide you through the basics of Agents. Jupyter Lab is a common application to use, which can be used as follows:

```bash
# Using `uv`
uv run jupyter lab

# Using python directly
jupyter lab
```

### **Terminal**

To run an example in a given chapter, you only need to run:

```bash
# For `uv`
uv run chapter03/example.py

# Directly from python
python chapter03/example.py
```

**NOTE**: In the `.py` examples, we assume you have `Ollama` running and downloaded Gemma 4 with `ollama pull gemma4:e4b`!
