# Introduction to Artificial Intelligence

Coursework repository for **Introduction to Artificial Intelligence**, part of my Master's in Artificial Intelligence.

This repository contains exercises, implementations, and other practical work developed throughout the course.

## Contents

| Folder | Topic |
|---|---|
| [`01_basic_concepts_of_ai`](./01_basic_concepts_of_ai/) | AI applications I use or have used |
| [`02_agents`](./02_agents/) | Modifying the Wumpus world, and PEAS descriptions of intelligent agents |
| [`03_uninformed_search`](./03_uninformed_search/) | Uninformed search |
| [`04_informed_search`](./04_informed_search/) | Informed search |
| [`05_multilayer_perceptron`](./05_multilayer_perceptron/) | Adding layers to a multilayer perceptron |
| [`06_computer_vision`](./06_computer_vision/) | Changing the prediction image in YOLO |
| [`07_clustering_k_means`](./07_clustering_k_means/) | Separating blobs and choosing k again |
| [`final-project`](./final-project/) | **Final project:** a RAG system over Autmix agitator brochures |

## Final project

A retrieval-augmented generation system that answers questions about industrial
agitators using only their public brochures, in Spanish, citing its sources and
abstaining when the brochures don't contain the answer. Built with Streamlit,
FastAPI, ChromaDB and Google AI, it also compares models, selects them by
requirements, shows the brochure page behind each citation and maps the index.

See the [project README](./final-project/README.md) to run it and see the evidences, and the
[report](./final-project/REPORT.md) (in Spanish) for the design decisions.
