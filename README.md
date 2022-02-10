# coding-art

## Table of Contents

- [Introduction](#introduction)

- [Installation](#installation)

- [Data sources](#data-sources)

- [Instructions](#instructions)

- [Architecture](#architecture)

- [Next steps](#next-steps)

---

## Introduction
### Description
This is a repository that will contain all my personal projects related to astronomy.

### Objectives
- Learn computer vision in general
- Explore computer vision techniques to create art

### When?
It is an ongoing project, started on `Jan 19, 2021`.

### Visuals
![Live demo](core/assets/images/live_demo.png)


## Installation
To run the program and see a demo of the code, you need:
- To install the libraries below
- To download the public datasets (see [Data sources](#data-sources) for information).

### Install the libraries
| Library          | Used to                                        |
| ---------------- | :----------------------------------------------|
| Numpy            | To handle Numpy arrays                         |
| Pandas           | To store and access info in a DataFrame        |
| Matplotlib       | To plot the data                               |
| opencv           | To read, process & render images               |
| jupyter          | To experiment quickly & interactively          |


Follow these instructions to install the required libraries: on terminal
1. Open your terminal;
2. cd to the directory where the `requirements.txt` file is located;
3. Create and activate your virtual environment.
4. Run the command: 
```pip3 install -r requirements.txt```

### Additional info
Note that I develop the source code on macOS Big Sur; chip: Apple M1

## Data Sources
To create my digital art, I use the datasets from
- my own photos & videos collection
- public datasets that I have manually downloaded or scraped

## Instructions
### How to run the program
- Run `main.py` to start the program.
- Run `main_demo.ipynb` to see a live demo of the program.
Or
On your terminal:
1. Open your terminal;
2. cd to the directory where the `main.py` or `main_demo.ipynb` are
3. Activate your virtual environment.
4. Run the command:
- `python3 main.py` (to run the program) with the following arguments:

```
Arguments
...
```

- `jupyter notebook main_demo.ipynb` (to open the jupyter notebook) 

### Usage example
![Demo usage](core/assets/repo_visuals/demo_usage.png)



## Architecture
The project is structured as follows:

```
coding-art
│   README.md               :explains the project
│   main.py                 :script to run in order to start the program
│   main_demo.ipynb         :jupyter notebook to see a demo of the program
│   requirements.txt        :packages to install to run the program
│   .gitignore              :files to ignore when pushing to the GitHub repository
│
└───core                    :directory contains all the core scripts of the program
│   │   __init__.py
│   │
│   └───assets              :contains the datasets, images and AI models
│       ├───data
│       ├───images
│       ├───models
│       └───repo_visuals
│   ├───models_3d           :contains the 3D models creation project
│   ├───mosaic              :contains the mosaic creation project
│   ├───tutorials           :contains the tutorials I follow
│   └───utils               :contains the utilities
```

### Roadmap
- [x] Create repo
- [ ] Clean, split code, make it more modular, easy to reuse
- [ ] Implement binary search tree to see if it can speed up mosaic creation
- [ ] In mosaic creation: process images to better match grid cell of photo to recreate
- [ ] Scrape images
- [ ] Prepare my own images
- [ ] Create mosaic gifs
- [ ] Create mosaic videos
- [ ] Create mosaic 3D models?

Continuously:
- [ ] Learn and apply new computer vision techniques

### Author(s) and acknowledgment
This project is carried out by **Van Frausum Derrick** 
from Theano 2.27 promotion at BeCode.

## Next steps
- Progress in roadmap
