Throughout this book, we are iteratively going to build up our `TinyAgent` using each chapter as a theoretical background for understanding why these particular components are needed and what they can do. This time around, we decided to explore this hands-on approach through **pure Python**! 

We assume that you have an LLM running on an OpenAI-compatible endpoint that you can query. Other than that, everything will be build using nothing more than Python. We also make sure to add examples that do make use of dependencies (like MCP) but these are completely optional and are considered bonus content!


# Setting up your environment

There are various methods for setting up your environment (uncomment the one that works best for you):

### pip

If you already have a Python environment (with Python 3.9 or newer), you can install the dependencies with:

```bash
# If you follow the notebook tutorials
pip install illustrated-agents[jupyter]

# The TinyAgent (in the cli) can be installed with
pip install illustrated-agents
```

You can also install the package directly using:

```bash
pip install git+https://github.com/HandsOnLLM/Illustrated-Agents.git
```

### uv

Our preferred method for creating and managing environments is [`uv`](https://github.com/astral-sh/uv) which can be [installed like so](https://docs.astral.sh/uv/getting-started/installation/). Usage is straightforward:

```bash
# If you follow the notebook tutorials
uv add illustrated-agents --extra jupyter

# The TinyAgent (in the cli) can be installed with
uv add illustrated-agents
```

or if you cloned the repo:

```bash
# If you follow the notebook tutorials
uv sync --extra jupyter

# The TinyAgent (in the cli) can be installed with
uv sync
```

# Chapters

Each chapter can be run with the following options:

* `Google Colab` -- This is a cloud environment which simplifies setup significantly
* `Jupyter Lab` -- A local coding environment using notebooks

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
